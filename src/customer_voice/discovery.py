from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator


def _tokens(value: str) -> set[str]:
    import re
    return {token for token in re.findall(r"[a-z0-9а-яё]+", value.lower()) if len(token) > 2}


def _source_text(item: "DiscoveryItem") -> str:
    metadata = item.metadata if isinstance(item.metadata, dict) else {}
    raw = metadata.get("raw", {}) if isinstance(metadata.get("raw", {}), dict) else {}
    fields = [item.title]
    if item.source == "reddit":
        fields.extend([str(metadata.get("subreddit", "")), str(raw.get("selftext", ""))])
    elif item.source == "youtube":
        fields.extend([str(metadata.get("channel", "")), str(raw.get("description", "")), str(raw.get("tags", ""))])
    elif item.source == "hackernews":
        fields.extend([str(raw.get("story_text", "")), str(raw.get("_tags", ""))])
    return " ".join(fields)


def _relevance(query: str, item: "DiscoveryItem") -> float:
    query_tokens = _tokens(query)
    text_tokens = _tokens(_source_text(item))
    overlap = len(query_tokens & text_tokens) / max(len(query_tokens), 1)
    compact_query = "".join(query.lower().split())
    compact_text = "".join(_source_text(item).lower().split())
    if compact_query and compact_query in compact_text:
        overlap = max(overlap, 1.0)
    return overlap


def _engagement(item: "DiscoveryItem") -> float:
    metadata = item.metadata if isinstance(item.metadata, dict) else {}
    raw = metadata.get("raw", {}) if isinstance(metadata.get("raw", {}), dict) else {}
    values = [metadata.get(key, 0) for key in ("score", "points", "likes", "view_count")]
    values.extend(raw.get(key, 0) for key in ("score", "points", "like_count", "view_count"))
    return max((float(value or 0) for value in values), default=0.0)


def rank_items(query: str, items: list["DiscoveryItem"], limit: int | None = None, per_source: int | None = None) -> list["DiscoveryItem"]:
    import math

    grouped: dict[str, list[DiscoveryItem]] = {}
    for item in items:
        grouped.setdefault(item.source, []).append(item)
    selected: list[DiscoveryItem] = []
    for source_items in grouped.values():
        max_engagement = max((_engagement(item) for item in source_items), default=0.0)

        def key(item: DiscoveryItem) -> tuple[float, float]:
            normalized_engagement = math.log1p(_engagement(item)) / max(math.log1p(max_engagement), 1.0)
            return _relevance(query, item), normalized_engagement

        ranked = sorted(source_items, key=key, reverse=True)
        selected.extend(ranked[:per_source] if per_source is not None else ranked)
    return selected[:limit] if limit is not None and per_source is None else selected


@dataclass(frozen=True)
class DiscoveryItem:
    source: str
    source_id: str
    title: str
    url: str = ""
    author: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class YouTubeDiscovery:
    source = "youtube"

    def __init__(self, runner: Callable[[list[str]], str] | None = None):
        self.runner = runner or self._run

    @staticmethod
    def _run(command: list[str]) -> str:
        return subprocess.run(command, check=True, capture_output=True, text=True).stdout

    def search(self, query: str, limit: int = 10) -> list[DiscoveryItem]:
        command = ["yt-dlp", "--dump-single-json", "--flat-playlist", "--skip-download", f"ytsearch{limit}:{query}"]
        payload = json.loads(self.runner(command))
        entries = payload.get("entries", [])[:limit]
        return [DiscoveryItem(
            source=self.source,
            source_id=entry.get("id", ""),
            title=entry.get("title", ""),
            url=entry.get("webpage_url") or entry.get("url", ""),
            author=entry.get("channel", "") or entry.get("uploader", ""),
            metadata={"raw": entry},
        ) for entry in entries if entry.get("id")]


class RedditDiscovery:
    source = "reddit"

    def __init__(self, fetch_page: Callable[[str, str | None], dict[str, Any]] | None = None):
        self.fetch_page = fetch_page or self._fetch_page

    @staticmethod
    def _fetch_page(query: str, after: str | None) -> dict[str, Any]:
        from urllib.parse import urlencode
        from urllib.request import Request, urlopen
        params: dict[str, Any] = {"q": query, "limit": 100, "raw_json": 1, "sort": "relevance"}
        if after:
            params["after"] = after
        request = Request(
            "https://www.reddit.com/search.json?" + urlencode(params),
            headers={"User-Agent": "customer-voice-research/0.1"},
        )
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read())

    def search(self, query: str, limit: int = 25) -> list[DiscoveryItem]:
        items: list[DiscoveryItem] = []
        after: str | None = None
        while len(items) < limit:
            payload = self.fetch_page(query, after)
            data = payload.get("data", {})
            for child in data.get("children", []):
                raw = child.get("data", {})
                if not raw.get("id"):
                    continue
                items.append(DiscoveryItem(
                    source=self.source,
                    source_id=raw["id"],
                    title=raw.get("title", ""),
                    url="https://www.reddit.com" + raw.get("permalink", ""),
                    author=raw.get("author", ""),
                    metadata={"subreddit": raw.get("subreddit", ""), "score": raw.get("score", 0), "raw": raw},
                ))
                if len(items) >= limit:
                    break
            after = data.get("after")
            if not after:
                break
        return items


class HackerNewsDiscovery:
    source = "hackernews"

    def __init__(self, fetch_page: Callable[[str, int], dict[str, Any]] | None = None):
        self.fetch_page = fetch_page or self._fetch_page

    @staticmethod
    def _fetch_page(query: str, page: int) -> dict[str, Any]:
        from urllib.parse import urlencode
        from urllib.request import Request, urlopen
        params = urlencode({"query": query, "tags": "story", "hitsPerPage": 100, "page": page})
        request = Request(f"https://hn.algolia.com/api/v1/search?{params}", headers={"User-Agent": "customer-voice-research/0.1"})
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read())

    def search(self, query: str, limit: int = 25) -> list[DiscoveryItem]:
        items: list[DiscoveryItem] = []
        page = 0
        while len(items) < limit:
            payload = self.fetch_page(query, page)
            for raw in payload.get("hits", []):
                if not raw.get("objectID"):
                    continue
                items.append(DiscoveryItem(
                    source=self.source,
                    source_id=raw["objectID"],
                    title=raw.get("title", "") or raw.get("story_title", ""),
                    url=raw.get("url") or f"https://news.ycombinator.com/item?id={raw['objectID']}",
                    author=raw.get("author", ""),
                    metadata={"points": raw.get("points", 0), "raw": raw},
                ))
                if len(items) >= limit:
                    break
            page += 1
            if page >= int(payload.get("nbPages", page)):
                break
        return items


def discover_all(query: str, limit: int = 10, discoverers: list[Any] | None = None) -> list[DiscoveryItem]:
    discoverers = discoverers or [YouTubeDiscovery(), RedditDiscovery(), HackerNewsDiscovery()]
    items: list[DiscoveryItem] = []
    for discoverer in discoverers:
        try:
            items.extend(discoverer.search(query, limit=limit))
        except (FileNotFoundError, OSError):
            # Optional tools and blocked/rate-limited sources must not block others.
            continue
    return rank_items(query, items, per_source=limit)
