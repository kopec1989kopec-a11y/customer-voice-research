from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import AnalysisResult


_HOOK_DIRECTIONS = {
    "cleaning": "Показать, как товар убирает или упрощает самый раздражающий этап ухода.",
    "price": "Объяснить, за какой конкретный результат клиент платит и что он экономит.",
    "quality": "Снять страх поломки через демонстрацию прочности и реального сценария использования.",
    "usability": "Показать простой путь от распаковки до результата без лишних действий.",
    "delivery": "Сделать понятными сроки, упаковку и момент получения товара.",
    "other": "Выделить повторяющуюся формулировку клиента и проверить её отдельным креативом.",
}


def render_markdown(result: AnalysisResult, title: str = "Untitled") -> str:
    lines = [
        f"# Customer Voice Report: {title}",
        "",
        "## Dataset summary",
        "",
        f"- Comments received: **{result.total_input}**",
        f"- Comments kept after filtering: **{result.total_kept}**",
        f"- Duplicates removed: **{result.duplicates_removed}**",
        f"- Noise/spam removed: **{result.noise_removed}**",
        "",
        "## Main customer signals",
        "",
    ]
    if not result.clusters:
        lines.append("No substantive customer signals were found in the supplied comments.")
        return "\n".join(lines) + "\n"

    for cluster in result.clusters:
        direction = _HOOK_DIRECTIONS.get(cluster.label, _HOOK_DIRECTIONS["other"])
        lines.extend([
            f"### {cluster.label.title()} — {cluster.count} comments",
            "",
            f"**Hook direction:** {direction}",
            "",
            "**Evidence:**",
        ])
        for quote in cluster.quotes:
            source = quote.source
            likes = f"; {quote.likes} likes" if quote.likes else ""
            lines.append(f"> {quote.text}  \n> — {source}{likes}")
        lines.append("")
    return "\n".join(lines)


def write_analysis(result: AnalysisResult, path: str | Path) -> None:
    payload = asdict(result)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
