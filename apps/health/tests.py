from django.test import TestCase, Client


class HealthCheckTest(TestCase):
    """健康检查端点测试."""

    def setUp(self):
        self.client = Client()

    def test_health_check_returns_200(self):
        """GET /health/ 返回 200."""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)

    def test_health_check_json_structure(self):
        """响应包含 status/database/redis 字段."""
        response = self.client.get('/health/')
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('database', data)
        self.assertIn('redis', data)

    def test_health_check_unauthenticated(self):
        """健康检查不需要登录."""
        response = self.client.get('/health/')
        self.assertNotEqual(response.status_code, 302)  # 不是重定向到登录
