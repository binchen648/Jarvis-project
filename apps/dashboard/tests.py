from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import DashboardLayout

User = get_user_model()


class DashboardLayoutModelTest(TestCase):
    """DashboardLayout 模型创建与字段验证."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='dashuser', password='testpass123'
        )
        self.layout = DashboardLayout.objects.create(user=self.user)

    def test_dashboard_layout_creation(self):
        """创建布局应关联正确的用户."""
        self.assertEqual(self.layout.user, self.user)
        self.assertIsNotNone(self.layout.created_at)
        self.assertIsNotNone(self.layout.updated_at)

    def test_default_layout_config(self):
        """layout_config 默认为空字典."""
        self.assertEqual(self.layout.layout_config, {})

    def test_layout_config_custom_value(self):
        """layout_config 可存储自定义配置."""
        config = {'widgets': ['stats', 'goals', 'wellness']}
        self.layout.layout_config = config
        self.layout.save()
        self.layout.refresh_from_db()
        self.assertEqual(self.layout.layout_config, config)

    def test_dashboard_layout_str(self):
        """__str__ 返回用户's dashboard 格式."""
        expected = f"{self.user}'s dashboard"
        self.assertEqual(str(self.layout), expected)

    def test_one_to_one_relationship(self):
        """每个用户只有一个 DashboardLayout."""
        with self.assertRaises(Exception):
            DashboardLayout.objects.create(user=self.user)

    def test_dashboard_layout_meta(self):
        """Meta 配置应正确."""
        self.assertEqual(DashboardLayout._meta.db_table, 'dashboard_layout')
        self.assertEqual(DashboardLayout._meta.verbose_name, 'Dashboard 布局')

    def test_created_at_auto_now_add(self):
        """created_at 在创建时自动赋值."""
        self.assertIsNotNone(self.layout.created_at)
