from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import HackerNewsAdapter, RedditAdapter, SourceRegistry, YouTubeAdapter
from .core import analyze_comments
from .report import render_markdown, write_analysis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze public customer comments from JSONL records.")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--source", choices=["reddit", "youtube", "hackernews"])
    source_group.add_argument("--sources", help="Comma-separated sources for mixed JSONL input")
    parser.add_argument("--input", required=True, help="JSONL file with source records")
    parser.add_argument("--output", required=True, help="JSON or Markdown report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--title", default="Customer Voice")
    parser.add_argument("--min-words", type=int, default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = SourceRegistry([RedditAdapter(), YouTubeAdapter(), HackerNewsAdapter()])
    records = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.sources:
        sources = [source.strip() for source in args.sources.split(",") if source.strip()]
        comments = registry.collect_mixed_records(records, sources=sources)
        source_label = ",".join(sources)
    else:
        source_label = args.source
        comments = registry.collect_from_records(args.source, records)
    result = analyze_comments(comments, min_words=args.min_words)
    if args.format == "markdown":
        Path(args.output).write_text(render_markdown(result, title=args.title), encoding="utf-8")
    else:
        write_analysis(result, args.output)
    print(f"source={source_label} input={result.total_input} kept={result.total_kept} clusters={len(result.clusters)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
