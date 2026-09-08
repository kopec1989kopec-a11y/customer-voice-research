from customer_voice.discovery import DiscoveryItem, rank_items


def test_source_specific_metadata_improves_relevance():
    items = [
        DiscoveryItem("reddit", "r1", "Product discussion", metadata={"subreddit": "portableblender", "score": 2}),
        DiscoveryItem("reddit", "r2", "Product discussion", metadata={"subreddit": "kitchen", "score": 100}),
    ]

    ranked = rank_items("portable blender", items, limit=2)

    assert ranked[0].source_id == "r1"


def test_engagement_is_normalized_within_source():
    items = [
        DiscoveryItem("reddit", "r1", "Portable blender review", metadata={"score": 1000}),
        DiscoveryItem("reddit", "r2", "Portable blender problems", metadata={"score": 10}),
        DiscoveryItem("hackernews", "h1", "Portable blender discussion", metadata={"points": 20}),
    ]

    ranked = rank_items("portable blender", items, limit=3)

    assert {item.source_id for item in ranked} == {"r1", "r2", "h1"}
    assert ranked[0].source == "reddit"
