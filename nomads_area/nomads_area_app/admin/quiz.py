import json

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from ..models import QuizLead, QuizQuestion
from .common import TranslationMediaMixin
from .inlines import QuizAnswerOptionInline


@admin.register(QuizQuestion)
class QuizQuestionAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["id", "question_text", "question_type", "is_active", "order"]
    list_filter = ["question_type", "is_active"]; search_fields = ["question_text"]
    list_editable = ["is_active", "order"]; inlines = [QuizAnswerOptionInline]

@admin.register(QuizLead)
class QuizLeadAdmin(admin.ModelAdmin):
    list_display = ["id", "customer_name", "customer_contact", "status", "created_at"]
    list_filter = ["status", "created_at"]; search_fields = ["customer_name", "customer_contact"]
    list_editable = ["status"]; readonly_fields = ["created_at", "answers_data_pretty"]
    fields = ["customer_name", "customer_contact", "status", "answers_data_pretty", "created_at"]

    def answers_data_pretty(self, i):
        return json.dumps(i.answers_data, ensure_ascii=False, indent=4) if i.answers_data else "-"
    answers_data_pretty.short_description = "Ответы"
