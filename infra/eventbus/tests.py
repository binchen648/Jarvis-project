from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Event
from .event_types import (
    GOAL_CREATED, GOAL_SESSION_CREATED,
    WELLNESS_RECORDED,
    CHAT_MESSAGE_SENT,
    CONTENT_BOOKMARKED,
    SKILL_NODE_COMPLETED,
)
from .emit import emit_event

User = get_user_model()


class EventModelTest(TestCase):
    """Event 模型创建与字段验证."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='eventuser', password='testpass123'
        )
        self.event = Event.objects.create(
            user=self.user,
            event_type='test.event',
            payload={'key': 'value'},
        )

    def test_event_creation(self):
        """创建事件应具有正确的字段值."""
        self.assertEqual(self.event.user, self.user)
        self.assertEqual(self.event.event_type, 'test.event')
        self.assertEqual(self.event.payload, {'key': 'value'})
        self.assertIsNotNone(self.event.created_at)

    def test_event_default_status(self):
        """status 默认为 pending."""
        self.assertEqual(self.event.status, 'pending')
        self.assertEqual(self.event.error_message, '')

    def test_event_user_nullable(self):
        """user 字段可为空."""
        event = Event.objects.create(event_type='system.event')
        self.assertIsNone(event.user)

    def test_event_all_statuses(self):
        """所有状态值均可设置."""
        for status_code, _ in Event.STATUS_CHOICES:
            event = Event.objects.create(
                event_type='status.test',
                status=status_code,
            )
            self.assertEqual(event.status, status_code)

    def test_event_str(self):
        """__str__ 返回 event_type(status) 格式."""
        expected = f"{self.event.event_type}({self.event.status})"
        self.assertEqual(str(self.event), expected)

    def test_event_processed_at(self):
        """processed_at 默认为 None，设置后有值."""
        self.assertIsNone(self.event.processed_at)
        from django.utils import timezone
        self.event.processed_at = timezone.now()
        self.event.save()
        self.event.refresh_from_db()
        self.assertIsNotNone(self.event.processed_at)

    def test_event_meta(self):
        """Meta 配置应正确."""
        self.assertEqual(Event._meta.db_table, 'eventbus_event')
        self.assertEqual(Event._meta.verbose_name, '事件')


class EventTypeValuesTest(TestCase):
    """事件类型常量值验证."""

    def test_event_type_strings(self):
        """事件类型常量应为带点号分隔的字符串."""
        self.assertEqual(GOAL_CREATED, 'goal.created')
        self.assertEqual(GOAL_SESSION_CREATED, 'goal_session.created')
        self.assertEqual(WELLNESS_RECORDED, 'wellness.recorded')
        self.assertEqual(CHAT_MESSAGE_SENT, 'chat.message_sent')
        self.assertEqual(CONTENT_BOOKMARKED, 'content.bookmarked')
        self.assertEqual(SKILL_NODE_COMPLETED, 'skill_node.completed')

    def test_events_can_be_created_with_type_constants(self):
        """使用类型常量创建 Event 应正常工作."""
        user = User.objects.create_user(
            username='etypeuser', password='testpass123'
        )
        event = Event.objects.create(
            user=user,
            event_type=GOAL_CREATED,
            payload={'goal_id': 1},
        )
        self.assertEqual(event.event_type, 'goal.created')
        self.assertEqual(event.payload, {'goal_id': 1})


class EmitEventTest(TestCase):
    """emit_event 函数测试."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='emitusr', password='testpass123'
        )

    def test_emit_event_creates_event(self):
        """emit_event 应创建一条 Event 记录."""
        emit_event('test.emit', user=self.user, payload={'msg': 'hello'})
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.first()
        self.assertEqual(event.event_type, 'test.emit')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.payload, {'msg': 'hello'})

    def test_emit_event_without_user(self):
        """emit_event 可不传 user."""
        emit_event('anonymous.event')
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.first()
        self.assertEqual(event.event_type, 'anonymous.event')
        self.assertIsNone(event.user)

    def test_emit_event_without_payload(self):
        """不传 payload 时默认为空字典."""
        emit_event('empty.payload.event', user=self.user)
        event = Event.objects.first()
        self.assertEqual(event.payload, {})

    def test_emit_event_uses_constant(self):
        """emit_event 可使用事件类型常量."""
        emit_event(GOAL_CREATED, user=self.user)
        event = Event.objects.first()
        self.assertEqual(event.event_type, 'goal.created')
