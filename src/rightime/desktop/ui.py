import tkinter as tk
from tkinter import ttk

from rightime.desktop.state import ComposerState


def snapshot_for_state(state: ComposerState) -> dict[str, object]:
    has_result = bool(state.result_text)
    return {
        "result": state.result_text or "",
        "message": state.message,
        "accept_enabled": has_result and not state.is_busy,
        "copy_enabled": has_result and not state.is_busy,
        "retry_enabled": has_result and not state.is_busy,
        "convert_enabled": bool(state.draft.strip()) and not state.is_busy,
        "auto_paste_enabled": state.auto_paste_enabled,
    }


class ComposerWindow:
    def __init__(self, root: tk.Tk, controller) -> None:
        self._root = root
        self._controller = controller
        self._draft = tk.StringVar()
        self._result = tk.StringVar()
        self._message = tk.StringVar()
        self._auto_paste = tk.BooleanVar(value=controller.state.auto_paste_enabled)

        root.title("rightIME")
        root.geometry("640x260")
        root.attributes("-topmost", True)
        root.withdraw()

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)

        self._entry = ttk.Entry(frame, textvariable=self._draft)
        self._entry.pack(fill="x")
        self._entry.bind("<Return>", lambda event: self.convert())
        self._entry.bind("<Control-Return>", lambda event: self.convert())

        result_label = ttk.Label(frame, textvariable=self._result, wraplength=600)
        result_label.pack(fill="x", pady=(12, 8))

        self._message_label = ttk.Label(frame, textvariable=self._message)
        self._message_label.pack(fill="x")

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(12, 0))

        self._convert_button = ttk.Button(controls, text="Convert", command=self.convert)
        self._accept_button = ttk.Button(controls, text="Accept", command=self.accept)
        self._copy_button = ttk.Button(controls, text="Copy", command=self.copy_result)
        self._retry_button = ttk.Button(controls, text="Retry", command=self.retry)
        self._auto_paste_check = ttk.Checkbutton(
            controls,
            text="Auto-paste",
            variable=self._auto_paste,
            command=self.toggle_auto_paste,
        )

        for widget in (
            self._convert_button,
            self._accept_button,
            self._copy_button,
            self._retry_button,
            self._auto_paste_check,
        ):
            widget.pack(side="left", padx=(0, 8))

        root.bind("<Escape>", lambda event: self.hide())
        self.render(controller.state)

    def show(self) -> None:
        self._root.deiconify()
        self._root.lift()
        self._entry.focus_set()

    def hide(self) -> None:
        self._root.withdraw()

    def convert(self) -> None:
        self._controller.set_draft(self._draft.get())
        self.render(self._controller.convert())

    def accept(self) -> None:
        self.render(self._controller.accept())
        if self._controller.state.status == "ready":
            self.hide()

    def copy_result(self) -> None:
        self.render(self._controller.copy_result())

    def retry(self) -> None:
        self.render(self._controller.retry())

    def toggle_auto_paste(self) -> None:
        self.render(self._controller.set_auto_paste_enabled(self._auto_paste.get()))

    def render(self, state: ComposerState) -> None:
        self._draft.set(state.draft)
        snapshot = snapshot_for_state(state)
        self._result.set(snapshot["result"])
        self._message.set(snapshot["message"])
        self._auto_paste.set(snapshot["auto_paste_enabled"])

        self._set_enabled(self._convert_button, snapshot["convert_enabled"])
        self._set_enabled(self._accept_button, snapshot["accept_enabled"])
        self._set_enabled(self._copy_button, snapshot["copy_enabled"])
        self._set_enabled(self._retry_button, snapshot["retry_enabled"])

    def _set_enabled(self, widget, enabled: bool) -> None:
        widget.configure(state="normal" if enabled else "disabled")
