# Customer Voice Research

Multi-source collection and analysis of public comments for finding real customer pain, objections, language, and creative opportunities.

This is a **separate research engine**, not a fork of `last30days`. It is designed to use `last30days` for discovery while owning the deeper comment-collection layer.

## Goal

```text
product/category
  -> source discovery
  -> many public comments
  -> normalization + deduplication
  -> spam/noise filtering
  -> pain/objection clusters
  -> customer-language evidence
  -> hooks and creative hypotheses
```

## Current MVP

The first vertical slice is offline and deterministic:

- normalized comment model with source, URL, date, likes, parent thread and metadata;
- source adapter registry;
- Reddit thread collector with cursor pagination and public JSON endpoint;
- YouTube collector that keeps the full `yt-dlp` comment payload when requested;
- Hacker News collector through Algolia's paginated comment search;
- offline fixtures for deterministic development;
- deduplication across sources;
- noise and link-spam filtering;
- basic pain clusters (`cleaning`, `price`, `quality`, `usability`, `delivery`);
- JSON report output;
- pytest coverage.

Example:

```bash
.venv/bin/pip install -e '.[dev]'
PYTHONPATH=src .venv/bin/python -m customer_voice.cli \
  --source youtube \
  --input examples/comments.jsonl \
  --output /tmp/customer-voice-report.json
```

For a customer-facing evidence report:

```bash
PYTHONPATH=src .venv/bin/python -m customer_voice.cli \
  --source youtube \
  --input examples/comments.jsonl \
  --output /tmp/customer-voice-report.md \
  --format markdown \
  --title "Portable Blender"
```

The Markdown report includes source coverage, filtering statistics, ranked signals, evidence quotes, and a hook direction per signal.

For a single combined dataset from several platforms:

```bash
PYTHONPATH=src .venv/bin/python -m customer_voice.cli \
  --sources youtube,reddit,hackernews \
  --input examples/mixed_comments.jsonl \
  --output /tmp/mixed-customer-voice.md \
  --format markdown \
  --title "Portable Blender"
```

Each JSONL row must contain a `source` field. The analyzer then performs one cross-source deduplication and reports coverage per source.

```bash
PYTHONPATH=src .venv/bin/python -m customer_voice.discovery_cli \
  --query "portable blender" \
  --limit 10 \
  --output /tmp/discovery.json
```

The discovery file contains source IDs, titles, URLs, authors, and raw metadata. Results are ranked by query-term overlap in the title and source metadata, then by source-normalized engagement. Reddit uses score/comments and subreddit/selftext context; YouTube uses likes/views/channel/tags; Hacker News uses points/comments/story tags. Engagement is log-normalized within each source, so raw Reddit points are not compared directly with YouTube views. Ranking is applied per source so one platform cannot crowd out all other sources. Blocked, rate-limited, or unavailable optional sources are skipped explicitly; the CLI never fabricates results.

For the complete query-to-report run:

```bash
PYTHONPATH=src .venv/bin/python -m customer_voice.research_cli \
  --query "portable blender" \
  --limit 10 \
  --output /tmp/research.json \
  --raw-output /tmp/research.raw.jsonl
```

`--raw-output` writes one provenance-preserving JSON object per collected comment for later re-analysis. When `yt-dlp` is installed in the project virtualenv, YouTube discovery is invoked through the same Python interpreter (`python -m yt_dlp`), avoiding PATH mismatches.

Use `--format markdown` for a human-readable report. The run records discovered items, collected comments, skipped sources, source coverage, collector pages/raw/emitted counts, deduplication, noise filtering, evidence quotes, and hooks. Collectors retry transient network failures with exponential backoff and avoid duplicate query collection when discovery returns multiple items from the same source.

## Planned source adapters

| Source | Collection path | Status |
|---|---|---|
| YouTube | `yt-dlp` for keyless collection; Data API for paginated collection/replies | collector implemented; Data API next |
| Reddit | public JSON endpoint with cursor pagination | collector implemented |
| Hacker News | Algolia/API comments | collector implemented |
| X | authenticated API/cookie-backed adapter where eligible | planned |
| TikTok | ScrapeCreators or an approved provider | planned |
| Instagram | ScrapeCreators or an approved provider | planned |
| Threads / Pinterest | provider-specific adapters | planned |

“Many/all comments” means the maximum public, retrievable set. Deleted, private, hidden, disabled, or rate-limited comments cannot be promised. Raw public comments should be retained only as needed for evidence, with PII minimization and source attribution.

## Architecture

- `adapters.py` — source boundary and record mapping.
- `models.py` — stable internal data contract.
- `core.py` — source-independent normalization and analysis.
- `report.py` — JSON report serialization.
- `cli.py` — deterministic local entry point.

Network collectors will be added behind adapters. Credentials alone must never trigger a paid provider: each provider will have an explicit opt-in and a dry-run path.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
```

## Official references

- [YouTube CommentThreads: list](https://developers.google.com/youtube/v3/docs/commentThreads/list)
- [YouTube Comments: list](https://developers.google.com/youtube/v3/docs/comments/list)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [last30days](https://github.com/mvanhorn/last30days-skill)
