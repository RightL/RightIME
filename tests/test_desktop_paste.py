import unittest

from rightime.desktop.paste import PynputPasteService


class FakeKey:
    ctrl = "ctrl"
    cmd = "cmd"


class FakeKeyboard:
    def __init__(self) -> None:
        self.actions = []

    def pressed(self, modifier):
        self.actions.append(("pressed", modifier))
        return self

    def __enter__(self):
        self.actions.append(("enter",))
        return self

    def __exit__(self, exc_type, exc, tb):
        self.actions.append(("exit",))

    def press(self, key):
        self.actions.append(("press", key))

    def release(self, key):
        self.actions.append(("release", key))


class PynputPasteServiceTest(unittest.TestCase):
    def test_windows_uses_ctrl_v(self) -> None:
        keyboard = FakeKeyboard()
        service = PynputPasteService(keyboard=keyboard, key=FakeKey, platform_name="Windows")

        self.assertTrue(service.paste())
        self.assertIn(("pressed", "ctrl"), keyboard.actions)
        self.assertIn(("press", "v"), keyboard.actions)

    def test_macos_uses_cmd_v(self) -> None:
        keyboard = FakeKeyboard()
        service = PynputPasteService(keyboard=keyboard, key=FakeKey, platform_name="Darwin")

        self.assertTrue(service.paste())
        self.assertIn(("pressed", "cmd"), keyboard.actions)
        self.assertIn(("release", "v"), keyboard.actions)


if __name__ == "__main__":
    unittest.main()
