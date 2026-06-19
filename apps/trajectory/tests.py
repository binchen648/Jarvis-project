from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from .models import SkillNode, UserLearningProgress, LearningPath, PathNode

User = get_user_model()


class SkillNodeModelTest(TestCase):
    """Test SkillNode model creation and CRUD."""

    def setUp(self):
        self.node = SkillNode.objects.create(
            name='Python 基础',
            category='编程语言',
            difficulty=1,
            estimated_hours=20,
        )

    def test_create_skill_node(self):
        self.assertEqual(self.node.name, 'Python 基础')
        self.assertEqual(self.node.category, '编程语言')
        self.assertEqual(self.node.difficulty, 1)
        self.assertEqual(self.node.estimated_hours, 20)
        self.assertEqual(self.node.learner_count, 0)
        self.assertIsNone(self.node.avg_completion_rate)

    def test_str_representation(self):
        self.assertEqual(str(self.node), 'Python 基础')

    def test_prerequisites_m2m(self):
        advanced = SkillNode.objects.create(
            name='Python 高级',
            category='编程语言',
            difficulty=4,
            estimated_hours=40,
        )
        self.node.prerequisites.add(advanced)
        self.assertIn(advanced, self.node.prerequisites.all())

    def test_meta_db_table(self):
        self.assertEqual(SkillNode._meta.db_table, 'trajectory_skill_node')

    def test_unique_name(self):
        with self.assertRaises(Exception):
            SkillNode.objects.create(
                name='Python 基础',
                category='其它',
                difficulty=2,
                estimated_hours=10,
            )


class UserLearningProgressModelTest(TestCase):
    """Test UserLearningProgress model."""

    def setUp(self):
        self.user = User.objects.create_user(username='learner1', password='pass1234')
        self.skill = SkillNode.objects.create(
            name='Django',
            category='Web 框架',
            difficulty=3,
            estimated_hours=30,
        )

    def test_create_progress(self):
        progress = UserLearningProgress.objects.create(
            user=self.user,
            skill=self.skill,
            status='learning',
        )
        self.assertEqual(progress.status, 'learning')
        self.assertEqual(progress.user, self.user)
        self.assertEqual(progress.skill, self.skill)
        self.assertIsNone(progress.predicted_completion_days)

    def test_str_representation(self):
        progress = UserLearningProgress.objects.create(
            user=self.user,
            skill=self.skill,
            status='completed',
        )
        self.assertIn('learner1', str(progress))
        self.assertIn('Django', str(progress))
        self.assertIn('已完成', str(progress))

    def test_unique_together(self):
        UserLearningProgress.objects.create(user=self.user, skill=self.skill)
        with self.assertRaises(Exception):
            UserLearningProgress.objects.create(user=self.user, skill=self.skill)


class LearningPathModelTest(TestCase):
    """Test LearningPath model."""

    def setUp(self):
        self.user = User.objects.create_user(username='path_user', password='pass1234')

    def test_create_path(self):
        path = LearningPath.objects.create(
            user=self.user,
            title='Python 全栈工程师',
            goal_description='从零到全栈',
        )
        self.assertEqual(path.title, 'Python 全栈工程师')
        self.assertTrue(path.is_active)
        self.assertIsNotNone(path.created_at)

    def test_str_representation(self):
        path = LearningPath.objects.create(
            user=self.user,
            title='数据科学入门',
        )
        self.assertEqual(str(path), '数据科学入门')

    def test_default_is_active(self):
        path = LearningPath.objects.create(user=self.user, title='默认路径')
        self.assertTrue(path.is_active)


