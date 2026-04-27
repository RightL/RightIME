import unittest
from dataclasses import FrozenInstanceError

from rightime.desktop.state import CommitResult, ComposerState


class ComposerStateTest(unittest.TestCase):
    def test_initial_state_is_empty_and_ready(self) -> None:
        state = ComposerState.initial()

        self.assertEqual(state.draft, "")
        self.assertIsNone(state.result_text)
        self.assertEqual(state.status, "ready")
        self.assertFalse(state.is_busy)
        self.assertTrue(state.auto_paste_enabled)

    def test_state_is_immutable(self) -> None:
        state = ComposerState.initial()

        with self.assertRaises(FrozenInstanceError):
            state.draft = "changed"

    def test_commit_result_success_and_failure(self) -> None:
        self.assertEqual(CommitResult.success().message, "Pasted into previous app.")
        self.assertEqual(CommitResult.failure("Paste failed.").message, "Paste failed.")


if __name__ == "__main__":
    unittest.main()
