import unittest

from rightime.desktop.clipboard import TkClipboard


class FakeRoot:
    def __init__(self) -> None:
        self.value = ""
        self.updated = False

    def clipboard_clear(self) -> None:
        self.value = ""

    def clipboard_append(self, text: str) -> None:
        self.value += text

    def update(self) -> None:
        self.updated = True


class TkClipboardTest(unittest.TestCase):
    def test_copy_sets_clipboard_and_updates_root(self) -> None:
        root = FakeRoot()
        clipboard = TkClipboard(root)

        clipboard.copy("我在写 rightIME。")

        self.assertEqual(root.value, "我在写 rightIME。")
        self.assertTrue(root.updated)


if __name__ == "__main__":
    unittest.main()
