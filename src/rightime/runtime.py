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
