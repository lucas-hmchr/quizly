from rest_framework import serializers
from ..models import Quiz, Question, UserQuizProgress, UserAnswer

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
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "created_at", "updated_at", "video_url", "questions"]
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

class UserAnswerSerializer(serializers.ModelSerializer):
    """
    Serializer for submitting a user's answer.
    """
    class Meta:
        model = UserAnswer
        fields = ["id", "question", "selected_answer"]

    def validate(self, attrs):
        # Ensure the answer is one of the options
        if attrs['selected_answer'] not in attrs['question'].question_options:
            raise serializers.ValidationError("Invalid answer option.")
        return attrs

class QuizResultSerializer(serializers.Serializer):
    """
    Serializer for displaying quiz results.
    """
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    score_percentage = serializers.FloatField()
    results = serializers.ListField()
