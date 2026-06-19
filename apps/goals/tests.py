from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Goal, GoalSession

User = get_user_model()


# ── Model field creation tests ──────────────────────────────────────────────


class GoalModelTest(TestCase):
    """Test Goal model field creation and defaults."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.goal = Goal.objects.create(
            user=self.user,
            title='测试目标',
            description='这是一个测试目标',
            goal_type='reading',
            target_value=10.0,
            target_unit='篇',
            category='weekly',
            is_recurring=True,
        )

    def test_goal_creation(self):
        """新创建的目标应有正确的字段值。"""
        self.assertEqual(self.goal.title, '测试目标')
        self.assertEqual(self.goal.description, '这是一个测试目标')
        self.assertEqual(self.goal.status, 'active')  # default
        self.assertEqual(self.goal.goal_type, 'reading')
        self.assertEqual(self.goal.target_value, 10.0)
        self.assertEqual(self.goal.target_unit, '篇')
        self.assertEqual(self.goal.category, 'weekly')
        self.assertTrue(self.goal.is_recurring)

    def test_goal_str(self):
        """__str__ 应返回标题。"""
        self.assertEqual(str(self.goal), '测试目标')

    def test_goal_defaults(self):
        """默认值应正确设置。"""
        goal2 = Goal.objects.create(user=self.user, title='默认目标')
        self.assertEqual(goal2.goal_type, 'custom')
        self.assertIsNone(goal2.target_value)
        self.assertEqual(goal2.target_unit, '')
        self.assertEqual(goal2.category, 'daily')
        self.assertFalse(goal2.is_recurring)

    def test_goal_meta(self):
        """Meta 配置应正确。"""
        self.assertEqual(Goal._meta.db_table, 'goals_goal')
        self.assertEqual(Goal._meta.verbose_name, '学习目标')
        self.assertEqual(Goal._meta.verbose_name_plural, '学习目标')

    def test_goal_existing_fields_preserved(self):
        """原有字段应保持不变。"""
        self.assertTrue(hasattr(self.goal, 'title'))
        self.assertTrue(hasattr(self.goal, 'description'))
        self.assertTrue(hasattr(self.goal, 'status'))
        self.assertTrue(hasattr(self.goal, 'deadline'))
        self.assertTrue(hasattr(self.goal, 'created_at'))
        self.assertTrue(hasattr(self.goal, 'updated_at'))
        self.assertTrue(hasattr(self.goal, 'user'))


class GoalSessionModelTest(TestCase):
    """Test GoalSession model creation (with nullable goal)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='sessionuser', password='testpass123'
        )
        self.goal = Goal.objects.create(user=self.user, title='关联目标')

    def test_session_with_goal(self):
        """创建关联目标的 session。"""
        session = GoalSession.objects.create(
            user=self.user,
            goal=self.goal,
            duration_minutes=45,
            note='学习 Django',
        )
        self.assertEqual(session.duration_minutes, 45)
        self.assertEqual(session.goal, self.goal)
        self.assertIsNotNone(session.date)  # auto_now_add

    def test_session_without_goal(self):
        """创建不关联目标的 session（可空）。"""
        session = GoalSession.objects.create(
            user=self.user,
            duration_minutes=30,
            note='自由学习',
        )
        self.assertEqual(session.duration_minutes, 30)
        self.assertIsNone(session.goal)
        self.assertIsNotNone(session.date)

    def test_session_str_with_goal(self):
        """__str__ 应包含目标标题。"""
        session = GoalSession.objects.create(
            user=self.user,
            goal=self.goal,
            duration_minutes=60,
        )
        self.assertIn('关联目标', str(session))
        self.assertIn('60分钟', str(session))

    def test_session_str_without_goal(self):
        """__str__ 应为无关联目标。"""
        session = GoalSession.objects.create(
            user=self.user,
            duration_minutes=25,
        )
        self.assertIn('无关联目标', str(session))

    def test_session_meta(self):
        """Meta 配置应正确。"""
        self.assertEqual(GoalSession._meta.db_table, 'goals_session')
        self.assertEqual(GoalSession._meta.verbose_name, '学习记录')
        self.assertEqual(GoalSession._meta.verbose_name_plural, '学习记录')
        self.assertEqual(GoalSession._meta.ordering, ['-date'])


