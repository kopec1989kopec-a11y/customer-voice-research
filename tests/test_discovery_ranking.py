from customer_voice.discovery import DiscoveryItem, rank_items


def test_rank_items_prioritizes_query_match_then_engagement():
    items = [
        DiscoveryItem("reddit", "r1", "Kitchen gadgets discussion", metadata={"score": 100}),
        DiscoveryItem("reddit", "r2", "Portable blender problems", metadata={"score": 4}),
        DiscoveryItem("reddit", "r3", "Portable blender review", metadata={"score": 20}),
    ]

    ranked = rank_items("portable blender", items, limit=2)

    assert [item.source_id for item in ranked] == ["r3", "r2"]


def test_rank_items_uses_source_diversity_when_requested():
    items = [
        DiscoveryItem("reddit", "r1", "Portable blender review", metadata={"score": 100}),
        DiscoveryItem("reddit", "r2", "Portable blender problems", metadata={"score": 90}),
        DiscoveryItem("hackernews", "h1", "Portable blender discussion", metadata={"points": 2}),
    ]

    ranked = rank_items("portable blender", items, limit=2, per_source=1)

    assert {item.source for item in ranked} == {"reddit", "hackernews"}
