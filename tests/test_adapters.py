from customer_voice.adapters import HackerNewsAdapter, RedditAdapter, SourceRegistry, YouTubeAdapter


def test_registry_collects_mixed_source_records():
    registry = SourceRegistry([RedditAdapter(), YouTubeAdapter(), HackerNewsAdapter()])
    records = [
        {"source": "youtube", "id": "y1", "text": "The lid leaks badly"},
        {"source": "reddit", "id": "r1", "body": "Too expensive for this quality"},
        {"source": "hackernews", "id": "h1", "comment_text": "Setup is frustrating"},
    ]

    comments = registry.collect_mixed_records(records, sources=["youtube", "reddit", "hackernews"])

    assert [comment.source for comment in comments] == ["youtube", "reddit", "hackernews"]
    assert [comment.source_id for comment in comments] == ["y1", "r1", "h1"]
    result = __import__("customer_voice.core", fromlist=["analyze_comments"]).analyze_comments(comments)
    assert result.source_counts == {"youtube": 1, "reddit": 1, "hackernews": 1}


def test_registry_rejects_record_from_unrequested_source():
    registry = SourceRegistry([RedditAdapter(), YouTubeAdapter()])

    try:
        registry.collect_mixed_records([{"source": "reddit", "id": "r1", "body": "Valid text"}], sources=["youtube"])
    except ValueError as exc:
        assert "not requested" in str(exc)
    else:
        raise AssertionError("expected source validation error")
