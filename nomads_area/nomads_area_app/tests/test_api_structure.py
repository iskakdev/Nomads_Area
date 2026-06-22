from unittest.mock import patch
from django.test import SimpleTestCase
from ..throttles import FormSubmitThrottle
from ..notifications import enqueue_task_safely


class FormSubmitThrottleTests(SimpleTestCase):
    """Проверка конфигурации троттлинга"""
    def test_rate_comes_from_drf_settings(self):
        with patch.dict(FormSubmitThrottle.THROTTLE_RATES, {"forms": "17/minute"}):
            self.assertEqual(FormSubmitThrottle().get_rate(), "17/minute")


class NotificationSafetyTests(SimpleTestCase):
    """Проверка отказоустойчивости системы уведомлений"""
    def test_enqueue_failure_is_swallowed(self):
        # Имитируем падение очереди Celery/Redis
        task = type("Task", (), {"name": "broken", "delay": lambda self, *args: (_ for _ in ()).throw(ConnectionError("down"))})()
        
        with self.assertLogs("nomads_area_app.notifications", level="ERROR"):
            result = enqueue_task_safely(task, "payload")
        self.assertIsNone(result)