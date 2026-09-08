from datetime import datetime, timezone

from customer_voice.core import analyze_comments, normalize_comment
from customer_voice.models import Comment


def test_normalize_comment_strips_html_and_collapses_whitespace():
    comment = normalize_comment(
        source="youtube",
        source_id="abc",
        author=" buyer ",
        text="  <b>This</b>   is\n actually useful.  ",
        url="https://example.com/c/1",
        published_at="2026-01-02T03:04:05Z",
        likes=7,
    )

    assert comment.text == "This is actually useful."
    assert comment.author == "buyer"
    assert comment.likes == 7
    assert comment.published_at == datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def test_analyze_comments_removes_noise_deduplicates_and_clusters_language():
    comments = [
        Comment(source="youtube", source_id="1", text="I hate cleaning this every day", likes=4),
        Comment(source="reddit", source_id="2", text="I hate cleaning this every day!", likes=2),
        Comment(source="youtube", source_id="3", text="Wish it was easier to clean after use", likes=3),
        Comment(source="youtube", source_id="4", text="Great video", likes=100),
        Comment(source="youtube", source_id="5", text="Buy now https://spam.example", likes=1),
    ]

    result = analyze_comments(comments, min_words=4)

    assert result.total_input == 5
    assert result.total_kept == 2
    assert result.duplicates_removed == 1
    assert result.noise_removed == 2
    assert result.clusters[0].label == "cleaning"
    assert result.clusters[0].count == 2
    assert result.clusters[0].quotes[0].text.startswith("I hate cleaning")
