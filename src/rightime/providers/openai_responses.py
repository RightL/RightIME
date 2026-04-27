import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rightime.provider import ProviderError, ProviderOutput
from rightime.types import ProviderPrompt


class OpenAIResponsesProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        endpoint: str = "https://api.openai.com/v1/responses",
        timeout_s: int = 20,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout_s = timeout_s
        self._opener = opener

    def convert(self, prompt: ProviderPrompt) -> ProviderOutput:
        payload = {
            "model": self.model,
            "instructions": prompt.instructions,
            "input": prompt.input_text,
            "text": {"format": {"type": "text"}},
        }
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            self._endpoint,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with self._opener(request, timeout=self._timeout_s) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(
                "request_rejected",
                f"OpenAI request failed with HTTP {exc.code}: {body}",
            ) from exc
        except URLError as exc:
            raise ProviderError(
                "provider_unavailable",
                f"OpenAI request failed: {exc.reason}",
            ) from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError("invalid_provider_response", "OpenAI response was not JSON") from exc

        text = _extract_output_text(parsed)
        token_count = _extract_token_count(parsed)
        return ProviderOutput(text=text, token_count=token_count)


def _extract_output_text(parsed: dict[str, Any]) -> str:
    for output_item in parsed.get("output", []):
        for content_item in output_item.get("content", []):
            if content_item.get("type") == "output_text":
                text = content_item.get("text")
                if isinstance(text, str):
                    return text
    raise ProviderError("invalid_provider_response", "OpenAI response missing output_text")


def _extract_token_count(parsed: dict[str, Any]) -> int | None:
    usage = parsed.get("usage")
    if not isinstance(usage, dict):
        return None

    total = usage.get("total_tokens")
    if isinstance(total, int):
        return total

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        return input_tokens + output_tokens

    return None
