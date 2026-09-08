from customer_voice.collectors import HackerNewsCollector, YouTubeCollector


def test_youtube_runner_retries_transient_failure():
    calls = []

    def runner(command):
        calls.append(command)
        if len(calls) == 1:
            raise OSError("temporary network error")
        return '{"comments": []}'

    list(YouTubeCollector(runner=runner, max_retries=2, backoff=0).collect_video("v1"))

    assert len(calls) == 2


def test_hackernews_fetch_retries_and_records_coverage():
    calls = []

    def fetch_page(query, page):
        calls.append(page)
        if len(calls) == 1:
            raise OSError("429")
        return {"hits": [], "nbPages": 1}

    collector = HackerNewsCollector(fetch_page=fetch_page, max_retries=2, backoff=0)
    list(collector.collect("demo"))

    assert calls == [0, 0]
    assert collector.stats == {"pages": 1, "raw_items": 0, "emitted_items": 0}
