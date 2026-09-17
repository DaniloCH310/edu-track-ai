import json

import httpx
import pytest

from app.integrations.edu_ia.gemini import GeminiClient, GeminiError


def make_client(handler) -> GeminiClient:
    return GeminiClient(
        api_key="secret-must-not-appear",
        model="gemini-2.5-flash",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_gemini_client_builds_tutor_request_and_returns_text():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "Comece pela lista."}]}}]},
        )

    reply = make_client(handler).generate_reply(
        "Você é EDU IA.",
        [{"role": "user", "content": "Como começo?"}],
    )

    assert reply == "Comece pela lista."
    assert requests[0].url.path.endswith(":generateContent")
    assert requests[0].url.params["key"] == "secret-must-not-appear"
    payload = json.loads(requests[0].content)
    assert payload["system_instruction"]["parts"][0]["text"] == "Você é EDU IA."
    assert payload["contents"] == [{"role": "user", "parts": [{"text": "Como começo?"}]}]


@pytest.mark.parametrize("status", [429, 500])
def test_gemini_client_sanitizes_transient_failures(status: int):
    with pytest.raises(GeminiError) as captured:
        make_client(lambda _request: httpx.Response(status)).generate_reply("Tutor", [])

    assert captured.value.code == "edu_ai_temporarily_unavailable"
    assert "secret-must-not-appear" not in str(captured.value)
