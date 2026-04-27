from dataclasses import dataclass


@dataclass(frozen=True)
class SessionContext:
    accepted_outputs: tuple[str, ...] = ()

    def accept(self, text: str) -> "SessionContext":
        return SessionContext(accepted_outputs=(*self.accepted_outputs, text))

    def as_prompt_context(self, max_items: int = 6) -> str:
        if not self.accepted_outputs:
            return "(no accepted text yet)"
        recent = self.accepted_outputs[-max_items:]
        return "\n".join(f"- {item}" for item in recent)
