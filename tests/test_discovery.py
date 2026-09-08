from customer_voice.discovery import DiscoveryItem, discover_all


def test_discover_all_skips_unavailable_optional_source():
    class Missing:
        def search(self, query, limit):
            raise FileNotFoundError("yt-dlp")

    class Available:
        def search(self, query, limit):
            return [DiscoveryItem(source="hackernews", source_id="h1", title="Discussion")]

    items = discover_all("portable blender", limit=2, discoverers=[Missing(), Available()])

    assert [item.source_id for item in items] == ["h1"]
