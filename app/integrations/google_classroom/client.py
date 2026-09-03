from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode

import httpx

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CLASSROOM_API = "https://classroom.googleapis.com/v1"

COURSES_SCOPE = "https://www.googleapis.com/auth/classroom.courses.readonly"
COURSEWORK_SCOPE = "https://www.googleapis.com/auth/classroom.coursework.me.readonly"
REQUIRED_SCOPES = frozenset({COURSES_SCOPE, COURSEWORK_SCOPE})


@dataclass(frozen=True)
class GoogleTokens:
    access_token: str
    refresh_token: str | None
    scopes: frozenset[str]


class GoogleClassroomError(RuntimeError):
    def __init__(self, code: str, retryable: bool = False) -> None:
        self.code = code
        self.retryable = retryable
        super().__init__(f"Google Classroom request failed ({code}).")


class GoogleClassroomClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._http = http_client or httpx.Client(
            timeout=httpx.Timeout(15.0), follow_redirects=False
        )

    def authorization_url(self, state: str, challenge: str) -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": f"{COURSES_SCOPE} {COURSEWORK_SCOPE}",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "access_type": "offline",
                "prompt": "consent",
                "include_granted_scopes": "true",
            }
        )
        return f"{GOOGLE_AUTH_URL}?{query}"

    def exchange_code(self, code: str, verifier: str) -> GoogleTokens:
        payload = self._post_token(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
            }
        )
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise GoogleClassroomError("google_invalid_response")
        refresh_token = payload.get("refresh_token")
        scopes = payload.get("scope", "")
        return GoogleTokens(
            access_token=access_token,
            refresh_token=refresh_token if isinstance(refresh_token, str) else None,
            scopes=frozenset(str(scopes).split()),
        )

    def refresh_access_token(self, refresh_token: str) -> str:
        payload = self._post_token(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        )
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise GoogleClassroomError("google_invalid_response")
        return access_token

    def list_active_courses(self, access_token: str) -> list[dict[str, Any]]:
        return self._paginated_get(
            f"{GOOGLE_CLASSROOM_API}/courses",
            access_token,
            "courses",
            {"courseStates": "ACTIVE", "pageSize": 100},
        )

    def list_published_coursework(
        self, access_token: str, course_id: str
    ) -> list[dict[str, Any]]:
        encoded_course = quote(course_id, safe="")
        return self._paginated_get(
            f"{GOOGLE_CLASSROOM_API}/courses/{encoded_course}/courseWork",
            access_token,
            "courseWork",
            {"courseWorkStates": "PUBLISHED", "pageSize": 100},
        )

    def list_my_submissions(
        self, access_token: str, course_id: str, coursework_id: str
    ) -> list[dict[str, Any]]:
        encoded_course = quote(course_id, safe="")
        encoded_work = quote(coursework_id, safe="")
        return self._paginated_get(
            (
                f"{GOOGLE_CLASSROOM_API}/courses/{encoded_course}/courseWork/"
                f"{encoded_work}/studentSubmissions"
            ),
            access_token,
            "studentSubmissions",
            {"userId": "me", "pageSize": 100},
        )

    def _post_token(self, data: dict[str, Any]) -> dict[str, Any]:
        response = self._request("POST", GOOGLE_TOKEN_URL, data=data)
        return self._safe_json(response)

    def _paginated_get(
        self,
        url: str,
        access_token: str,
        response_key: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            page_params = dict(params)
            if page_token:
                page_params["pageToken"] = page_token
            response = self._request(
                "GET",
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                params=page_params,
            )
            payload = self._safe_json(response)
            page_items = payload.get(response_key, [])
            if not isinstance(page_items, list):
                raise GoogleClassroomError("google_invalid_response")
            items.extend(item for item in page_items if isinstance(item, dict))
            next_token = payload.get("nextPageToken")
            if not isinstance(next_token, str) or not next_token:
                return items
            page_token = next_token

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._http.request(method, url, **kwargs)
        except httpx.HTTPError as exception:
            raise GoogleClassroomError(
                "google_temporarily_unavailable", retryable=True
            ) from exception

        if response.status_code < 400:
            return response
        if response.status_code == 401:
            raise GoogleClassroomError("google_unauthorized")
        if response.status_code == 403:
            raise GoogleClassroomError("google_access_blocked")
        if response.status_code == 429 or response.status_code >= 500:
            raise GoogleClassroomError("google_temporarily_unavailable", retryable=True)
        raise GoogleClassroomError("google_request_failed")

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exception:
            raise GoogleClassroomError("google_invalid_response") from exception
        if not isinstance(payload, dict):
            raise GoogleClassroomError("google_invalid_response")
        return payload
