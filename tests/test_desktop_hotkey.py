import unittest

from rightime.desktop.hotkey import PynputHotkeyService


class FakeGlobalHotKeys:
    created = []

    def __init__(self, bindings):
        self.bindings = bindings
        self.started = False
        self.stopped = False
        FakeGlobalHotKeys.created.append(self)

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


class PynputHotkeyServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        FakeGlobalHotKeys.created = []

    def test_start_registers_hotkey(self) -> None:
        activated = []
        service = PynputHotkeyService(
            hotkey="<ctrl>+<alt>+space",
            callback=lambda: activated.append(True),
            global_hotkeys_cls=FakeGlobalHotKeys,
        )

        service.start()
        FakeGlobalHotKeys.created[0].bindings["<ctrl>+<alt>+space"]()

        self.assertTrue(FakeGlobalHotKeys.created[0].started)
        self.assertEqual(activated, [True])

    def test_stop_stops_listener(self) -> None:
        service = PynputHotkeyService(
            hotkey="<ctrl>+<alt>+space",
            callback=lambda: None,
            global_hotkeys_cls=FakeGlobalHotKeys,
        )

        service.start()
        service.stop()

        self.assertTrue(FakeGlobalHotKeys.created[0].stopped)


if __name__ == "__main__":
    unittest.main()
