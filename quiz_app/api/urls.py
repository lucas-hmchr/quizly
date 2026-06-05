from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuizAnswerView, QuizResultView

router = DefaultRouter()
router.register(r'', QuizViewSet, basename='quiz')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:quiz_id>/answer/', QuizAnswerView.as_view(), name='quiz-answer'),
    path('<int:quiz_id>/result/', QuizResultView.as_view(), name='quiz-result'),
]
