from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Callable, Iterable, Iterator
from typing import Any


def _retry_call(fn: Callable[[], Any], max_retries: int, backoff: float) -> Any:
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except (OSError, TimeoutError):
            if attempt >= max_retries:
                raise
            if backoff:
                time.sleep(backoff * (2 ** attempt))

from .core import normalize_comment
from .models import Comment


class YouTubeCollector:
    """Collect comments for a video using yt-dlp's JSON output.

    ``max_comments=None`` requests/keeps the full payload returned by yt-dlp.
    The caller controls the number of videos; this class does not silently cap
    the comment count to five.
    """

    name = "youtube"

    def __init__(self, runner: Callable[[list[str]], str] | None = None, max_retries: int = 2, backoff: float = 1.0):
        self.runner = runner or self._run
        self.max_retries = max_retries
        self.backoff = backoff
        self.stats = {"pages": 0, "raw_items": 0, "emitted_items": 0}

    @staticmethod
    def _run(command: list[str]) -> str:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout

    def collect_video(self, video_id: str, max_comments: int | None = None) -> Iterator[Comment]:
        requested = "all" if max_comments is None else str(max_comments)
        command = [
            "yt-dlp",
            "--write-comments",
            "--skip-download",
            "--dump-single-json",
            "--no-warnings",
            "--ignore-config",
            "--extractor-args",
            f"youtube:comment_sort=top;max_comments={requested},all,{requested}",
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        payload = json.loads(_retry_call(lambda: self.runner(command), self.max_retries, self.backoff))
        comments = payload.get("comments") or []
        self.stats["pages"] = 1
        self.stats["raw_items"] = len(comments)
        if max_comments is not None:
            comments = comments[:max_comments]
        for raw in comments:
            text = raw.get("text") or ""
            if not text:
                continue
            self.stats["emitted_items"] += 1
            yield normalize_comment(
                source=self.name,
                source_id=raw.get("id", ""),
                text=text,
                author=raw.get("author", ""),
                url=raw.get("webpage_url", "") or raw.get("url", ""),
                published_at=raw.get("timestamp") or raw.get("date"),
                likes=raw.get("like_count", 0),
                parent_id=raw.get("parent", None),
                metadata={"video_id": video_id, "raw": raw},
            )


class HackerNewsCollector:
    """Collect public HN comments through Algolia's paginated search API."""

    name = "hackernews"

    def __init__(self, fetch_page: Callable[[str, int], dict[str, Any]] | None = None, max_retries: int = 2, backoff: float = 1.0):
        self.fetch_page = fetch_page or self._fetch_page
        self.max_retries = max_retries
        self.backoff = backoff
        self.stats = {"pages": 0, "raw_items": 0, "emitted_items": 0}

    @staticmethod
    def _fetch_page(query: str, page: int) -> dict[str, Any]:
        from urllib.parse import urlencode
        from urllib.request import Request, urlopen
        params = urlencode({"query": query, "tags": "comment", "hitsPerPage": 100, "page": page})
        request = Request(f"https://hn.algolia.com/api/v1/search?{params}", headers={"User-Agent": "customer-voice-research/0.1"})
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read())

    def collect(self, query: str, max_pages: int | None = None) -> Iterator[Comment]:
        page = 0
        while max_pages is None or page < max_pages:
            payload = _retry_call(lambda: self.fetch_page(query, page), self.max_retries, self.backoff)
            hits = payload.get("hits", [])
            self.stats["pages"] += 1
            self.stats["raw_items"] += len(hits)
            for raw in hits:
                text = raw.get("comment_text") or ""
                if not text:
                    continue
                self.stats["emitted_items"] += 1
                yield normalize_comment(
                    source=self.name,
                    source_id=raw.get("objectID", ""),
                    text=text,
                    author=raw.get("author", ""),
                    url=raw.get("story_url") or f"https://news.ycombinator.com/item?id={raw.get('objectID', '')}",
                    published_at=raw.get("created_at"),
                    metadata={"raw": raw},
                )
            page += 1
            if page >= int(payload.get("nbPages", page)):
                break


class RedditCollector:
    """Collect all available comments from a Reddit thread listing.

    ``fetch_page`` receives the Reddit ``after`` cursor and returns one JSON
    listing. The default network implementation is deliberately not enabled
    until a caller supplies an HTTP client with its own rate-limit policy.
    """

    name = "reddit"

    @staticmethod
    def thread_url(thread_id: str, after: str | None = None) -> str:
        from urllib.parse import urlencode
        params = {"limit": 100, "raw_json": 1}
        if after:
            params["after"] = after
        return f"https://www.reddit.com/comments/{thread_id}.json?{urlencode(params)}"

    @classmethod
    def from_public_thread(cls, thread_id: str, user_agent: str = "customer-voice-research/0.1") -> "RedditCollector":
        from urllib.request import Request, urlopen

        def fetch_page(after: str | None = None) -> dict[str, Any]:
            request = Request(cls.thread_url(thread_id, after), headers={"User-Agent": user_agent})
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read())
            if isinstance(payload, list) and len(payload) > 1:
                return payload[1]
            return payload

        return cls(fetch_page=fetch_page)

    def __init__(self, fetch_page: Callable[[str | None], dict[str, Any]] | None = None, max_retries: int = 2, backoff: float = 1.0):
        self.fetch_page = fetch_page
        self.max_retries = max_retries
        self.backoff = backoff
        self.stats = {"pages": 0, "raw_items": 0, "emitted_items": 0}

    def collect_thread(self, thread_id: str) -> Iterator[Comment]:
        if self.fetch_page is None:
            raise RuntimeError("Provide a rate-limited Reddit fetch_page implementation")
        after: str | None = None
        while True:
            payload = _retry_call(lambda: self.fetch_page(after), self.max_retries, self.backoff)
            listing = payload[1] if isinstance(payload, list) and len(payload) > 1 else payload
            data = listing.get("data", {})
            self.stats["pages"] += 1
            children = data.get("children", [])
            self.stats["raw_items"] += len(children)
            for child in children:
                if child.get("kind") != "t1":
                    continue
                raw = child.get("data", {})
                body = raw.get("body", "")
                if not body:
                    continue
                self.stats["emitted_items"] += 1
                yield normalize_comment(
                    source=self.name,
                    source_id=raw.get("id", ""),
                    text=body,
                    author=raw.get("author", ""),
                    url=f"https://www.reddit.com{raw.get('permalink', '')}",
                    published_at=raw.get("created_utc"),
                    likes=raw.get("score", 0),
                    parent_id=raw.get("parent_id"),
                    metadata={"thread_id": thread_id, "raw": raw},
                )
            after = data.get("after")
            if not after:
                break
