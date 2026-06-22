from rest_framework import serializers

from ..models import QuizLead, QuizProgress, QuizQuestion
from ..services import create_quiz_lead_service
from .common import LocalizedModelSerializer


class QuizQuestionSerializer(LocalizedModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = QuizQuestion
        fields = ["id", "question_text", "question_type", "options"]

    def get_options(self, obj):
        return [{"id": o.id, "option_text": o.option_text, "next_question": o.next_question_id} for o in obj.options.all()]

class QuizProgressSerializer(LocalizedModelSerializer):
    class Meta:
        model = QuizProgress
        fields = ["session_key", "answers_data", "current_question_index", "is_completed", "updated_at"]
        read_only_fields = fields

class QuizProgressUpdateSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_options = serializers.ListField(child=serializers.IntegerField(), required=False)
    text_answer = serializers.CharField(required=False, allow_blank=True)

class QuizLeadSerializer(LocalizedModelSerializer):
    answers = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = QuizLead
        fields = ["id", "customer_name", "customer_contact", "answers", "answers_data", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def create(self, validated_data):
        answers = validated_data.pop("answers", None)
        if answers is not None and not validated_data.get("answers_data"):
            validated_data["answers_data"] = answers

        i, is_dup = create_quiz_lead_service(validated_data)
        self.is_duplicate = is_dup
        return i
