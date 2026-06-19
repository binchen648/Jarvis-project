from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Conversation, Message

User = get_user_model()


class ConversationModelTest(TestCase):
    """Conversation 模型创建与字段验证."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='chatuser', password='testpass123'
        )
        self.conversation = Conversation.objects.create(
            user=self.user,
            title='测试对话',
        )

    def test_conversation_creation(self):
        """创建对话应具有正确的字段值."""
        self.assertEqual(self.conversation.user, self.user)
        self.assertEqual(self.conversation.title, '测试对话')
        self.assertIsNotNone(self.conversation.created_at)
        self.assertIsNotNone(self.conversation.updated_at)

    def test_conversation_default_title_blank(self):
        """title 默认为空字符串."""
        conv = Conversation.objects.create(user=self.user)
        self.assertEqual(conv.title, '')

    def test_conversation_str(self):
        """__str__ 返回包含模型名和主键的字符串."""
        self.assertIn('Conversation', str(self.conversation))
        self.assertIn(str(self.conversation.pk), str(self.conversation))

    def test_conversation_ordering(self):
        """对话按 updated_at 降序排列."""
        older = Conversation.objects.create(user=self.user, title='旧对话')
        qs = Conversation.objects.all()
        self.assertEqual(qs[0], self.conversation)  # 最新在前
        self.assertEqual(qs[1], older)

    def test_conversation_meta(self):
        """Meta 配置应正确."""
        self.assertEqual(Conversation._meta.db_table, 'chat_conversation')
        self.assertEqual(Conversation._meta.verbose_name, '对话')
        self.assertEqual(Conversation._meta.ordering, ['-updated_at'])


class MessageModelTest(TestCase):
    """Message 模型创建与字段验证."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='msgsuser', password='testpass123'
        )
        self.conversation = Conversation.objects.create(
            user=self.user, title='消息测试'
        )
        self.message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='你好，今天天气怎么样？',
            tokens_used=10,
        )

    def test_message_creation(self):
        """创建消息应具有正确的字段值."""
        self.assertEqual(self.message.conversation, self.conversation)
        self.assertEqual(self.message.role, 'user')
        self.assertEqual(self.message.content, '你好，今天天气怎么样？')
        self.assertEqual(self.message.tokens_used, 10)
        self.assertIsNotNone(self.message.created_at)

    def test_message_tokens_used_nullable(self):
        """tokens_used 默认为 None."""
        msg = Message.objects.create(
            conversation=self.conversation,
            role='system',
            content='系统消息',
        )
        self.assertIsNone(msg.tokens_used)

    def test_message_str(self):
        """__str__ 返回包含模型名和主键的字符串."""
        self.assertIn('Message', str(self.message))
        self.assertIn(str(self.message.pk), str(self.message))

    def test_message_all_roles(self):
        """所有角色均可创建."""
        for role_code, _ in Message.ROLE_CHOICES:
            msg = Message.objects.create(
                conversation=self.conversation,
                role=role_code,
                content=f'{role_code} 消息',
            )
            self.assertEqual(msg.role, role_code)

    def test_message_ordering(self):
        """消息按 created_at 升序排列."""
        msg2 = Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='今天天气不错。',
        )
        qs = Message.objects.all()
        self.assertEqual(qs[0], self.message)  # 先创建的在前面
        self.assertEqual(qs[1], msg2)


class ConversationMessageRelationTest(TestCase):
    """Conversation ↔ Message 关系测试."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='reluser', password='testpass123'
        )
        self.conversation = Conversation.objects.create(
            user=self.user, title='关系测试'
        )

    def test_create_messages_via_related_name(self):
        """通过 related_name 创建消息."""
        self.conversation.messages.create(
            role='user', content='用户消息'
        )
        self.conversation.messages.create(
            role='assistant', content='AI 回复'
        )
        self.assertEqual(self.conversation.messages.count(), 2)

    def test_cascade_delete(self):
        """删除对话时关联消息也被删除."""
        self.conversation.messages.create(
            role='user', content='将被删除'
        )
        pk = self.conversation.pk
        self.conversation.delete()
        self.assertEqual(Message.objects.filter(conversation_id=pk).count(), 0)
