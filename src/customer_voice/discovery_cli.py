from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

from .discovery import discover_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discover public discussions across supported sources.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", required=True, help="JSON discovery file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    items = discover_all(args.query, limit=args.limit)
    payload = [asdict(item) if is_dataclass(item) else item for item in items]
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    by_source: dict[str, int] = {}
    for item in payload:
        by_source[item["source"]] = by_source.get(item["source"], 0) + 1
    print(f"query={args.query} discovered={len(payload)} sources={by_source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
