from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import LLMCallLog, UserPersona, MemoryEntry

User = get_user_model()


class LLMCallLogModelTest(TestCase):
    """LLMCallLog 模型创建与字段验证."""

    def setUp(self):
        self.log = LLMCallLog.objects.create(
            model_name='deepseek-chat',
            prompt_tokens=150,
            completion_tokens=300,
            total_tokens=450,
            cost=0.009,
            duration_ms=1200,
            success=True,
        )

    def test_call_log_creation(self):
        """创建调用日志应具有正确的字段值."""
        self.assertEqual(self.log.model_name, 'deepseek-chat')
        self.assertEqual(self.log.prompt_tokens, 150)
        self.assertEqual(self.log.completion_tokens, 300)
        self.assertEqual(self.log.total_tokens, 450)
        self.assertEqual(self.log.cost, 0.009)
        self.assertEqual(self.log.duration_ms, 1200)
        self.assertTrue(self.log.success)
        self.assertIsNotNone(self.log.created_at)

    def test_call_log_defaults(self):
        """字段默认值应正确."""
        log = LLMCallLog.objects.create(model_name='gpt-4')
        self.assertEqual(log.prompt_tokens, 0)
        self.assertEqual(log.completion_tokens, 0)
        self.assertEqual(log.total_tokens, 0)
        self.assertEqual(log.cost, 0.0)
        self.assertEqual(log.duration_ms, 0)
        self.assertTrue(log.success)
        self.assertEqual(log.error_message, '')

    def test_call_log_failed_call(self):
        """失败调用应记录错误信息."""
        log = LLMCallLog.objects.create(
            model_name='deepseek-chat',
            success=False,
            error_message='API timeout',
        )
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, 'API timeout')

    def test_call_log_str(self):
        """__str__ 返回模型名和 token 数."""
        expected = f"{self.log.model_name} - {self.log.total_tokens}tokens"
        self.assertEqual(str(self.log), expected)

    def test_call_log_ordering(self):
        """日志按 created_at 降序排列."""
        log2 = LLMCallLog.objects.create(model_name='gpt-4')
        qs = LLMCallLog.objects.all()
        self.assertEqual(qs[0], log2)  # 后创建的在前
        self.assertEqual(qs[1], self.log)

    def test_call_log_meta(self):
        """Meta 配置应正确."""
        self.assertEqual(LLMCallLog._meta.db_table, 'llm_call_log')
        self.assertEqual(LLMCallLog._meta.verbose_name, 'LLM 调用日志')


class UserPersonaModelTest(TestCase):
    """UserPersona 模型创建与字段验证."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='personauser', password='testpass123'
        )
        self.persona = UserPersona.objects.create(
            user=self.user,
            persona_summary='热爱编程的大学生，擅长 Python 和 Django',
            facts=[{'key': '学校', 'value': '清华大学'}],
            interests=[{'tag': 'Python', 'weight': 9.0}],
            version=1,
        )

    def test_persona_creation(self):
        """创建画像应具有正确的字段值."""
        self.assertEqual(self.persona.user, self.user)
        self.assertEqual(self.persona.persona_summary, '热爱编程的大学生，擅长 Python 和 Django')
        self.assertEqual(self.persona.facts, [{'key': '学校', 'value': '清华大学'}])
        self.assertEqual(self.persona.interests, [{'tag': 'Python', 'weight': 9.0}])
        self.assertEqual(self.persona.version, 1)
        self.assertIsNotNone(self.persona.created_at)

    def test_persona_defaults(self):
        """字段默认值应正确."""
        persona = UserPersona.objects.create(user=self.user)
        self.assertEqual(persona.persona_summary, '')
        self.assertEqual(persona.facts, [])
        self.assertEqual(persona.interests, [])
        self.assertEqual(persona.version, 0)
        self.assertIsNone(persona.last_built_at)

    def test_persona_one_to_one(self):
        """每个用户只有一个 UserPersona."""
        UserPersona.objects.create(user=self.user)
        with self.assertRaises(Exception):
            UserPersona.objects.create(user=self.user)

    def test_persona_str(self):
        """__str__ 返回用户's persona (v版本) 格式."""
        expected = f"{self.user}'s persona (v{self.persona.version})"
        self.assertEqual(str(self.persona), expected)

    def test_persona_meta(self):
        """Meta 配置应正确."""
        self.assertEqual(UserPersona._meta.db_table, 'llm_user_persona')
        self.assertEqual(UserPersona._meta.verbose_name, '用户画像')


