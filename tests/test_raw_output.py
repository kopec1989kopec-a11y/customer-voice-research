import json

from customer_voice.models import AnalysisResult
from customer_voice.research import ResearchPipeline, ResearchResult
from customer_voice.research_cli import main


def test_research_cli_writes_raw_jsonl(monkeypatch, tmp_path):
    raw = tmp_path / "raw.jsonl"
    output = tmp_path / "report.json"
    empty = ResearchResult("demo", [], [], AnalysisResult(0, 0, 0, 0, []))
    monkeypatch.setattr(ResearchPipeline, "run", lambda self, query, limit, max_comments: empty)

    assert main(["--query", "demo", "--output", str(output), "--raw-output", str(raw)]) == 0
    assert raw.read_text(encoding="utf-8") == ""
