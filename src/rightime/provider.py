from dataclasses import dataclass
from typing import Protocol

from rightime.types import ProviderPrompt


@dataclass(frozen=True)
class ProviderOutput:
    text: str
    token_count: int | None = None


class ProviderError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class ConversionProvider(Protocol):
    model: str

    def convert(self, prompt: ProviderPrompt) -> ProviderOutput:
        raise NotImplementedError