class MemoryEntryModelTest(TestCase):
    """MemoryEntry 模型创建与字段验证."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='memuser', password='testpass123'
        )

    def test_create_l1_memory(self):
        """创建 L1 (Core Profile) 记忆条目."""
        entry = MemoryEntry.objects.create(
            user=self.user,
            level=1,
            memory_type='persona_summary',
            content='用户核心画像摘要',
            weight=10.0,
        )
        self.assertEqual(entry.level, 1)
        self.assertEqual(entry.memory_type, 'persona_summary')
        self.assertEqual(entry.content, '用户核心画像摘要')
        self.assertEqual(entry.weight, 10.0)
        self.assertTrue(entry.is_active)
        self.assertEqual(entry.access_count, 0)
        self.assertEqual(entry.metadata, {})

    def test_create_l2_memory(self):
        """创建 L2 (Context) 记忆条目."""
        entry = MemoryEntry.objects.create(
            user=self.user,
            level=2,
            memory_type='conversation',
            content='最近的对话上下文',
            metadata={'session_id': 'abc123'},
        )
        self.assertEqual(entry.level, 2)
        self.assertEqual(entry.memory_type, 'conversation')
        self.assertEqual(entry.metadata, {'session_id': 'abc123'})

    def test_create_l3_memory(self):
        """创建 L3 (Detail) 记忆条目."""
        entry = MemoryEntry.objects.create(
            user=self.user,
            level=3,
            memory_type='skill_progress',
            content='Python 基础学习完成度 80%',
            expires_at='2026-12-31 23:59:59+00:00',
        )
        self.assertEqual(entry.level, 3)
        self.assertEqual(entry.memory_type, 'skill_progress')
        self.assertIsNotNone(entry.expires_at)

    def test_memory_entry_defaults(self):
        """字段默认值应正确."""
        entry = MemoryEntry.objects.create(
            user=self.user,
            level=1,
            memory_type='user_fact',
            content='测试默认值',
        )
        self.assertEqual(entry.weight, 1.0)
        self.assertTrue(entry.is_active)
        self.assertEqual(entry.access_count, 0)
        self.assertEqual(entry.metadata, {})
        self.assertIsNone(entry.expires_at)

    def test_memory_entry_str(self):
        """__str__ 返回 user-Llevel/type 格式."""
        entry = MemoryEntry.objects.create(
            user=self.user,
            level=2,
            memory_type='goal',
            content='学习 Django 目标',
        )
        expected = f"{self.user}-L{entry.level}/{entry.memory_type}"
        self.assertEqual(str(entry), expected)

    def test_memory_entry_ordering(self):
        """记忆条目按 weight 降序、created_at 降序排列."""
        e1 = MemoryEntry.objects.create(
            user=self.user, level=1, memory_type='persona_summary',
            content='高权重', weight=5.0,
        )
        e2 = MemoryEntry.objects.create(
            user=self.user, level=1, memory_type='user_fact',
            content='更高权重', weight=10.0,
        )
        qs = MemoryEntry.objects.all()
        self.assertEqual(qs[0], e2)  # 权重更高的在前
        self.assertEqual(qs[1], e1)

    def test_memory_entry_meta(self):
        """Meta 配置应正确."""
        self.assertEqual(MemoryEntry._meta.db_table, 'llm_memory_entry')
        self.assertEqual(MemoryEntry._meta.verbose_name, '记忆条目')
