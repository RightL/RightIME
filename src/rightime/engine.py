from collections.abc import Callable
from time import monotonic

from rightime.prompt import build_prompt
from rightime.provider import ConversionProvider
from rightime.types import ConversionMetadata, ConversionRequest, ConversionResult


class ConversionEngine:
    def __init__(
        self,
        provider: ConversionProvider,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._provider = provider
        self._clock = clock

    def convert(self, request: ConversionRequest) -> ConversionResult:
        prompt = build_prompt(request)
        started = self._clock()
        provider_output = self._provider.convert(prompt)
        finished = self._clock()

        metadata = ConversionMetadata(
            model=self._provider.model,
            latency_ms=round((finished - started) * 1000),
            token_count=provider_output.token_count,
        )
        return ConversionResult(text=provider_output.text, metadata=metadata)
