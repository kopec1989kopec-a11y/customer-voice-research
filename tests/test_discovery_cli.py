import json

from customer_voice.discovery_cli import main


def test_discovery_cli_writes_json(tmp_path, monkeypatch):
    output = tmp_path / "discovery.json"
    monkeypatch.setattr(
        "customer_voice.discovery_cli.discover_all",
        lambda query, limit: [{"source": "reddit", "source_id": "r1", "title": query}],
    )

    assert main(["--query", "portable blender", "--limit", "3", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload[0]["source_id"] == "r1"
