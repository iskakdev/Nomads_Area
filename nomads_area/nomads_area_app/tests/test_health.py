from rest_framework import status
from rest_framework.test import APITestCase


class HealthEndpointTests(APITestCase):
    """Тесты эндпоинтов мониторинга (health checks)"""

    def test_healthz_returns_ok(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")

    def test_readyz_checks_dependencies(self):
        response = self.client.get("/readyz/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        # Проверяем наличие детальных проверок БД и кэша
        self.assertTrue(response.data["checks"]["database"])
        self.assertTrue(response.data["checks"]["cache"])