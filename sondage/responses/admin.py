from django.contrib import admin
from .models import SurveyResponse, Answer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'selected_option', 'text_answer', 'scale_answer')
    can_delete = False

@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('survey', 'user', 'ip_address', 'submitted_at')
    list_filter = ('survey', 'submitted_at')
    search_fields = ('survey__title', 'user__username', 'ip_address')
    date_hierarchy = 'submitted_at'
    readonly_fields = ('survey', 'user', 'ip_address', 'submitted_at')
    inlines = [AnswerInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('survey_response', 'question', 'get_answer_display')
    list_filter = ('question__survey', 'question')
    search_fields = ('question__text', 'text_answer')
    
    def get_answer_display(self, obj):
        return obj.get_answer_value()
    get_answer_display.short_description = 'Réponse'
