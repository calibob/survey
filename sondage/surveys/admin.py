from django.contrib import admin
from .models import Survey, Question, QuestionOption

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 3

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [QuestionInline]
    date_hierarchy = 'created_at'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une nouvelle instance
            obj.author = request.user
        super().save_model(request, obj, form, change)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'question_type', 'required', 'order')
    list_filter = ('question_type', 'required', 'survey')
    search_fields = ('text', 'survey__title')
    inlines = [QuestionOptionInline]
    
@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'order')
    list_filter = ('question__survey', 'question')
    search_fields = ('text', 'question__text')
