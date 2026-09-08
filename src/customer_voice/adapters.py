from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from .core import normalize_comment
from .models import Comment


class SourceAdapter(ABC):
    name: str

    @abstractmethod
    def collect(self, query: str, **kwargs: Any) -> Iterable[Comment]:
        raise NotImplementedError

    def from_records(self, records: Iterable[dict[str, Any]]) -> list[Comment]:
        return [normalize_comment(source=self.name, **self.map_record(record)) for record in records]

    @abstractmethod
    def map_record(self, record: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class RedditAdapter(SourceAdapter):
    name = "reddit"

    def collect(self, query: str, **kwargs: Any) -> Iterable[Comment]:
        """Network collection is intentionally explicit; pass records in offline mode."""
        raise NotImplementedError("Use the Reddit API adapter in the network layer; offline fixtures are supported.")

    def map_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_id": record.get("id", ""),
            "text": record.get("body", record.get("text", "")),
            "author": record.get("author", ""),
            "url": record.get("url", ""),
            "published_at": record.get("created_at", record.get("published_at")),
            "likes": record.get("score", record.get("likes", 0)),
            "parent_id": record.get("parent_id"),
            "metadata": record,
        }


class HackerNewsAdapter(RedditAdapter):
    name = "hackernews"

    def map_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_id": record.get("objectID", record.get("id", "")),
            "text": record.get("comment_text", record.get("text", "")),
            "author": record.get("author", ""),
            "url": record.get("story_url", record.get("url", "")),
            "published_at": record.get("created_at", record.get("published_at")),
            "likes": record.get("points", record.get("likes", 0)),
            "parent_id": record.get("parent_id"),
            "metadata": record,
        }


class YouTubeAdapter(RedditAdapter):
    name = "youtube"

    def map_record(self, record: dict[str, Any]) -> dict[str, Any]:
        mapped = super().map_record(record)
        mapped["text"] = record.get("text", record.get("body", ""))
        mapped["likes"] = record.get("like_count", record.get("likes", 0))
        return mapped


class SourceRegistry:
    def __init__(self, adapters: Iterable[SourceAdapter] = ()):
        self._adapters = {adapter.name: adapter for adapter in adapters}

    def available_sources(self) -> list[str]:
        return sorted(self._adapters)

    def collect_from_records(self, source: str, records: Iterable[dict[str, Any]]) -> list[Comment]:
        try:
            adapter = self._adapters[source]
        except KeyError as exc:
            raise ValueError(f"Unknown source: {source}") from exc
        return adapter.from_records(records)

    def collect_mixed_records(self, records: Iterable[dict[str, Any]], sources: Iterable[str]) -> list[Comment]:
        requested = set(sources)
        comments: list[Comment] = []
        for record in records:
            source = record.get("source")
            if source not in requested:
                raise ValueError(f"Source {source!r} is not requested")
            comments.extend(self.collect_from_records(source, [record]))
        return comments
