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
