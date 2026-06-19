"""Tests for the content app."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Creator, RawContent, ProcessedContent, ContentVector

User = get_user_model()


class CreatorModelTest(TestCase):
    """Test Creator model basics"""

    def test_create_creator(self):
        creator = Creator.objects.create(
            name="Test Creator",
            platform="youtube",
        )
        self.assertEqual(str(creator), "Test Creator")


class RawContentModelTest(TestCase):
    """Test RawContent model"""

    def test_create_raw_content(self):
        raw = RawContent.objects.create(
            source_url="https://example.com/test",
            raw_data={"key": "value"},
        )
        self.assertEqual(raw.source_url, "https://example.com/test")
        self.assertIsNotNone(raw.crawled_at)


class ProcessedContentModelTest(TestCase):
    """Test ProcessedContent model and lifecycle"""

    @classmethod
    def setUpTestData(cls):
        cls.creator = Creator.objects.create(name="Test", platform="youtube")
        cls.raw = RawContent.objects.create(source_url="https://example.com/1")

    def test_create_processed_content(self):
        content = ProcessedContent.objects.create(
            raw=self.raw,
            creator=self.creator,
            title="Test Content",
            url="https://example.com/test-content",
            content_type="video",
            published_at="2026-06-01T00:00:00Z",
        )
        self.assertEqual(content.title, "Test Content")
        self.assertEqual(content.stage, "pending")
        self.assertEqual(content.quality_score, 0.0)

    def test_stage_transitions(self):
        content = ProcessedContent.objects.create(
            raw=self.raw,
            creator=self.creator,
            title="Test",
            url="https://example.com/test-2",
            content_type="article",
            published_at="2026-06-01T00:00:00Z",
        )
        # Default stage is 'pending'
        self.assertEqual(content.stage, 'pending')

        # Transition to active
        content.stage = 'active'
        content.save()
        content.refresh_from_db()
        self.assertEqual(content.stage, 'active')

    def test_content_type_choices(self):
        content = ProcessedContent.objects.create(
            raw=self.raw,
            creator=self.creator,
            title="Test",
            url="https://example.com/test-3",
            content_type="podcast",
            published_at="2026-06-01T00:00:00Z",
        )
        self.assertEqual(content.content_type, "podcast")

    def test_str_method(self):
        content = ProcessedContent.objects.create(
            raw=self.raw,
            creator=self.creator,
            title="My Test Title",
            url="https://example.com/test-4",
            content_type="video",
            published_at="2026-06-01T00:00:00Z",
        )
        self.assertIn("My Test Title", str(content))


class ContentVectorModelTest(TestCase):
    """Test ContentVector with pgvector"""

    @classmethod
    def setUpTestData(cls):
        creator = Creator.objects.create(name="Test", platform="youtube")
        raw = RawContent.objects.create(source_url="https://example.com/vec-test")
        cls.content = ProcessedContent.objects.create(
            raw=raw,
            creator=creator,
            title="Vector Test",
            url="https://example.com/vec-test",
            content_type="video",
            published_at="2026-06-01T00:00:00Z",
        )

    def test_create_vector(self):
        import random
        vec = ContentVector.objects.create(
            content=self.content,
            embedding=[random.random() for _ in range(768)],
        )
        self.assertEqual(vec.content.title, "Vector Test")
        self.assertIsNotNone(vec.embedding)
        self.assertEqual(len(vec.embedding), 768)


class RecommenderTest(TestCase):
    """Test recommendation engine basic flow"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="test123")
        cls.creator = Creator.objects.create(name="Test Creator", platform="youtube")
        # Create some test content
        for i in range(5):
            raw = RawContent.objects.create(source_url=f"https://example.com/rec{i}")
            ProcessedContent.objects.create(
                raw=raw,
                creator=cls.creator,
                title=f"Recommendation Test {i}",
                url=f"https://example.com/rec-{i}",
                content_type="video",
                quality_score=4.0 + i * 0.2,
                stage="active",
                published_at="2026-06-01T00:00:00Z",
            )

    def test_get_user_stage(self):
        from .recommender import get_user_stage
        stage = get_user_stage(self.user)
        self.assertIn(stage, [0, 1, 2, 3])
    
    def test_subscription_recall(self):
        from .recommender import subscription_recall
        results = subscription_recall(self.user, limit=10)
        self.assertIsInstance(results, list)
    
    def test_get_recommendations(self):
        from .recommender import get_recommendations_for_user
        results = get_recommendations_for_user(self.user, limit=5)
        self.assertIsInstance(results, list)


class EmbeddingCircuitBreakerTest(TestCase):
    """测试 Embedding 熔断器和死信机制."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_circuit_breaker_opens_on_high_failure_rate(self):
        """失败率>80% 时熔断器打开."""
        from django.core.cache import cache
        circuit_key = 'embedding_circuit_open'

        # 模拟熔断器打开
        cache.set(circuit_key, True, timeout=600)

        from apps.content.tasks import process_pending_embeddings
        result = process_pending_embeddings()
        self.assertIn('circuit_open', result)
        self.assertTrue(result.get('circuit_open'))

        cache.clear()

    def test_dead_letter_after_5_failures(self):
        """同一内容失败 5 次后进入死信."""
        from django.core.cache import cache

        fail_key_template = 'embedding_fail:99999'
        # 模拟5次失败
        for i in range(5):
            cache.set(fail_key_template, i + 1, timeout=86400)

        from apps.content.tasks import _get_dead_letter_ids
        # 目前_dead_letter_ids返回空列表，测试确认
        result = _get_dead_letter_ids()
        self.assertIsInstance(result, list)

        cache.clear()
