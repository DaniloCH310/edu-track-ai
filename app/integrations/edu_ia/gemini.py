import httpx

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiError(RuntimeError):
    def __init__(self, code: str, retryable: bool = False) -> None:
        self.code = code
        self.retryable = retryable
        super().__init__(f"EDU IA request failed ({code}).")


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._http = http_client or httpx.Client(timeout=httpx.Timeout(30.0))

    def generate_reply(self, instruction: str, messages: list[dict[str, str]]) -> str:
        contents = [
            {
                "role": "model" if message["role"] == "assistant" else "user",
                "parts": [{"text": message["content"]}],
            }
            for message in messages
        ]
        payload = {
            "system_instruction": {"parts": [{"text": instruction}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1500},
        }
        try:
            response = self._http.post(
                f"{GEMINI_API_BASE}/{self.model}:generateContent",
                params={"key": self.api_key},
                json=payload,
            )
        except httpx.HTTPError as exception:
            raise GeminiError("edu_ai_temporarily_unavailable", retryable=True) from exception
        if response.status_code == 401 or response.status_code == 403:
            raise GeminiError("edu_ai_unavailable")
        if response.status_code == 429 or response.status_code >= 500:
            raise GeminiError("edu_ai_temporarily_unavailable", retryable=True)
        if response.status_code >= 400:
            raise GeminiError("edu_ai_request_failed")
        try:
            payload = response.json()
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
        except (IndexError, KeyError, TypeError, ValueError) as exception:
            raise GeminiError("edu_ai_invalid_response") from exception
        if not isinstance(text, str) or not text.strip():
            raise GeminiError("edu_ai_invalid_response")
        return text.strip()
