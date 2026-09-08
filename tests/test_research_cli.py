import json

from customer_voice.research_cli import main
from customer_voice.research import ResearchResult
from customer_voice.models import AnalysisResult


def test_research_cli_writes_json(monkeypatch, tmp_path):
    output = tmp_path / "research.json"
    fake = ResearchResult(
        query="demo",
        discovered=[],
        comments=[],
        analysis=AnalysisResult(0, 0, 0, 0, []),
    )
    monkeypatch.setattr("customer_voice.research_cli.ResearchPipeline", lambda: type("P", (), {"run": lambda self, query, limit, max_comments: fake})())

    assert main(["--query", "demo", "--limit", "2", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["query"] == "demo"
    assert payload["analysis"]["total_input"] == 0
