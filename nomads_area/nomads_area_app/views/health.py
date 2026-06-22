from django.core.cache import cache
from django.db import connection
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class HealthCheckView(views.APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class ReadinessCheckView(views.APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        checks = {
            "database": False,
            "cache": False,
        }

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks["database"] = True
        except Exception:
            checks["database"] = False

        try:
            cache_key = "readyz"
            cache.set(cache_key, "ok", 10)
            checks["cache"] = cache.get(cache_key) == "ok"
        except Exception:
            checks["cache"] = False

        is_ready = all(checks.values())
        return Response(
            {"status": "ok" if is_ready else "degraded", "checks": checks},
            status=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
