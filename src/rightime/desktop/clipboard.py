class TkClipboard:
    def __init__(self, root) -> None:
        self._root = root

    def copy(self, text: str) -> None:
        self._root.clipboard_clear()
        self._root.clipboard_append(text)
        self._root.update()
