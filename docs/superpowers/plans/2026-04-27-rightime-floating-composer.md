# rightIME Floating Composer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Milestone 2: a hotkey-triggered minimal floating composer that uses the existing `ConversionEngine` to convert pinyin mixed with English, preview the result, and commit by paste or explicit copy.

**Architecture:** Keep the Milestone 2 desktop shell thin and testable. Put product behavior in a pure-Python controller with injected engine, clipboard, and paste callbacks; put OS-facing global hotkey and paste keystrokes behind adapters; put the visual panel in a small `tkinter` UI wrapper.

**Tech Stack:** Python 3.11+ in the `part` conda environment, existing `rightime` conversion engine, standard-library `tkinter`/`ttk` for the panel, optional `pynput>=1.8.1,<2` desktop extra for global hotkey and paste keystroke automation, `unittest` for tests.

**References:**
- Approved spec: `docs/superpowers/specs/2026-04-27-rightime-design.md`
- Milestone 1 engine plan: `docs/superpowers/plans/2026-04-27-rightime-conversion-engine.md`
- Python `tkinter` docs: https://docs.python.org/3.11/library/tkinter.html
- `pynput` keyboard docs: https://pynput.readthedocs.io/en/latest/keyboard-usage.html
- `pynput` PyPI release page: https://pypi.org/project/pynput/

---

## Scope

This plan implements Milestone 2 from the approved design:

- global hotkey
- input panel
- manual conversion trigger
- result preview
- accept, copy, and retry actions
- auto-paste into the previous app with visible failure reporting
- copy-only setting

This plan does not implement Windows TSF, macOS InputMethodKit, app packaging and signing, local model support, automatic surrounding-text capture, complex candidate selection UI, startup-at-login behavior, durable settings storage, or crash reporting.

## File Structure

- Modify: `pyproject.toml`  
  Add the `desktop` optional dependency and `rightime-composer` console entry point.
- Create: `src/rightime/runtime.py`  
  Shared runtime configuration and engine construction from environment variables.
- Modify: `src/rightime/cli.py`  
  Reuse `runtime.py` so CLI and composer share provider configuration.
- Create: `src/rightime/desktop/__init__.py`  
  Desktop shell package marker.
- Create: `src/rightime/desktop/state.py`  
  Immutable composer state and commit result types.
- Create: `src/rightime/desktop/controller.py`  
  Testable composer behavior: draft editing, conversion, result acceptance, copy, retry, session-context update.
- Create: `src/rightime/desktop/clipboard.py`  
  Clipboard abstraction plus Tk-backed clipboard implementation.
- Create: `src/rightime/desktop/paste.py`  
  Paste abstraction plus `pynput` paste keystroke implementation.
- Create: `src/rightime/desktop/hotkey.py`  
  Hotkey abstraction plus `pynput` global hotkey implementation.
- Create: `src/rightime/desktop/ui.py`  
  Minimal `tkinter` floating composer panel.
- Create: `src/rightime/desktop_app.py`  
  App wiring and `rightime-composer` entry point.
- Create: `tests/test_runtime.py`  
  Runtime configuration and engine construction tests.
- Create: `tests/test_desktop_state.py`  
  Composer state tests.
- Create: `tests/test_desktop_controller.py`  
  Controller behavior tests with fake engine and fake commit callbacks.
- Create: `tests/test_desktop_clipboard.py`  
  Tk clipboard adapter tests with a fake root object.
- Create: `tests/test_desktop_paste.py`  
  Paste adapter tests with fake keyboard objects.
- Create: `tests/test_desktop_hotkey.py`  
  Hotkey adapter tests with fake `pynput` class injection.
- Create: `tests/test_desktop_app.py`  
  App entry point tests that do not open a real GUI.

## Task 0: Branch Setup

**Files:**
- Modify: `.git/` metadata

- [ ] **Step 1: Create a feature branch**

Run:

```bash
git checkout master
git status --short
git switch -c feature/floating-composer
```

Expected: branch changes to `feature/floating-composer`. `git status --short` may show `.codex` as untracked; do not add it.

## Task 1: Shared Runtime Configuration

**Files:**
- Create: `src/rightime/runtime.py`
- Modify: `src/rightime/cli.py`
- Test: `tests/test_runtime.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing runtime tests**

Create `tests/test_runtime.py`:

```python
import os
import unittest
from unittest.mock import patch

