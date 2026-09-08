from customer_voice.core import analyze_comments, normalize_comment
from customer_voice.report import render_markdown


def test_render_markdown_exposes_evidence_and_hook_directions():
    comments = [
        normalize_comment(source="youtube", source_id="1", text="I hate cleaning this every day", likes=8),
        normalize_comment(source="reddit", source_id="2", text="Wish it was easier to clean after use", likes=3),
        normalize_comment(source="hackernews", source_id="3", text="The price is too expensive", likes=2),
    ]

    markdown = render_markdown(analyze_comments(comments), title="Portable Blender")

    assert "# Customer Voice Report: Portable Blender" in markdown
    assert "## Main customer signals" in markdown
    assert "cleaning" in markdown
    assert "I hate cleaning this every day" in markdown
    assert "Hook direction" in markdown
