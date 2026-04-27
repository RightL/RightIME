import unittest
from io import StringIO
from unittest.mock import patch

from rightime import ConversionMetadata, ConversionResult
from rightime.cli import main


class FakeEngine:
    requests = []

    def convert(self, request):
        self.requests.append(request)
        return ConversionResult(
            text="我在写 rightIME。",
            metadata=ConversionMetadata(model="fake-model", latency_ms=33, token_count=10),
        )


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        FakeEngine.requests = []

    def test_cli_prints_conversion_text(self) -> None:
        stdout = StringIO()

        with patch("rightime.cli.load_runtime_config", return_value="config"), patch(
            "rightime.cli.build_engine", return_value=FakeEngine()
        ), patch("sys.stdout", stdout):
            code = main(["wo zai xie rightIME", "--context-line", "我们在讨论输入法。"])

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "我在写 rightIME。\n")
        self.assertEqual(FakeEngine.requests[0].raw_text, "wo zai xie rightIME")
        self.assertEqual(FakeEngine.requests[0].session_context, ("我们在讨论输入法。",))

    def test_cli_reports_runtime_configuration_error(self) -> None:
        stderr = StringIO()

        with patch("rightime.cli.load_runtime_config", side_effect=RuntimeError("missing config")), patch(
            "sys.stderr", stderr
        ):
            code = main(["wo yao ceshi"])

        self.assertEqual(code, 2)
        self.assertIn("missing config", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
