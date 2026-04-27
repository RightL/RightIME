from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConversionSettings:
    locale: str = "zh-Hans"
    preserve_ascii_terms: bool = True


@dataclass(frozen=True)
class ConversionRequest:
    raw_text: str
    session_context: tuple[str, ...] = ()
    settings: ConversionSettings = field(default_factory=ConversionSettings)


@dataclass(frozen=True)
class ProviderPrompt:
    instructions: str
    input_text: str


@dataclass(frozen=True)
class ConversionMetadata:
    model: str
    latency_ms: int
    token_count: int | None = None


@dataclass(frozen=True)
class ConversionResult:
    text: str
    metadata: ConversionMetadata
