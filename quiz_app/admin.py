from django.contrib import admin
from .models import Quiz, Question

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_title', 'quiz')
    list_filter = ('quiz',)

class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('title', 'description')

admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
