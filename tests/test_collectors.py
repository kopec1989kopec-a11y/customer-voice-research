from customer_voice.collectors import RedditCollector


def test_reddit_thread_url_contains_cursor_and_json_endpoint():
    url = RedditCollector.thread_url("abc123", after="t3_next")

    assert url.startswith("https://www.reddit.com/comments/abc123.json?")
    assert "after=t3_next" in url
    assert "limit=100" in url
