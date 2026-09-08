from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Comment:
    source: str
    source_id: str
    text: str
    author: str = ""
    url: str = ""
    published_at: datetime | None = None
    likes: int = 0
    parent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Cluster:
    label: str
    count: int
    score: float
    quotes: list[Comment]


@dataclass(frozen=True)
class AnalysisResult:
    total_input: int
    total_kept: int
    duplicates_removed: int
    noise_removed: int
    clusters: list[Cluster]
