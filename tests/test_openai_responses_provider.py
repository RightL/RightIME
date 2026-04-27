import json
import unittest
from io import BytesIO
from urllib.error import HTTPError

from rightime.provider import ProviderError
from rightime.providers.openai_responses import OpenAIResponsesProvider
from rightime.types import ProviderPrompt


class FakeHttpResponse:
    status = 200

    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class CapturingOpener:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.requests = []
        self.timeouts = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        self.timeouts.append(timeout)
        return FakeHttpResponse(self.payload)


class OpenAIResponsesProviderTest(unittest.TestCase):
    def test_sends_responses_request_and_parses_output_text(self) -> None:
        opener = CapturingOpener(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "我在写 rightIME。"}
                        ],
                    }
                ],
                "usage": {"input_tokens": 12, "output_tokens": 9},
            }
        )
        provider = OpenAIResponsesProvider(
            api_key="secret",
            model="test-model",
            opener=opener,
            timeout_s=7,
        )

        output = provider.convert(
            ProviderPrompt(
                instructions="Return only text.",
                input_text="Current draft:\nwo zai xie rightIME",
            )
        )

        self.assertEqual(output.text, "我在写 rightIME。")
        self.assertEqual(output.token_count, 21)
        sent = opener.requests[0]
        body = json.loads(sent.data.decode("utf-8"))
        self.assertEqual(sent.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(sent.get_method(), "POST")
        self.assertEqual(sent.headers["Authorization"], "Bearer secret")
        self.assertEqual(body["model"], "test-model")
        self.assertEqual(body["instructions"], "Return only text.")
        self.assertEqual(body["input"], "Current draft:\nwo zai xie rightIME")
        self.assertEqual(body["text"]["format"]["type"], "text")
        self.assertEqual(opener.timeouts, [7])

    def test_rejects_response_without_output_text(self) -> None:
        provider = OpenAIResponsesProvider(
            api_key="secret",
            model="test-model",
            opener=CapturingOpener({"output": []}),
        )

        with self.assertRaisesRegex(ProviderError, "missing output_text"):
            provider.convert(ProviderPrompt(instructions="i", input_text="x"))

    def test_http_error_is_visible(self) -> None:
        def raising_opener(request, timeout):
            raise HTTPError(
                url=request.full_url,
                code=401,
                msg="Unauthorized",
                hdrs={},
                fp=BytesIO(b'{"error":{"message":"bad key"}}'),
            )

        provider = OpenAIResponsesProvider(
            api_key="secret",
            model="test-model",
            opener=raising_opener,
        )

        with self.assertRaisesRegex(ProviderError, "401"):
            provider.convert(ProviderPrompt(instructions="i", input_text="x"))


if __name__ == "__main__":
    unittest.main()
