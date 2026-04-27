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
