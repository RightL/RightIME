class PynputHotkeyService:
    def __init__(self, hotkey: str, callback, global_hotkeys_cls=None) -> None:
        if global_hotkeys_cls is None:
            from pynput.keyboard import GlobalHotKeys

            global_hotkeys_cls = GlobalHotKeys

        self._hotkey = hotkey
        self._callback = callback
        self._global_hotkeys_cls = global_hotkeys_cls
        self._listener = None

    def start(self) -> None:
        if self._listener is not None:
            raise RuntimeError("Hotkey listener already started.")
        self._listener = self._global_hotkeys_cls({self._hotkey: self._callback})
        self._listener.start()

    def stop(self) -> None:
        if self._listener is None:
            return
        self._listener.stop()
        self._listener = None
