from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app.integrations.google_classroom.client import (
    COURSES_SCOPE,
    COURSEWORK_SCOPE,
    GoogleClassroomClient,
    GoogleClassroomError,
)


def make_client(handler) -> GoogleClassroomClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return GoogleClassroomClient(
        client_id="fake-client-id",
        client_secret="fake-client-secret",
        redirect_uri="http://127.0.0.1:8000/callback",
        http_client=http_client,
    )


def test_authorization_url_uses_exact_readonly_scopes():
    client = make_client(lambda request: httpx.Response(500))

    query = parse_qs(urlparse(client.authorization_url("state-1", "challenge-1")).query)

    assert query["scope"] == [f"{COURSES_SCOPE} {COURSEWORK_SCOPE}"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]


def test_exchange_code_and_refresh_token_use_google_token_endpoint():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if b"authorization_code" in request.content:
            return httpx.Response(
                200,
                json={
                    "access_token": "fake-access",
                    "refresh_token": "fake-refresh",
                    "scope": f"{COURSES_SCOPE} {COURSEWORK_SCOPE}",
                },
            )
        return httpx.Response(200, json={"access_token": "refreshed-access"})

    client = make_client(handler)

    tokens = client.exchange_code("fake-code", "fake-verifier")
    refreshed = client.refresh_access_token("fake-refresh")

    assert tokens.access_token == "fake-access"
    assert tokens.refresh_token == "fake-refresh"
    assert tokens.scopes == frozenset({COURSES_SCOPE, COURSEWORK_SCOPE})
    assert refreshed == "refreshed-access"
    assert all(request.url.path == "/token" for request in requests)
    assert b"fake-client-secret" in requests[0].content


def test_courses_are_paginated_until_next_page_token():
    page_tokens: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page_tokens.append(request.url.params.get("pageToken"))
        if len(page_tokens) == 1:
            return httpx.Response(
                200,
                json={"courses": [{"id": "course-1"}], "nextPageToken": "next-1"},
            )
        return httpx.Response(200, json={"courses": [{"id": "course-2"}]})

    courses = make_client(handler).list_active_courses("fake-access")

    assert [course["id"] for course in courses] == ["course-1", "course-2"]
    assert page_tokens == [None, "next-1"]


def test_coursework_and_submissions_encode_path_ids_and_apply_filters():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        key = "studentSubmissions" if "studentSubmissions" in request.url.path else "courseWork"
        return httpx.Response(200, json={key: [{"id": "item-1"}]})

    client = make_client(handler)

    assert client.list_published_coursework("fake-access", "course/1") == [
        {"id": "item-1"}
    ]
    assert client.list_my_submissions("fake-access", "course/1", "work/1") == [
        {"id": "item-1"}
    ]

    assert "/courses/course%2F1/courseWork" in str(requests[0].url)
    assert requests[0].url.params["courseWorkStates"] == "PUBLISHED"
    assert "/courseWork/work%2F1/studentSubmissions" in str(requests[1].url)
    assert requests[1].url.params["userId"] == "me"


@pytest.mark.parametrize(
    ("status", "code", "retryable"),
    [
        (401, "google_unauthorized", False),
        (403, "google_access_blocked", False),
        (429, "google_temporarily_unavailable", True),
        (503, "google_temporarily_unavailable", True),
    ],
)
def test_google_error_is_sanitized(status: int, code: str, retryable: bool):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": "fake-access must never leak"})

    with pytest.raises(GoogleClassroomError) as captured:
        make_client(handler).list_active_courses("fake-access")

    assert captured.value.code == code
    assert captured.value.retryable is retryable
    assert "fake-access" not in str(captured.value)


def test_network_failure_is_sanitized_and_retryable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("remote included fake-access", request=request)

    with pytest.raises(GoogleClassroomError) as captured:
        make_client(handler).list_active_courses("fake-access")

    assert captured.value.code == "google_temporarily_unavailable"
    assert captured.value.retryable is True
    assert "fake-access" not in str(captured.value)
