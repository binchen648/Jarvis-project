from datetime import timedelta, datetime as dt
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from .models import HealthSuggestion, WellnessRecord

User = get_user_model()


class HealthSuggestionModelTest(TestCase):
    """HealthSuggestion 模型创建与字段验证."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_create_suggestion(self):
        """创建一条完整的健康建议."""
        suggestion = HealthSuggestion.objects.create(
            user=self.user,
            suggestion_type='break',
            content='测试建议内容',
            trigger_reason='测试触发原因',
        )
        self.assertEqual(suggestion.user, self.user)
        self.assertEqual(suggestion.suggestion_type, 'break')
        self.assertEqual(suggestion.content, '测试建议内容')
        self.assertEqual(suggestion.trigger_reason, '测试触发原因')
        self.assertFalse(suggestion.is_read)
        self.assertIsNotNone(suggestion.created_at)

    def test_suggestion_str(self):
        """__str__ 返回可读字符串."""
        suggestion = HealthSuggestion.objects.create(
            user=self.user,
            suggestion_type='eye',
            content='测试',
            trigger_reason='测试',
        )
        self.assertIn('护眼', str(suggestion))
        self.assertIn(self.user.username, str(suggestion))

    def test_default_is_read_false(self):
        """新创建的建议 is_read 默认为 False."""
        suggestion = HealthSuggestion.objects.create(
            user=self.user,
            suggestion_type='sleep',
            content='测试',
            trigger_reason='测试',
        )
        self.assertFalse(suggestion.is_read)

    def test_suggestion_types_all_valid(self):
        """所有建议类型均可创建."""
        for stype, _ in HealthSuggestion.SUGGESTION_TYPES:
            suggestion = HealthSuggestion.objects.create(
                user=self.user,
                suggestion_type=stype,
                content=f'{stype} 建议',
                trigger_reason=f'{stype} 触发',
            )
            self.assertEqual(suggestion.suggestion_type, stype)

    def test_ordering_newest_first(self):
        """建议按 created_at 降序排列."""
        from django.utils import timezone
        from datetime import timedelta

        s1 = HealthSuggestion.objects.create(
            user=self.user, suggestion_type='break',
            content='旧', trigger_reason='测试',
        )
        s2 = HealthSuggestion.objects.create(
            user=self.user, suggestion_type='sleep',
            content='新', trigger_reason='测试',
        )
        # auto_now_add overrides explicit values, so backdate via update
        earlier = timezone.now() - timedelta(hours=1)
        HealthSuggestion.objects.filter(pk=s1.pk).update(created_at=earlier)

        qs = HealthSuggestion.objects.all()
        self.assertEqual(qs[0], s2)
        self.assertEqual(qs[1], s1)

    def test_db_table(self):
        """自定义 db_table 生效."""
        self.assertEqual(
            HealthSuggestion._meta.db_table, 'wellness_suggestion'
        )


class SuggestionListViewTest(TestCase):
    """suggestion_list 视图测试."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.url = reverse('wellness:suggestion_list')

    def test_login_required(self):
        """未认证用户重定向到登录页."""
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f'/accounts/login/?next={self.url}'
        )

    def test_list_empty(self):
        """登录用户无未读建议时显示空状态."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wellness/suggestion_list.html')
        self.assertContains(response, '暂无健康建议')

    def test_list_unread_suggestions(self):
        """列表只显示当前用户的未读建议."""
        self.client.login(username='testuser', password='testpass123')
        other_user = User.objects.create_user(
            username='other', password='testpass123'
        )
        # 创建 3 条当前用户的未读建议
        for i in range(3):
            HealthSuggestion.objects.create(
                user=self.user, suggestion_type='break',
                content=f'建议{i}', trigger_reason='测试',
            )
        # 创建其他用户的建议
        HealthSuggestion.objects.create(
            user=other_user, suggestion_type='sleep',
            content='其他用户建议', trigger_reason='测试',
        )
        # 创建已读建议
        HealthSuggestion.objects.create(
            user=self.user, suggestion_type='eye',
            content='已读建议', trigger_reason='测试',
            is_read=True,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # 只应看到 3 条未读建议
        suggestions = response.context['suggestions']
        self.assertEqual(suggestions.count(), 3)
        for s in suggestions:
            self.assertEqual(s.user, self.user)
            self.assertFalse(s.is_read)


class DismissSuggestionViewTest(TestCase):
    """dismiss_suggestion 视图测试."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.suggestion = HealthSuggestion.objects.create(
            user=self.user, suggestion_type='posture',
            content='调整坐姿', trigger_reason='测试',
        )
        self.url = reverse(
            'wellness:dismiss_suggestion', args=[self.suggestion.pk]
        )

    def test_login_required(self):
        """未认证用户重定向."""
        response = self.client.post(self.url)
        self.assertRedirects(
            response, f'/accounts/login/?next={self.url}'
        )

    def test_dismiss_suggestion(self):
        """POST 标记建议为已读."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.suggestion.refresh_from_db()
        self.assertTrue(self.suggestion.is_read)

    def test_require_post(self):
        """GET 请求返回 405."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_dismiss_other_user_suggestion(self):
        """不能操作其他用户的建议."""
        other_user = User.objects.create_user(
            username='other', password='testpass123'
        )
        other_suggestion = HealthSuggestion.objects.create(
            user=other_user, suggestion_type='exercise',
            content='运动', trigger_reason='测试',
        )
        self.client.login(username='testuser', password='testpass123')
        url = reverse(
            'wellness:dismiss_suggestion', args=[other_suggestion.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class RecordCreateViewTest(TestCase):
    """record_create 视图测试."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.url = reverse('wellness:record_create')

    def test_login_required(self):
        """未认证用户重定向."""
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f'/accounts/login/?next={self.url}'
        )

    def test_get_form(self):
        """GET 返回表单页面."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wellness/record_form.html')

    def test_post_valid_record(self):
        """POST 有效数据创建健康记录."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url, {
            'mood_score': 4,
            'sleep_hours': 7.5,
            'exercise_minutes': 30,
            'note': '今天状态不错',
        })
        self.assertRedirects(response, self.url)
        self.assertEqual(WellnessRecord.objects.count(), 1)
        record = WellnessRecord.objects.first()
        self.assertEqual(record.user, self.user)
        self.assertEqual(record.mood_score, 4)
        self.assertEqual(record.sleep_hours, 7.5)
        self.assertEqual(record.exercise_minutes, 30)
        self.assertEqual(record.note, '今天状态不错')

    def test_post_minimal_record(self):
        """只提交必填字段 (mood_score)."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url, {
            'mood_score': 3,
        })
        self.assertRedirects(response, self.url)
        self.assertEqual(WellnessRecord.objects.count(), 1)
        record = WellnessRecord.objects.first()
        self.assertEqual(record.mood_score, 3)
        self.assertIsNone(record.sleep_hours)
        self.assertIsNone(record.exercise_minutes)
        self.assertEqual(record.note, '')