class PathNodeModelTest(TestCase):
    """Test PathNode model."""

    def setUp(self):
        self.user = User.objects.create_user(username='node_user', password='pass1234')
        self.skill = SkillNode.objects.create(
            name='Linux 基础',
            category='操作系统',
            difficulty=2,
            estimated_hours=15,
        )
        self.path = LearningPath.objects.create(
            user=self.user,
            title='后端工程师',
        )

    def test_create_path_node(self):
        node = PathNode.objects.create(
            path=self.path,
            skill=self.skill,
            order=1,
            estimated_minutes=120,
        )
        self.assertEqual(node.order, 1)
        self.assertEqual(node.status, 'pending')
        self.assertEqual(node.estimated_minutes, 120)

    def test_str_with_skill(self):
        node = PathNode.objects.create(
            path=self.path,
            skill=self.skill,
            order=1,
        )
        self.assertIn('后端工程师', str(node))
        self.assertIn('Linux', str(node))

    def test_str_without_skill(self):
        node = PathNode.objects.create(
            path=self.path,
            skill=None,
            order=2,
        )
        self.assertIn('(已删除)', str(node))

    def test_ordering(self):
        node1 = PathNode.objects.create(path=self.path, order=2)
        node2 = PathNode.objects.create(path=self.path, order=1)
        nodes = PathNode.objects.all()
        self.assertEqual(nodes[0], node2)
        self.assertEqual(nodes[1], node1)


