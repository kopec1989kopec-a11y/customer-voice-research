from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .core import analyze_comments
from .collectors import HackerNewsCollector, RedditCollector, YouTubeCollector
from .discovery import DiscoveryItem, HackerNewsDiscovery, RedditDiscovery, YouTubeDiscovery, discover_all
from .models import AnalysisResult, Comment


@dataclass(frozen=True)
class ResearchResult:
    query: str
    discovered: list[DiscoveryItem]
    comments: list[Comment]
    analysis: AnalysisResult
    skipped_sources: list[str] = field(default_factory=list)

    @property
    def discovery_count(self) -> int:
        return len(self.discovered)

    @property
    def comment_count(self) -> int:
        return len(self.comments)


class ResearchPipeline:
    """Run discovery, source-specific collection, and source-independent analysis."""

    def __init__(
        self,
        discoverers: list[Any] | None = None,
        youtube: Any | None = None,
        reddit: Any | None = None,
        hackernews: Any | None = None,
    ):
        self.discoverers = discoverers or [YouTubeDiscovery(), RedditDiscovery(), HackerNewsDiscovery()]
        self.youtube = youtube or YouTubeCollector()
        self.reddit = reddit or RedditCollector()
        self.hackernews = hackernews or HackerNewsCollector()

    def run(self, query: str, limit: int = 10, max_comments: int | None = None, min_words: int = 4) -> ResearchResult:
        discovered = discover_all(query, limit=limit, discoverers=self.discoverers)
        comments: list[Comment] = []
        skipped: list[str] = []
        for item in discovered:
            try:
                if item.source == "youtube" and self.youtube is not None:
                    comments.extend(self.youtube.collect_video(item.source_id, max_comments=max_comments))
                elif item.source == "reddit" and self.reddit is not None:
                    comments.extend(self.reddit.collect_thread(item.source_id))
                elif item.source == "hackernews" and self.hackernews is not None:
                    # HN comment search is query-based; its collector paginates comments for the query.
                    comments.extend(self.hackernews.collect(query, max_pages=1))
                else:
                    skipped.append(item.source)
            except (FileNotFoundError, OSError, RuntimeError):
                skipped.append(item.source)
        return ResearchResult(
            query=query,
            discovered=discovered,
            comments=comments,
            analysis=analyze_comments(comments, min_words=min_words),
            skipped_sources=sorted(set(skipped)),
        )
