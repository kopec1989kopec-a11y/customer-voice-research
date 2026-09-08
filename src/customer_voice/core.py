from __future__ import annotations

import html
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Iterable

from .models import AnalysisResult, Cluster, Comment

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+", re.I)
_NOISE = {"great video", "nice", "first", "lol", "thanks", "thank you", "buy now"}
_CLUSTER_TERMS = {
    "cleaning": ("clean", "cleaning", "wash", "mess", "dirty"),
    "price": ("price", "expensive", "cost", "cheap", "afford"),
    "quality": ("break", "broken", "durable", "quality", "cheaply made"),
    "usability": ("hard to use", "difficult", "confusing", "easy", "setup"),
    "delivery": ("shipping", "delivery", "arrived", "package", "delivery"),
}


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    value = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def normalize_text(text: str) -> str:
    text = html.unescape(_TAG_RE.sub(" ", text or ""))
    return _SPACE_RE.sub(" ", text).strip()


def normalize_comment(**data) -> Comment:
    return Comment(
        source=str(data.get("source", "unknown")).strip().lower(),
        source_id=str(data.get("source_id", "")).strip(),
        text=normalize_text(str(data.get("text", ""))),
        author=normalize_text(str(data.get("author", ""))),
        url=str(data.get("url", "") or ""),
        published_at=_parse_datetime(data.get("published_at")),
        likes=int(data.get("likes", 0) or 0),
        parent_id=data.get("parent_id"),
        metadata=dict(data.get("metadata") or {}),
    )


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9а-яё]+", " ", text.lower()).strip()


def _cluster_for(text: str) -> str:
    lower = text.lower()
    for label, terms in _CLUSTER_TERMS.items():
        if any(term in lower for term in terms):
            return label
    return "other"


def _is_noise(comment: Comment, min_words: int) -> bool:
    words = comment.text.split()
    lowered = comment.text.lower()
    return (
        len(words) < min_words
        or lowered in _NOISE
        or (_URL_RE.search(comment.text) and len(words) < 10)
    )


def analyze_comments(comments: Iterable[Comment], min_words: int = 4) -> AnalysisResult:
    rows = list(comments)
    unique: dict[str, Comment] = {}
    noise_removed = 0
    for comment in rows:
        if _is_noise(comment, min_words):
            noise_removed += 1
            continue
        key = _key(comment.text)
        if not key:
            noise_removed += 1
            continue
        previous = unique.get(key)
        if previous is None or comment.likes > previous.likes:
            unique[key] = comment

    kept = list(unique.values())
    clusters: dict[str, list[Comment]] = defaultdict(list)
    for comment in kept:
        clusters[_cluster_for(comment.text)].append(comment)

    result_clusters = []
    for label, items in clusters.items():
        items.sort(key=lambda item: item.likes, reverse=True)
        result_clusters.append(
            Cluster(
                label=label,
                count=len(items),
                score=sum(max(item.likes, 1) for item in items),
                quotes=items[:5],
            )
        )
    result_clusters.sort(key=lambda cluster: (cluster.count, cluster.score), reverse=True)
    return AnalysisResult(
        total_input=len(rows),
        total_kept=len(kept),
        duplicates_removed=len(rows) - noise_removed - len(kept),
        noise_removed=noise_removed,
        clusters=result_clusters,
        source_counts=dict(Counter(comment.source for comment in rows)),
    )
