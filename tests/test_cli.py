import json

from customer_voice.cli import main


def test_cli_can_analyze_mixed_sources_in_one_input(tmp_path):
    source = tmp_path / "mixed.jsonl"
    source.write_text(
        json.dumps({"source": "youtube", "id": "y1", "text": "I hate cleaning this every day"}) + "\n"
        + json.dumps({"source": "reddit", "id": "r1", "body": "Too expensive for this quality"}) + "\n"
        + json.dumps({"source": "hackernews", "objectID": "h1", "comment_text": "The setup is frustrating"}) + "\n"
    )
    output = tmp_path / "mixed.md"

    assert main(["--sources", "youtube,reddit,hackernews", "--input", str(source), "--output", str(output), "--format", "markdown", "--title", "Mixed"]) == 0
    text = output.read_text()
    assert "Comments received: **3**" in text
    assert "**hackernews**: 1 comments" in text
    assert "**reddit**: 1 comments" in text
    assert "**youtube**: 1 comments" in text
    assert "Price" in text


def test_cli_can_write_customer_voice_markdown_report(tmp_path):
    source = tmp_path / "comments.jsonl"
    source.write_text(json.dumps({"id": "1", "text": "I hate cleaning this every day", "like_count": 4}) + "\n")
    output = tmp_path / "report.md"

    assert main(["--source", "youtube", "--input", str(source), "--output", str(output), "--format", "markdown", "--title", "Demo"]) == 0
    assert "# Customer Voice Report: Demo" in output.read_text()
