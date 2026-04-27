import argparse
import os
import sys

from rightime.engine import ConversionEngine
from rightime.providers.openai_responses import OpenAIResponsesProvider
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
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 2

    provider_kwargs = {"api_key": api_key, "model": model}
    if endpoint:
        provider_kwargs["endpoint"] = endpoint

    provider = OpenAIResponsesProvider(**provider_kwargs)
    engine = ConversionEngine(provider=provider)
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
