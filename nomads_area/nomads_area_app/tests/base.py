from unittest.mock import patch
from rest_framework.test import APITestCase

LANG = "ru"
API = f"/api/{LANG}"


class BaseNoSpamTestCase(APITestCase):
    def setUp(self):
        super().setUp()

        # Отключаем троттлинг для тестов
        self.patcher_throttle = patch(
            "nomads_area_app.throttles.FormSubmitThrottle.allow_request",
            return_value=True,
        )
        # Патчим отправку уведомлений (Telegram и Email)
        self.patcher_tg = patch("nomads_area_app.tasks.send_telegram_task.delay")
        self.patcher_email = patch("nomads_area_app.tasks.send_email_task.delay")
        # Заставляем transaction.on_commit выполняться немедленно в тестах
        self.patcher_on_commit = patch(
            "django.db.transaction.on_commit",
            side_effect=lambda fn: fn(),
        )

        self.mock_allow = self.patcher_throttle.start()
        self.mock_tg = self.patcher_tg.start()
        self.mock_email = self.patcher_email.start()
        self.mock_on_commit = self.patcher_on_commit.start()

    def tearDown(self):
        self.patcher_on_commit.stop()
        self.patcher_email.stop()
        self.patcher_tg.stop()
        self.patcher_throttle.stop()
        super().tearDown()