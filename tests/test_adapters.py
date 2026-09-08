from customer_voice.adapters import RedditAdapter, SourceRegistry
from customer_voice.models import Comment


def test_registry_lists_planned_sources_and_collects_fixture_data():
    registry = SourceRegistry([RedditAdapter()])

    assert "reddit" in registry.available_sources()
    rows = registry.collect_from_records(
        "reddit",
        [{"id": "t1_a", "body": "This product breaks after a week", "score": 9}],
    )

    assert len(rows) == 1
    assert rows[0].source == "reddit"
    assert rows[0].source_id == "t1_a"
    assert rows[0].text == "This product breaks after a week"
    assert rows[0].likes == 9
