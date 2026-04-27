import unittest

from rightime import ConversionRequest
from rightime.engine import ConversionEngine
from rightime.provider import ProviderError, ProviderOutput


class FakeProvider:
    model = "fake-model"

    def __init__(self) -> None:
        self.prompts = []

    def convert(self, prompt):
        self.prompts.append(prompt)
        return ProviderOutput(text="我想要 continuous input", token_count=17)


class FailingProvider:
    model = "broken-model"

    def convert(self, prompt):
        raise ProviderError("provider_unavailable", "network request failed")


class ConversionEngineTest(unittest.TestCase):
    def test_convert_returns_provider_text_and_metadata(self) -> None:
        provider = FakeProvider()
        ticks = iter([10.0, 10.125])
        engine = ConversionEngine(provider=provider, clock=lambda: next(ticks))

        result = engine.convert(
            ConversionRequest(
                raw_text="wo xiang yao continuous input",
                session_context=("我们在讨论 rightIME。",),
            )
        )

        self.assertEqual(result.text, "我想要 continuous input")
        self.assertEqual(result.metadata.model, "fake-model")
        self.assertEqual(result.metadata.latency_ms, 125)
        self.assertEqual(result.metadata.token_count, 17)
        self.assertEqual(len(provider.prompts), 1)
        self.assertIn("我们在讨论 rightIME。", provider.prompts[0].input_text)

    def test_provider_failure_is_visible(self) -> None:
        engine = ConversionEngine(provider=FailingProvider())

        with self.assertRaisesRegex(ProviderError, "network request failed"):
            engine.convert(ConversionRequest(raw_text="wo yao shibai"))


if __name__ == "__main__":
    unittest.main()