class GenerateHealthSuggestionsTaskTest(TestCase):
    """Celery 定时任务测试."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def _make_aware(self, year, month, day, hour, minute=0):
        """Helper to create a timezone-aware datetime."""
        return timezone.make_aware(dt(year, month, day, hour, minute))

    # ── Sleep suggestion via helper ──────────────────────────

    def test_sleep_suggestion_generated_after_22(self):
        """22:00 之后为活跃用户生成睡眠建议."""
        now = self._make_aware(2026, 6, 11, 23, 0)
        from .tasks import _generate_sleep_suggestion
        _generate_sleep_suggestion(self.user, now)
        self.assertTrue(
            HealthSuggestion.objects.filter(
                user=self.user, suggestion_type='sleep'
            ).exists()
        )

    def test_no_sleep_suggestion_before_22(self):
        """22:00 之前不生成睡眠建议."""
        now = self._make_aware(2026, 6, 11, 20, 0)
        from .tasks import _generate_sleep_suggestion
        _generate_sleep_suggestion(self.user, now)
        self.assertFalse(
            HealthSuggestion.objects.filter(
                user=self.user, suggestion_type='sleep'
            ).exists()
        )

    def test_no_duplicate_sleep_suggestion_same_day(self):
        """同一天不重复生成睡眠建议."""
        # Pre-create a sleep suggestion for today
        today = self._make_aware(2026, 6, 11, 22, 30)
        HealthSuggestion.objects.create(
            user=self.user, suggestion_type='sleep',
            content='早点休息', trigger_reason='已触发',
            created_at=today,
        )
        from .tasks import _generate_sleep_suggestion
        # Try to generate again at 23:00
        later = self._make_aware(2026, 6, 11, 23, 0)
        _generate_sleep_suggestion(self.user, later)
        self.assertEqual(
            HealthSuggestion.objects.filter(
                user=self.user, suggestion_type='sleep'
            ).count(), 1
        )

    # ── Full task integration ────────────────────────────────

    def test_task_runs_without_exception(self):
        """定时任务主入口不抛出异常."""
        from .tasks import generate_health_suggestions
        with patch('apps.wellness.tasks.timezone') as mock_tz:
            mock_tz.now.return_value = self._make_aware(2026, 6, 11, 15, 0)
            mock_tz.timedelta = timedelta
            result = generate_health_suggestions()
        self.assertIn('break_suggestions', result)
        self.assertIn('sleep_suggestions', result)
        self.assertIn('errors', result)

    def test_break_suggestion_skipped_when_goal_session_missing(self):
        """当 GoalSession 未实现时，break 建议被跳过且不报错."""
        from .tasks import generate_health_suggestions
        with patch('apps.wellness.tasks.timezone') as mock_tz:
            mock_tz.now.return_value = self._make_aware(2026, 6, 11, 15, 0)
            mock_tz.timedelta = timedelta
            result = generate_health_suggestions()
        self.assertEqual(result['break_suggestions'], 0)

    def test_sleep_generated_in_task_after_22(self):
        """完整任务在 22:00 后生成睡眠建议."""
        from .tasks import generate_health_suggestions
        with patch('apps.wellness.tasks.timezone') as mock_tz:
            mock_tz.now.return_value = self._make_aware(2026, 6, 11, 22, 0)
            mock_tz.timedelta = timedelta
            result = generate_health_suggestions()
        self.assertEqual(result['sleep_suggestions'], 1)
        self.assertTrue(
            HealthSuggestion.objects.filter(
                user=self.user, suggestion_type='sleep'
            ).exists()
        )


class WellnessRecordModelTest(TestCase):
    """确认现有 WellnessRecord 模型未被修改."""

    def test_wellness_record_preserved(self):
        """WellnessRecord 模型仍然可用."""
        user = User.objects.create_user(
            username='recorduser', password='testpass123'
        )
        record = WellnessRecord.objects.create(
            user=user, mood_score=5
        )
        self.assertEqual(record.mood_score, 5)
        self.assertIsNotNone(record.record_date)
        self.assertEqual(
            WellnessRecord._meta.db_table, 'wellness_record'
        )