# ── View GET 200 tests ─────────────────────────────────────────────────────


class GoalViewsTest(TestCase):
    """Test all goal views return 200 for authenticated users."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='viewuser', password='testpass123'
        )
        self.goal = Goal.objects.create(user=self.user, title='视图测试目标')
        self.client.login(username='viewuser', password='testpass123')

    def test_goal_list_get(self):
        url = reverse('goals:goal_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_goal_create_get(self):
        url = reverse('goals:goal_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_goal_detail_get(self):
        url = reverse('goals:goal_detail', kwargs={'pk': self.goal.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_goal_edit_get(self):
        url = reverse('goals:goal_edit', kwargs={'pk': self.goal.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_log_session_get(self):
        url = reverse('goals:log_session')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


# ── View POST create tests ─────────────────────────────────────────────────


class GoalCreatePostTest(TestCase):
    """Test POST creates objects."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='createuser', password='testpass123'
        )
        self.client.login(username='createuser', password='testpass123')

    def test_goal_create_post(self):
        url = reverse('goals:goal_create')
        response = self.client.post(url, {
            'title': 'POST 创建的目标',
            'goal_type': 'coding',
            'target_value': 5,
            'target_unit': '个项目',
            'category': 'monthly',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Goal.objects.filter(title='POST 创建的目标').exists())

    def test_log_session_post(self):
        url = reverse('goals:log_session')
        response = self.client.post(url, {
            'duration_minutes': 50,
            'note': '测试学习记录',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GoalSession.objects.filter(note='测试学习记录').exists())

    def test_update_status_post(self):
        goal = Goal.objects.create(user=self.user, title='状态测试')
        url = reverse('goals:update_status', kwargs={'pk': goal.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'completed')  # active → completed


# ── Celery task invocation tests ──────────────────────────────────────────


class CeleryTaskTest(TestCase):
    """Test Celery tasks can be called and return expected output."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='taskuser', password='testpass123'
        )

    def test_check_goal_deadlines_runs(self):
        """check_goal_deadlines 应能执行且不抛异常。"""
        from .tasks import check_goal_deadlines
        result = check_goal_deadlines()
        self.assertIsNotNone(result)
        self.assertIn('Checked', result)

    def test_aggregate_daily_sessions_runs(self):
        """aggregate_daily_sessions 应能执行且不抛异常。"""
        from .tasks import aggregate_daily_sessions
        result = aggregate_daily_sessions()
        self.assertIsNotNone(result)
        self.assertIn('Aggregated', result)


# ── Unauthenticated access redirect tests ──────────────────────────────────


class UnauthenticatedAccessTest(TestCase):
    """Test unauthenticated users are redirected to login."""

    def setUp(self):
        self.client = Client()

    def _assert_redirect(self, url_name, *args, **kwargs):
        url = reverse(url_name, *args, **kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_goal_list_redirect(self):
        self._assert_redirect('goals:goal_list')

    def test_goal_create_redirect(self):
        self._assert_redirect('goals:goal_create')

    def test_goal_detail_redirect(self):
        user = User.objects.create_user(username='anon', password='testpass123')
        goal = Goal.objects.create(user=user, title='匿名目标')
        self._assert_redirect('goals:goal_detail', kwargs={'pk': goal.pk})

    def test_goal_edit_redirect(self):
        user = User.objects.create_user(username='anon2', password='testpass123')
        goal = Goal.objects.create(user=user, title='匿名目标2')
        self._assert_redirect('goals:goal_edit', kwargs={'pk': goal.pk})

    def test_log_session_redirect(self):
        self._assert_redirect('goals:log_session')
