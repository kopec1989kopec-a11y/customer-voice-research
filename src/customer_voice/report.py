from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import AnalysisResult


def write_analysis(result: AnalysisResult, path: str | Path) -> None:
    payload = asdict(result)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
