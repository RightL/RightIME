import unittest

from rightime import SessionContext


class SessionContextTest(unittest.TestCase):
    def test_accept_returns_new_context_with_text(self) -> None:
        context = SessionContext()
        updated = context.accept("我现在在写 rightIME")

        self.assertEqual(context.accepted_outputs, ())
        self.assertEqual(updated.accepted_outputs, ("我现在在写 rightIME",))

    def test_as_prompt_context_lists_recent_outputs(self) -> None:
        context = (
            SessionContext()
            .accept("第一句")
            .accept("第二句")
            .accept("第三句")
        )

        self.assertEqual(context.as_prompt_context(max_items=2), "- 第二句\n- 第三句")

    def test_empty_context_has_explicit_marker(self) -> None:
        self.assertEqual(SessionContext().as_prompt_context(), "(no accepted text yet)")


if __name__ == "__main__":
    unittest.main()