class SkillGraphViewTest(TestCase):
    """Test skill_graph view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='graph_user', password='pass1234')
        SkillNode.objects.create(name='HTML', category='前端', difficulty=1, estimated_hours=5)
        SkillNode.objects.create(name='CSS', category='前端', difficulty=1, estimated_hours=5)
        SkillNode.objects.create(name='Python', category='后端', difficulty=2, estimated_hours=20)

    def test_redirect_unauthenticated(self):
        response = self.client.get(reverse('trajectory:skill_graph'))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('trajectory:skill_graph'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'trajectory/skill_graph.html')
        self.assertIn('skills_by_category', response.context)
        self.assertIn('user_progress_map', response.context)

    def test_skills_grouped_by_category(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('trajectory:skill_graph'))
        categories = response.context['skills_by_category']
        self.assertIn('前端', categories)
        self.assertIn('后端', categories)
        self.assertEqual(len(categories['前端']), 2)
        self.assertEqual(len(categories['后端']), 1)


class PathListViewTest(TestCase):
    """Test path_list view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='list_user', password='pass1234')
        self.other = User.objects.create_user(username='other_user', password='pass1234')
        LearningPath.objects.create(user=self.user, title='我的路径')
        LearningPath.objects.create(user=self.other, title='别人的路径')

    def test_redirect_unauthenticated(self):
        response = self.client.get(reverse('trajectory:path_list'))
        self.assertEqual(response.status_code, 302)

    def test_only_own_paths_shown(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('trajectory:path_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'trajectory/path_list.html')
        titles = [item['path'].title for item in response.context['path_progress']]
        self.assertIn('我的路径', titles)
        self.assertNotIn('别人的路径', titles)


class PathDetailViewTest(TestCase):
    """Test path_detail view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='detail_user', password='pass1234')
        self.path = LearningPath.objects.create(user=self.user, title='我的路径')

    def test_redirect_unauthenticated(self):
        response = self.client.get(reverse('trajectory:path_detail', args=[self.path.pk]))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('trajectory:path_detail', args=[self.path.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'trajectory/path_detail.html')
        self.assertEqual(response.context['path'], self.path)

    def test_other_user_forbidden(self):
        other = User.objects.create_user(username='other2', password='pass1234')
        self.client.force_login(other)
        response = self.client.get(reverse('trajectory:path_detail', args=[self.path.pk]))
        self.assertEqual(response.status_code, 404)

    def test_progress_computed(self):
        self.client.force_login(self.user)
        skill = SkillNode.objects.create(name='Test', category='T', difficulty=1, estimated_hours=1)
        PathNode.objects.create(path=self.path, skill=skill, order=1)
        response = self.client.get(reverse('trajectory:path_detail', args=[self.path.pk]))
        self.assertEqual(response.context['total'], 1)
        self.assertEqual(response.context['completed'], 0)
        self.assertEqual(response.context['progress_pct'], 0)


class CompleteNodeViewTest(TestCase):
    """Test complete_node view (POST only, human-centric)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='complete_user', password='pass1234')
        self.skill = SkillNode.objects.create(name='Git', category='工具', difficulty=1, estimated_hours=5)
        self.path = LearningPath.objects.create(user=self.user, title='工具链')
        self.node = PathNode.objects.create(path=self.path, skill=self.skill, order=1, status='in_progress')

    def test_redirect_unauthenticated(self):
        response = self.client.post(reverse('trajectory:complete_node', args=[self.node.pk]))
        self.assertEqual(response.status_code, 302)

    def test_get_method_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('trajectory:complete_node', args=[self.node.pk]))
        self.assertEqual(response.status_code, 405)

    def test_complete_node(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('trajectory:complete_node', args=[self.node.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'ok', 'node_id': self.node.pk})
        self.node.refresh_from_db()
        self.assertEqual(self.node.status, 'completed')

    def test_double_completion_returns_info(self):
        self.client.force_login(self.user)
        self.node.status = 'completed'
        self.node.save()
        response = self.client.post(reverse('trajectory:complete_node', args=[self.node.pk]))
        self.assertJSONEqual(response.content, {'status': 'already_completed'})

    def test_other_user_cannot_complete(self):
        other = User.objects.create_user(username='other3', password='pass1234')
        self.client.force_login(other)
        response = self.client.post(reverse('trajectory:complete_node', args=[self.node.pk]))
        self.assertEqual(response.status_code, 404)

    def test_complete_updates_user_learning_progress(self):
        self.client.force_login(self.user)
        self.client.post(reverse('trajectory:complete_node', args=[self.node.pk]))
        progress = UserLearningProgress.objects.get(user=self.user, skill=self.skill)
        self.assertEqual(progress.status, 'completed')


class CeleryTaskTest(TestCase):
    """Test Celery tasks."""

    def setUp(self):
        self.user = User.objects.create_user(username='celery_user', password='pass1234')
        self.skill = SkillNode.objects.create(
            name='Task Test Skill',
            category='测试',
            difficulty=2,
            estimated_hours=10,
        )
        self.path = LearningPath.objects.create(user=self.user, title='测试路径')

    def test_update_skill_stats_task(self):
        from .tasks import update_skill_stats
        # Create some progress records
        UserLearningProgress.objects.create(
            user=self.user, skill=self.skill, status='completed'
        )
        result = update_skill_stats()
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.learner_count, 1)
        self.assertEqual(self.skill.avg_completion_rate, 1.0)
        self.assertIn('updated', result)
        self.assertIn('total', result)

    def test_update_skill_stats_empty(self):
        from .tasks import update_skill_stats
        result = update_skill_stats()
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.learner_count, 0)
        self.assertIsNone(self.skill.avg_completion_rate)
        self.assertEqual(result['updated'], 1)

    def test_check_path_progress_task(self):
        from .tasks import check_path_progress
        node = PathNode.objects.create(
            path=self.path,
            skill=self.skill,
            order=1,
            status='pending',
        )
        result = check_path_progress()
        self.assertEqual(result['paths_checked'], 1)
        self.assertEqual(result['not_started'], 1)
        self.assertEqual(result['almost_complete'], 0)

    def test_check_path_progress_almost_done(self):
        from .tasks import check_path_progress
        PathNode.objects.create(path=self.path, skill=self.skill, order=1, status='completed')
        skill2 = SkillNode.objects.create(name='Node 2', category='测试', difficulty=1, estimated_hours=5)
        PathNode.objects.create(path=self.path, skill=skill2, order=2, status='in_progress')
        result = check_path_progress()
        self.assertEqual(result['paths_checked'], 1)
        self.assertEqual(result['almost_complete'], 1)
