from django.db import transaction
from rest_framework import serializers

from ..models import QuizLead, QuizQuestion
from .common import (
    _acquire_fingerprint_lock,
    _fingerprint,
    _normalize_text,
    _recent_duplicate,
)


def update_quiz_progress_service(progress, validated_data):
    question_id = validated_data["question_id"]
    text_answer = validated_data.get("text_answer", "")
    selected_options = validated_data.get("selected_options", [])

    try:
        question = QuizQuestion.objects.prefetch_related("options").get(pk=question_id)
    except QuizQuestion.DoesNotExist as exc:
        raise serializers.ValidationError({"question_id": "Вопрос не найден."}) from exc

    answers = progress.answers_data or {}
    if question.question_type == "text":
        answers[str(question_id)] = {"question": question.question_text, "answer": text_answer}
        next_opt = question.options.filter(next_question__isnull=False).first()
        next_id = next_opt.next_question_id if next_opt else None
    else:
        selected_objects = question.options.filter(id__in=selected_options)
        answers[str(question_id)] = {"question": question.question_text, "answer": [o.option_text for o in selected_objects]}
        next_id = next((o.next_question_id for o in selected_objects if o.next_question_id), None)

    progress.answers_data = answers
    if next_id:
        progress.current_question_index = next_id
    else:
        nxt = QuizQuestion.objects.filter(is_active=True, order__gt=question.order).order_by("order").first()
        progress.current_question_index = nxt.id if nxt else progress.current_question_index
        progress.is_completed = not nxt
    progress.save(update_fields=["answers_data", "current_question_index", "is_completed", "updated_at"])
    return progress

def create_quiz_lead_service(validated_data):
    validated_data = validated_data.copy()
    validated_data["customer_contact"] = str(validated_data["customer_contact"]).strip()
    fingerprint = _fingerprint({
        "customer_name": _normalize_text(validated_data.get("customer_name")),
        "customer_contact": _normalize_text(validated_data["customer_contact"]),
        "answers_data": validated_data.get("answers_data") or {},
    })
    with transaction.atomic():
        _acquire_fingerprint_lock(fingerprint)
        duplicate = _recent_duplicate(QuizLead, fingerprint)
        if duplicate:
            return duplicate, True
        return QuizLead.objects.create(request_fingerprint=fingerprint, **validated_data), False
