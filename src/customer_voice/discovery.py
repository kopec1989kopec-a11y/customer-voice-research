from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator


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
                    metadata={"subreddit": raw.get("subreddit", ""), "raw": raw},
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
                    metadata={"raw": raw},
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
    return items
