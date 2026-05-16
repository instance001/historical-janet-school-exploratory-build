import argparse
from pathlib import Path

from telemetry_engine import (
    EPISODES_FILE,
    TELEMETRY_JSON,
    TELEMETRY_MD,
    build_telemetry,
    write_json,
    write_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Janet telemetry CLI – build JSON + Markdown logs from episodes.jsonl"
    )
    parser.add_argument(
        "--episodes",
        type=str,
        default=EPISODES_FILE,
        help="Path to episodes.jsonl (default: episodes.jsonl)",
    )
    parser.add_argument(
        "--out-json",
        type=str,
        default=TELEMETRY_JSON,
        help="Output JSON path (default: telemetry_log.json)",
    )
    parser.add_argument(
        "--out-md",
        type=str,
        default=TELEMETRY_MD,
        help="Output Markdown path (default: telemetry_log.md)",
    )

    args = parser.parse_args()

    episodes_path = Path(args.episodes)
    telemetry = build_telemetry(episodes_path)

    write_json(telemetry, Path(args.out_json))
    write_markdown(telemetry, Path(args.out_md))

    print(f"[telemetry] Read episodes from: {episodes_path}")
    print(f"[telemetry] Wrote JSON to:    {args.out_json}")
    print(f"[telemetry] Wrote Markdown to: {args.out_md}")


if __name__ == "__main__":
    main()
