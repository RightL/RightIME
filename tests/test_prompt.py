import unittest

from rightime import ConversionRequest
from rightime.prompt import build_prompt


class PromptBuilderTest(unittest.TestCase):
    def test_prompt_contains_context_and_current_draft(self) -> None:
        prompt = build_prompt(
            ConversionRequest(
                raw_text="wo xiang yao continuous input",
                session_context=("我们在讨论 rightIME。",),
            )
        )

        self.assertIn("Return only the converted text", prompt.instructions)
        self.assertIn("Do not use Markdown", prompt.instructions)
        self.assertIn("我们在讨论 rightIME。", prompt.input_text)
        self.assertIn("wo xiang yao continuous input", prompt.input_text)

    def test_prompt_preserves_ascii_terms_instruction(self) -> None:
        prompt = build_prompt(ConversionRequest(raw_text="ba API key fang zai settings li"))

        self.assertIn("Preserve clear English words", prompt.instructions)
        self.assertIn("Product names, code identifiers", prompt.instructions)


if __name__ == "__main__":
    unittest.main()
