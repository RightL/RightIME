import unittest
from unittest.mock import patch

from rightime.desktop_app import DEFAULT_HOTKEY, create_controller


class FakeEngine:
    pass


class FakeClipboard:
    def __init__(self) -> None:
        self.copied = []

    def copy(self, text: str) -> None:
        self.copied.append(text)


class FakePasteService:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.calls = 0

    def paste(self) -> bool:
        self.calls += 1
        return self.result


class DesktopAppTest(unittest.TestCase):
    def test_default_hotkey_is_explicit(self) -> None:
        self.assertEqual(DEFAULT_HOTKEY, "<ctrl>+<alt>+space")

    def test_create_controller_wires_copy_and_paste(self) -> None:
        clipboard = FakeClipboard()
        paste_service = FakePasteService()

        controller = create_controller(
            engine=FakeEngine(),
            clipboard=clipboard,
            paste_service=paste_service,
        )

        controller._copy_text("text")
        self.assertEqual(clipboard.copied, ["text"])
        self.assertTrue(controller._paste_text("text"))
        self.assertEqual(clipboard.copied, ["text", "text"])
        self.assertEqual(paste_service.calls, 1)

    def test_main_reports_runtime_configuration_error(self) -> None:
        with patch("rightime.desktop_app.load_runtime_config", side_effect=RuntimeError("missing config")):
            import rightime.desktop_app as app_module
            self.assertEqual(app_module.main([]), 2)


if __name__ == "__main__":
    unittest.main()
