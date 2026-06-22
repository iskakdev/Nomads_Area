from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import QuizProgress, QuizQuestion
from ..notifications import send_quiz_notification
from ..serializers import (
    QuizLeadSerializer,
    QuizProgressSerializer,
    QuizProgressUpdateSerializer,
    QuizQuestionSerializer,
)
from ..services import update_quiz_progress_service
from ..throttles import FormSubmitThrottle
from .common import cache_public_api


@cache_public_api
class QuizQuestionListView(generics.ListAPIView):
    queryset = QuizQuestion.objects.filter(is_active=True).prefetch_related("options")
    serializer_class = QuizQuestionSerializer
    permission_classes = [AllowAny]


class QuizProgressStartView(generics.CreateAPIView):
    serializer_class = QuizProgressSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        if not request.session.session_key:
            request.session.save()
        progress, created = QuizProgress.objects.get_or_create(
            session_key=request.session.session_key,
            defaults={"answers_data": {}, "current_question_index": 0},
        )
        if not created and progress.is_completed:
            progress.answers_data = {}
            progress.current_question_index = 0
            progress.is_completed = False
            progress.save(update_fields=["answers_data", "current_question_index", "is_completed"])
        return Response(self.get_serializer(progress).data, status=status.HTTP_200_OK)


class QuizProgressUpdateView(generics.UpdateAPIView):
    serializer_class = QuizProgressUpdateSerializer
    permission_classes = [AllowAny]
    lookup_field = "session_key"

    def get_object(self):
        key = self.kwargs.get(self.lookup_field) or self.request.session.session_key
        return generics.get_object_or_404(QuizProgress, session_key=key)

    def update(self, request, *args, **kwargs):
        progress = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        progress = update_quiz_progress_service(progress, serializer.validated_data)
        return Response(QuizProgressSerializer(progress).data, status=status.HTTP_200_OK)


class QuizLeadCreateView(generics.CreateAPIView):
    serializer_class = QuizLeadSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        lead = serializer.save()
        if not getattr(serializer, "is_duplicate", False):
            transaction.on_commit(lambda: send_quiz_notification(lead))