from rightime.runtime import RuntimeConfig, build_engine, load_runtime_config


class RuntimeConfigTest(unittest.TestCase):
    def test_load_runtime_config_reads_required_environment(self) -> None:
        env = {
            "RIGHTIME_OPENAI_API_KEY": "secret",
            "RIGHTIME_OPENAI_MODEL": "test-model",
            "RIGHTIME_OPENAI_ENDPOINT": "https://example.test/responses",
        }

        with patch.dict(os.environ, env, clear=True):
            config = load_runtime_config()

        self.assertEqual(config.api_key, "secret")
        self.assertEqual(config.model, "test-model")
        self.assertEqual(config.endpoint, "https://example.test/responses")

    def test_load_runtime_config_reports_missing_names(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "RIGHTIME_OPENAI_API_KEY"):
                load_runtime_config()

    def test_build_engine_uses_provider_settings(self) -> None:
        created = []

        class FakeProvider:
            model = "fake"

            def __init__(self, **kwargs) -> None:
                created.append(kwargs)

        engine = build_engine(
            RuntimeConfig(api_key="secret", model="test-model", endpoint=None),
            provider_cls=FakeProvider,
        )

        self.assertEqual(created, [{"api_key": "secret", "model": "test-model"}])
        self.assertEqual(engine._provider.model, "fake")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_runtime -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'rightime.runtime'`.

- [ ] **Step 3: Add runtime config and update CLI**

Create `src/rightime/runtime.py`:

```python
import os
from dataclasses import dataclass
from typing import Type

from rightime.engine import ConversionEngine
from rightime.providers.openai_responses import OpenAIResponsesProvider


@dataclass(frozen=True)
class RuntimeConfig:
    api_key: str
    model: str
    endpoint: str | None = None


