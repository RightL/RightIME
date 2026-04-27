import platform


class PynputPasteService:
    def __init__(self, keyboard=None, key=None, platform_name: str | None = None) -> None:
        if keyboard is None or key is None:
            from pynput.keyboard import Controller, Key

            keyboard = Controller()
            key = Key

        self._keyboard = keyboard
        self._key = key
        self._platform_name = platform_name or platform.system()

    def paste(self) -> bool:
        modifier = self._key.cmd if self._platform_name == "Darwin" else self._key.ctrl
        with self._keyboard.pressed(modifier):
            self._keyboard.press("v")
            self._keyboard.release("v")
        return True
