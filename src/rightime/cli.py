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