def load_runtime_config() -> RuntimeConfig:
    api_key = os.environ.get("RIGHTIME_OPENAI_API_KEY")
    model = os.environ.get("RIGHTIME_OPENAI_MODEL")
    endpoint = os.environ.get("RIGHTIME_OPENAI_ENDPOINT")

    missing = [
        name
        for name, value in (
            ("RIGHTIME_OPENAI_API_KEY", api_key),
            ("RIGHTIME_OPENAI_MODEL", model),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return RuntimeConfig(api_key=api_key, model=model, endpoint=endpoint)


def build_engine(
    config: RuntimeConfig,
    provider_cls: Type[OpenAIResponsesProvider] = OpenAIResponsesProvider,
) -> ConversionEngine:
    provider_kwargs = {"api_key": config.api_key, "model": config.model}
    if config.endpoint:
        provider_kwargs["endpoint"] = config.endpoint
    return ConversionEngine(provider=provider_cls(**provider_kwargs))
```

Modify `src/rightime/cli.py`:

```python
import argparse
import sys

from rightime.runtime import build_engine, load_runtime_config
from rightime.types import ConversionRequest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rightime-convert")
    parser.add_argument("text", help="Pinyin and English mixed draft to convert")
    parser.add_argument(
        "--context-line",
        action="append",
        default=[],
        help="Accepted session context line. May be passed multiple times.",
    )
    args = parser.parse_args(argv)

    try:
        engine = build_engine(load_runtime_config())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    result = engine.convert(
        ConversionRequest(
            raw_text=args.text,
            session_context=tuple(args.context_line),
        )
    )
    print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Modify `tests/test_cli.py`:

```python
import unittest
from io import StringIO
from unittest.mock import patch

from rightime import ConversionMetadata, ConversionResult
from rightime.cli import main


class FakeEngine:
    requests = []

    def convert(self, request):
        self.requests.append(request)
        return ConversionResult(
            text="我在写 rightIME。",
            metadata=ConversionMetadata(model="fake-model", latency_ms=33, token_count=10),
        )


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        FakeEngine.requests = []

    def test_cli_prints_conversion_text(self) -> None:
        stdout = StringIO()

        with patch("rightime.cli.load_runtime_config", return_value="config"), patch(
            "rightime.cli.build_engine", return_value=FakeEngine()
        ), patch("sys.stdout", stdout):
            code = main(["wo zai xie rightIME", "--context-line", "我们在讨论输入法。"])

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "我在写 rightIME。\n")
        self.assertEqual(FakeEngine.requests[0].raw_text, "wo zai xie rightIME")
        self.assertEqual(FakeEngine.requests[0].session_context, ("我们在讨论输入法。",))

    def test_cli_reports_runtime_configuration_error(self) -> None:
        stderr = StringIO()

        with patch("rightime.cli.load_runtime_config", side_effect=RuntimeError("missing config")), patch(
            "sys.stderr", stderr
        ):
            code = main(["wo yao ceshi"])

        self.assertEqual(code, 2)
        self.assertIn("missing config", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run runtime and CLI tests**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_runtime tests.test_cli -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/runtime.py src/rightime/cli.py tests/test_runtime.py tests/test_cli.py
git commit -m "feat: share runtime engine configuration"
```

Expected: Git creates the runtime configuration commit.

## Task 2: Composer State Types

**Files:**
- Create: `src/rightime/desktop/__init__.py`
- Create: `src/rightime/desktop/state.py`
- Test: `tests/test_desktop_state.py`

- [ ] **Step 1: Write the failing state tests**

Create `tests/test_desktop_state.py`:

```python
import unittest
from dataclasses import FrozenInstanceError

from rightime.desktop.state import CommitResult, ComposerState


class ComposerStateTest(unittest.TestCase):
    def test_initial_state_is_empty_and_ready(self) -> None:
        state = ComposerState.initial()

        self.assertEqual(state.draft, "")
        self.assertIsNone(state.result_text)
        self.assertEqual(state.status, "ready")
        self.assertFalse(state.is_busy)
        self.assertTrue(state.auto_paste_enabled)

    def test_state_is_immutable(self) -> None:
        state = ComposerState.initial()

        with self.assertRaises(FrozenInstanceError):
            state.draft = "changed"

    def test_commit_result_success_and_failure(self) -> None:
        self.assertEqual(CommitResult.success().message, "Pasted into previous app.")
        self.assertEqual(CommitResult.failure("Paste failed.").message, "Paste failed.")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_state -v
```

Expected: FAIL with missing `rightime.desktop`.

- [ ] **Step 3: Add state types**

Create `src/rightime/desktop/__init__.py`:

```python
"""Desktop floating composer shell for rightIME."""
```

Create `src/rightime/desktop/state.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ComposerState:
    draft: str
    result_text: str | None
    status: str
    message: str
    is_busy: bool
    auto_paste_enabled: bool

    @classmethod
    def initial(cls) -> "ComposerState":
        return cls(
            draft="",
            result_text=None,
            status="ready",
            message="",
            is_busy=False,
            auto_paste_enabled=True,
        )


@dataclass(frozen=True)
class CommitResult:
    ok: bool
    message: str

    @classmethod
    def success(cls) -> "CommitResult":
        return cls(ok=True, message="Pasted into previous app.")

    @classmethod
    def copied(cls) -> "CommitResult":
        return cls(ok=True, message="Copied result.")

    @classmethod
    def failure(cls, message: str) -> "CommitResult":
        return cls(ok=False, message=message)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_state -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/desktop/__init__.py src/rightime/desktop/state.py tests/test_desktop_state.py
git commit -m "feat: add floating composer state"
```

Expected: Git creates the state commit.

## Task 3: Composer Controller

**Files:**
- Create: `src/rightime/desktop/controller.py`
- Test: `tests/test_desktop_controller.py`

- [ ] **Step 1: Write the failing controller tests**

Create `tests/test_desktop_controller.py`:

```python
import unittest

from rightime import ConversionMetadata, ConversionResult
from rightime.desktop.controller import ComposerController
from rightime.provider import ProviderError


class FakeEngine:
    def __init__(self) -> None:
        self.requests = []
        self.results = [
            ConversionResult(
                text="我在写 rightIME。",
                metadata=ConversionMetadata(model="fake-model", latency_ms=12, token_count=9),
            )
        ]

    def convert(self, request):
        self.requests.append(request)
        return self.results.pop(0)


class FailingEngine:
    def convert(self, request):
        raise ProviderError("provider_unavailable", "network request failed")


class ComposerControllerTest(unittest.TestCase):
    def test_convert_uses_draft_and_session_context(self) -> None:
        engine = FakeEngine()
        copied = []
        pasted = []
        controller = ComposerController(
            engine=engine,
            copy_text=copied.append,
            paste_text=lambda text: pasted.append(text) or True,
        )

        controller.set_draft("wo zai xie rightIME")
        state = controller.convert()

        self.assertEqual(state.result_text, "我在写 rightIME。")
        self.assertEqual(state.status, "result")
        self.assertEqual(engine.requests[0].raw_text, "wo zai xie rightIME")
        self.assertEqual(engine.requests[0].session_context, ())

    def test_accept_auto_pastes_and_records_session_context(self) -> None:
        engine = FakeEngine()
        pasted = []
        controller = ComposerController(
            engine=engine,
            copy_text=lambda text: None,
            paste_text=lambda text: pasted.append(text) or True,
        )

        controller.set_draft("wo zai xie rightIME")
        controller.convert()
        state = controller.accept()

        self.assertEqual(pasted, ["我在写 rightIME。"])
        self.assertEqual(state.status, "ready")
        self.assertEqual(controller.session_context.accepted_outputs, ("我在写 rightIME。",))

    def test_copy_result_does_not_accept_session_context(self) -> None:
        engine = FakeEngine()
        copied = []
        controller = ComposerController(
            engine=engine,
            copy_text=copied.append,
            paste_text=lambda text: True,
        )

        controller.set_draft("wo zai xie rightIME")
        controller.convert()
        state = controller.copy_result()

        self.assertEqual(copied, ["我在写 rightIME。"])
        self.assertEqual(state.status, "result")
        self.assertEqual(controller.session_context.accepted_outputs, ())

    def test_paste_failure_is_visible_and_result_stays_available(self) -> None:
        engine = FakeEngine()
        controller = ComposerController(
            engine=engine,
            copy_text=lambda text: None,
            paste_text=lambda text: False,
        )

        controller.set_draft("wo zai xie rightIME")
        controller.convert()
        state = controller.accept()

        self.assertEqual(state.status, "error")
        self.assertIn("Paste failed", state.message)
        self.assertEqual(state.result_text, "我在写 rightIME。")

    def test_provider_failure_is_visible(self) -> None:
        controller = ComposerController(
            engine=FailingEngine(),
            copy_text=lambda text: None,
            paste_text=lambda text: True,
        )

        controller.set_draft("wo yao shibai")
        state = controller.convert()

        self.assertEqual(state.status, "error")
        self.assertIn("network request failed", state.message)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_controller -v
```

Expected: FAIL with missing `rightime.desktop.controller`.

- [ ] **Step 3: Add controller**

Create `src/rightime/desktop/controller.py`:

```python
from collections.abc import Callable

from rightime.context import SessionContext
from rightime.desktop.state import ComposerState
from rightime.provider import ProviderError
from rightime.types import ConversionRequest


class ComposerController:
    def __init__(
        self,
        engine,
        copy_text: Callable[[str], None],
        paste_text: Callable[[str], bool],
        auto_paste_enabled: bool = True,
    ) -> None:
        self._engine = engine
        self._copy_text = copy_text
        self._paste_text = paste_text
        self._session_context = SessionContext()
        self._state = ComposerState.initial()
        self._state = self._replace(auto_paste_enabled=auto_paste_enabled)

    @property
    def state(self) -> ComposerState:
        return self._state

    @property
    def session_context(self) -> SessionContext:
        return self._session_context

    def set_draft(self, draft: str) -> ComposerState:
        self._state = self._replace(draft=draft, status="ready", message="")
        return self._state

    def set_auto_paste_enabled(self, enabled: bool) -> ComposerState:
        self._state = self._replace(auto_paste_enabled=enabled)
        return self._state

    def convert(self) -> ComposerState:
        draft = self._state.draft.strip()
        if not draft:
            self._state = self._replace(status="error", message="Enter text before converting.")
            return self._state

        self._state = self._replace(status="converting", message="Converting...", is_busy=True)
        try:
            result = self._engine.convert(
                ConversionRequest(
                    raw_text=draft,
                    session_context=self._session_context.accepted_outputs,
                )
            )
        except ProviderError as exc:
            self._state = self._replace(status="error", message=str(exc), is_busy=False)
            return self._state

        self._state = self._replace(
            result_text=result.text,
            status="result",
            message=f"Converted with {result.metadata.model} in {result.metadata.latency_ms} ms.",
            is_busy=False,
        )
        return self._state

    def accept(self) -> ComposerState:
        if not self._state.result_text:
            self._state = self._replace(status="error", message="No result to accept.")
            return self._state

        result_text = self._state.result_text
        if self._state.auto_paste_enabled:
            pasted = self._paste_text(result_text)
            if not pasted:
                self._state = self._replace(
                    status="error",
                    message="Paste failed. Result is still available to copy.",
                )
                return self._state
        else:
            self._copy_text(result_text)

        self._session_context = self._session_context.accept(result_text)
        self._state = self._replace(
            draft="",
            result_text=None,
            status="ready",
            message="Accepted.",
            is_busy=False,
        )
        return self._state

    def copy_result(self) -> ComposerState:
        if not self._state.result_text:
            self._state = self._replace(status="error", message="No result to copy.")
            return self._state

        self._copy_text(self._state.result_text)
        self._state = self._replace(status="result", message="Copied result.")
        return self._state

    def retry(self) -> ComposerState:
        return self.convert()

    def _replace(self, **changes) -> ComposerState:
        data = {
            "draft": self._state.draft,
            "result_text": self._state.result_text,
            "status": self._state.status,
            "message": self._state.message,
            "is_busy": self._state.is_busy,
            "auto_paste_enabled": self._state.auto_paste_enabled,
        }
        data.update(changes)
        return ComposerState(**data)
```

- [ ] **Step 4: Run the controller tests**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_controller -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/desktop/controller.py tests/test_desktop_controller.py
git commit -m "feat: add floating composer controller"
```

Expected: Git creates the controller commit.

## Task 4: Clipboard And Paste Services

**Files:**
- Create: `src/rightime/desktop/clipboard.py`
- Create: `src/rightime/desktop/paste.py`
- Test: `tests/test_desktop_clipboard.py`
- Test: `tests/test_desktop_paste.py`

- [ ] **Step 1: Write failing clipboard and paste tests**

Create `tests/test_desktop_clipboard.py`:

```python
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
```

Create `tests/test_desktop_paste.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_clipboard tests.test_desktop_paste -v
```

Expected: FAIL with missing `rightime.desktop.clipboard` or `rightime.desktop.paste`.

- [ ] **Step 3: Add clipboard and paste services**

Create `src/rightime/desktop/clipboard.py`:

```python
class TkClipboard:
    def __init__(self, root) -> None:
        self._root = root

    def copy(self, text: str) -> None:
        self._root.clipboard_clear()
        self._root.clipboard_append(text)
        self._root.update()
```

Create `src/rightime/desktop/paste.py`:

```python
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
```

- [ ] **Step 4: Run the tests**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_clipboard tests.test_desktop_paste -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/desktop/clipboard.py src/rightime/desktop/paste.py tests/test_desktop_clipboard.py tests/test_desktop_paste.py
git commit -m "feat: add clipboard and paste services"
```

Expected: Git creates the clipboard and paste commit.

## Task 5: Global Hotkey Service

**Files:**
- Create: `src/rightime/desktop/hotkey.py`
- Test: `tests/test_desktop_hotkey.py`

- [ ] **Step 1: Write the failing hotkey tests**

Create `tests/test_desktop_hotkey.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_hotkey -v
```

Expected: FAIL with missing `rightime.desktop.hotkey`.

- [ ] **Step 3: Add hotkey service**

Create `src/rightime/desktop/hotkey.py`:

```python
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
```

- [ ] **Step 4: Run the test**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_hotkey -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/desktop/hotkey.py tests/test_desktop_hotkey.py
git commit -m "feat: add global hotkey service"
```

Expected: Git creates the hotkey service commit.

## Task 6: Tk Floating Composer UI

**Files:**
- Create: `src/rightime/desktop/ui.py`
- Test: `tests/test_desktop_ui.py`

- [ ] **Step 1: Write the failing UI adapter tests without opening a real window**

Create `tests/test_desktop_ui.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_ui -v
```

Expected: FAIL with missing `rightime.desktop.ui`.

- [ ] **Step 3: Add Tk UI module**

Create `src/rightime/desktop/ui.py`:

```python
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
```

- [ ] **Step 4: Run the UI adapter tests**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_ui -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/desktop/ui.py tests/test_desktop_ui.py
git commit -m "feat: add Tk floating composer UI"
```

Expected: Git creates the UI commit.

## Task 7: Desktop App Wiring And Entry Point

**Files:**
- Modify: `pyproject.toml`
- Create: `src/rightime/desktop_app.py`
- Test: `tests/test_desktop_app.py`

- [ ] **Step 1: Write failing desktop app tests**

Create `tests/test_desktop_app.py`:

```python
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
            self.assertEqual(__import__("rightime.desktop_app").desktop_app.main([]), 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_app -v
```

Expected: FAIL with missing `rightime.desktop_app`.

- [ ] **Step 3: Add desktop app entry point and optional dependency**

Modify `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "rightime"
version = "0.1.0"
description = "Cloud-first pinyin-to-Chinese conversion engine for rightIME"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
desktop = ["pynput>=1.8.1,<2"]

[project.scripts]
rightime-convert = "rightime.cli:main"
rightime-composer = "rightime.desktop_app:main"

[tool.setuptools.packages.find]
where = ["src"]
```

Create `src/rightime/desktop_app.py`:

```python
import argparse
import sys
import tkinter as tk

from rightime.desktop.clipboard import TkClipboard
from rightime.desktop.controller import ComposerController
from rightime.desktop.hotkey import PynputHotkeyService
from rightime.desktop.paste import PynputPasteService
from rightime.desktop.ui import ComposerWindow
from rightime.runtime import build_engine, load_runtime_config


DEFAULT_HOTKEY = "<ctrl>+<alt>+space"


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
```

- [ ] **Step 4: Run the desktop app tests**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_desktop_app -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add pyproject.toml src/rightime/desktop_app.py tests/test_desktop_app.py
git commit -m "feat: wire floating composer app"
```

Expected: Git creates the desktop app wiring commit.

## Task 8: Full Verification And Desktop Smoke Notes

**Files:**
- Create: `docs/superpowers/manual-tests/2026-04-27-floating-composer-smoke.md`

- [ ] **Step 1: Add manual smoke test instructions**

Create `docs/superpowers/manual-tests/2026-04-27-floating-composer-smoke.md`:

````markdown
# Floating Composer Manual Smoke Test

Date: 2026-04-27

## Setup

```bash
conda run -n part python -m pip install -e '.[desktop]'
export RIGHTIME_OPENAI_API_KEY='<key>'
export RIGHTIME_OPENAI_MODEL='<model>'
```

On macOS, grant Accessibility permission to the terminal or packaged app that runs `rightime-composer`.

## Run Without Global Hotkey

```bash
conda run -n part rightime-composer --no-hotkey
```

Expected:

- composer window opens
- typing pinyin in the input field works
- Return triggers conversion
- result preview shows one plain-text Chinese result
- Copy puts the result on the clipboard
- Accept copies the result and attempts paste
- paste failure remains visible and the result stays available

## Run With Global Hotkey

```bash
conda run -n part rightime-composer
```

Expected:

- app starts without showing the window
- pressing `<ctrl>+<alt>+space` opens the composer
- Escape hides the composer
````

- [ ] **Step 2: Run the full unit test suite**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest discover -s tests -v
```

Expected: all tests PASS.

- [ ] **Step 3: Run import smoke for the desktop modules**

Run:

```bash
PYTHONPATH=src conda run -n part python - <<'PY'
from rightime.desktop_app import DEFAULT_HOTKEY
from rightime.desktop.controller import ComposerController
print(DEFAULT_HOTKEY)
print(ComposerController.__name__)
PY
```

Expected stdout:

```text
<ctrl>+<alt>+space
ComposerController
```

- [ ] **Step 4: Run the manual desktop smoke test on Windows or macOS**

Run the instructions in `docs/superpowers/manual-tests/2026-04-27-floating-composer-smoke.md`.

Expected: all manual smoke test checks pass. If this is executed in a headless Linux environment, record that the manual smoke test was not run because the target platforms are Windows and macOS.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/superpowers/manual-tests/2026-04-27-floating-composer-smoke.md
git commit -m "test: add floating composer smoke checklist"
```

Expected: Git creates the smoke checklist commit.

## Completion Criteria

- `PYTHONPATH=src conda run -n part python -m unittest discover -s tests -v` passes.
- `rightime-composer --no-hotkey` opens the composer on a desktop OS with Tk available.
- The composer can collect draft pinyin text, trigger `ConversionEngine.convert()`, show the result, and keep the result visible after conversion.
- Accept tries to copy the result and send the paste keystroke.
- If paste reports failure, the UI shows a visible failure message and keeps the result available for explicit copy.
- Copy-only behavior is available by disabling Auto-paste.
- The default global hotkey is `<ctrl>+<alt>+space`.
- Global hotkey and paste automation are behind `pynput` adapters rather than embedded in the controller.
- No Windows TSF, macOS InputMethodKit, packaging, signing, local model, or surrounding-text capture code exists in this milestone.
