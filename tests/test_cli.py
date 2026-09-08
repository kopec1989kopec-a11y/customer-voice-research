import json

from customer_voice.cli import main


def test_cli_can_write_customer_voice_markdown_report(tmp_path):
    source = tmp_path / "comments.jsonl"
    source.write_text(json.dumps({"id": "1", "text": "I hate cleaning this every day", "like_count": 4}) + "\n")
    output = tmp_path / "report.md"

    assert main(["--source", "youtube", "--input", str(source), "--output", str(output), "--format", "markdown", "--title", "Demo"]) == 0
    assert "# Customer Voice Report: Demo" in output.read_text()
