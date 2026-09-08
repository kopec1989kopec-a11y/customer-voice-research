from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import RedditAdapter, SourceRegistry, YouTubeAdapter
from .core import analyze_comments
from .report import write_analysis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze public customer comments from JSONL records.")
    parser.add_argument("--source", choices=["reddit", "youtube"], required=True)
    parser.add_argument("--input", required=True, help="JSONL file with source records")
    parser.add_argument("--output", required=True, help="JSON report path")
    parser.add_argument("--min-words", type=int, default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = SourceRegistry([RedditAdapter(), YouTubeAdapter()])
    records = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    comments = registry.collect_from_records(args.source, records)
    result = analyze_comments(comments, min_words=args.min_words)
    write_analysis(result, args.output)
    print(f"source={args.source} input={result.total_input} kept={result.total_kept} clusters={len(result.clusters)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
