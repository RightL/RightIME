import os
import unittest
from io import StringIO
from unittest.mock import patch

from rightime import ConversionMetadata, ConversionResult
from rightime.cli import main


class FakeEngine:
    requests = []

    def __init__(self, provider) -> None:
        self.provider = provider

    def convert(self, request):
        self.requests.append(request)
        return ConversionResult(
            text="我在写 rightIME。",
            metadata=ConversionMetadata(model="fake-model", latency_ms=33, token_count=10),
        )


class FakeProvider:
    def __init__(self, api_key: str, model: str, endpoint: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        FakeEngine.requests = []

    def test_cli_prints_conversion_text(self) -> None:
        env = {
            "RIGHTIME_OPENAI_API_KEY": "secret",
            "RIGHTIME_OPENAI_MODEL": "test-model",
        }
        stdout = StringIO()

        with patch.dict(os.environ, env, clear=True), patch(
            "rightime.cli.OpenAIResponsesProvider", FakeProvider
        ), patch("rightime.cli.ConversionEngine", FakeEngine), patch("sys.stdout", stdout):
            code = main(["wo zai xie rightIME", "--context-line", "我们在讨论输入法。"])

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "我在写 rightIME。\n")
        self.assertEqual(FakeEngine.requests[0].raw_text, "wo zai xie rightIME")
        self.assertEqual(FakeEngine.requests[0].session_context, ("我们在讨论输入法。",))

    def test_cli_requires_api_key_and_model(self) -> None:
        stderr = StringIO()

        with patch.dict(os.environ, {}, clear=True), patch("sys.stderr", stderr):
            code = main(["wo yao ceshi"])

        self.assertEqual(code, 2)
        self.assertIn("RIGHTIME_OPENAI_API_KEY", stderr.getvalue())
        self.assertIn("RIGHTIME_OPENAI_MODEL", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
