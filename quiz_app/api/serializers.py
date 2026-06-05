from rest_framework import serializers
from ..models import Quiz, Question

class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Question model.
    """
    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer", "created_at", "updated_at"]

class QuizSerializer(serializers.ModelSerializer):
    """
    Serializer for the Quiz model.
    """
    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "created_at", "updated_at", "video_url"]
        read_only_fields = ["id", "created_at", "updated_at", "video_url"]

class QuizDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for the Quiz model, including questions.
    """
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "created_at", "updated_at", "video_url", "questions"]
        read_only_fields = ["id", "created_at", "updated_at", "video_url"]

