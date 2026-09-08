from customer_voice.models import Comment
from customer_voice.research import ResearchPipeline


class FakeDiscoverer:
    def search(self, query, limit):
        from customer_voice.discovery import DiscoveryItem
        return [
            DiscoveryItem("youtube", "v1", "Video", "https://youtube/v1"),
            DiscoveryItem("reddit", "r1", "Thread", "https://reddit/r1"),
        ]


class FakeYouTube:
    def collect_video(self, source_id, max_comments=None):
        return iter([Comment("youtube", "c1", "I hate cleaning this every day", likes=4)])


class FakeReddit:
    def collect_thread(self, source_id):
        return iter([Comment("reddit", "c2", "Too expensive for this quality", likes=3)])


def test_pipeline_runs_discovery_collection_and_analysis():
    pipeline = ResearchPipeline(
        discoverers=[FakeDiscoverer()],
        youtube=FakeYouTube(),
        reddit=FakeReddit(),
    )

    result = pipeline.run("portable blender", limit=5)

    assert result.discovery_count == 2
    assert result.comment_count == 2
    assert result.analysis.total_kept == 2
    assert result.analysis.source_counts == {"youtube": 1, "reddit": 1}
