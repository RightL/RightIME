import unittest

from rightime.desktop.state import ComposerState
from rightime.desktop.ui import snapshot_for_state


class UiSnapshotTest(unittest.TestCase):
    def test_snapshot_for_ready_state(self) -> None:
        snapshot = snapshot_for_state(ComposerState.initial())

        self.assertEqual(snapshot["result"], "")
        self.assertEqual(snapshot["message"], "")
        self.assertFalse(snapshot["accept_enabled"])
        self.assertFalse(snapshot["retry_enabled"])

    def test_snapshot_for_result_state(self) -> None:
        state = ComposerState(
            draft="wo zai xie rightIME",
            result_text="我在写 rightIME。",
            status="result",
            message="Converted.",
            is_busy=False,
            auto_paste_enabled=True,
        )

        snapshot = snapshot_for_state(state)

        self.assertEqual(snapshot["result"], "我在写 rightIME。")
        self.assertEqual(snapshot["message"], "Converted.")
        self.assertTrue(snapshot["accept_enabled"])
        self.assertTrue(snapshot["retry_enabled"])


if __name__ == "__main__":
    unittest.main()
