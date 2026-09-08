from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .report import render_markdown
from .research import ResearchPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discover, collect, and analyze customer voice in one run.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=10, help="Discovery limit per source")
    parser.add_argument("--max-comments", type=int, default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--title", default="Customer Voice")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = ResearchPipeline().run(args.query, limit=args.limit, max_comments=args.max_comments)
    if args.format == "markdown":
        summary = [
            f"# Research Run: {args.title}",
            "",
            f"- Query: `{result.query}`",
            f"- Discovered: **{result.discovery_count}**",
            f"- Comments collected: **{result.comment_count}**",
            f"- Skipped sources: **{', '.join(result.skipped_sources) or 'none'}**",
            "",
        ]
        Path(args.output).write_text("\n".join(summary) + render_markdown(result.analysis, title=args.title), encoding="utf-8")
    else:
        Path(args.output).write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"query={result.query} discovered={result.discovery_count} comments={result.comment_count} skipped={result.skipped_sources}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
