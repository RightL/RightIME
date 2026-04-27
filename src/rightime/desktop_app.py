import argparse
import sys
import tkinter as tk

from rightime.desktop.clipboard import TkClipboard
from rightime.desktop.controller import ComposerController
from rightime.desktop.hotkey import PynputHotkeyService
from rightime.desktop.paste import PynputPasteService
from rightime.desktop.ui import ComposerWindow
from rightime.runtime import build_engine, load_runtime_config


DEFAULT_HOTKEY = "<ctrl>+<alt>+<space>"


def create_controller(engine, clipboard: TkClipboard, paste_service: PynputPasteService) -> ComposerController:
    def paste_text(text: str) -> bool:
        clipboard.copy(text)
        return paste_service.paste()

    return ComposerController(
        engine=engine,
        copy_text=clipboard.copy,
        paste_text=paste_text,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rightime-composer")
    parser.add_argument("--hotkey", default=DEFAULT_HOTKEY)
    parser.add_argument("--no-hotkey", action="store_true")
    args = parser.parse_args(argv)

    try:
        engine = build_engine(load_runtime_config())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    root = tk.Tk()
    clipboard = TkClipboard(root)
    paste_service = PynputPasteService()
    controller = create_controller(engine=engine, clipboard=clipboard, paste_service=paste_service)
    window = ComposerWindow(root=root, controller=controller)

    hotkey_service = None
    if args.no_hotkey:
        window.show()
    else:
        hotkey_service = PynputHotkeyService(hotkey=args.hotkey, callback=window.show)
        hotkey_service.start()

    try:
        root.mainloop()
    finally:
        if hotkey_service is not None:
            hotkey_service.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
