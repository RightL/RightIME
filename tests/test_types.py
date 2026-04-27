import unittest
from dataclasses import FrozenInstanceError

from rightime import (
    ConversionMetadata,
    ConversionRequest,
    ConversionResult,
    ConversionSettings,
    ProviderPrompt,
)


class DomainTypesTest(unittest.TestCase):
    def test_conversion_request_defaults(self) -> None:
        request = ConversionRequest(raw_text="wo zai xie rightIME")

        self.assertEqual(request.raw_text, "wo zai xie rightIME")
        self.assertEqual(request.session_context, ())
        self.assertEqual(request.settings.locale, "zh-Hans")
        self.assertTrue(request.settings.preserve_ascii_terms)

    def test_types_are_immutable(self) -> None:
        result = ConversionResult(
            text="我在写 rightIME",
            metadata=ConversionMetadata(model="test-model", latency_ms=12, token_count=8),
        )

        with self.assertRaises(FrozenInstanceError):
            result.text = "changed"

    def test_provider_prompt_carries_instructions_and_input(self) -> None:
        prompt = ProviderPrompt(
            instructions="Return plain text only.",
            input_text="Draft: wo yao ceshi",
        )

        self.assertIn("plain text", prompt.instructions)
        self.assertIn("wo yao ceshi", prompt.input_text)


if __name__ == "__main__":
    unittest.main()
