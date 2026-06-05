from rest_framework import serializers
from ..models import Quiz, Question, Answer, UserQuizProgress, UserAnswer

class AnswerSerializer(serializers.ModelSerializer):
    """
    Serializer for the Answer model.
    """
    class Meta:
        model = Answer
        fields = ["id", "text", "is_correct"]

class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Question model. Includes answers.
    """
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "answers"]

class QuizSerializer(serializers.ModelSerializer):
    """
    Serializer for the Quiz model.
    """
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "youtube_url", "created_at", "questions_count"]
        read_only_fields = ["id", "created_at", "youtube_url"]

class QuizDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for the Quiz model, including questions.
    """
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "youtube_url", "transcript", "created_at", "questions"]
        read_only_fields = ["id", "created_at", "youtube_url", "transcript"]

class UserAnswerSerializer(serializers.ModelSerializer):
    """
    Serializer for submitting a user's answer.
    """
    class Meta:
        model = UserAnswer
        fields = ["id", "question", "selected_answer"]

    def validate(self, attrs):
        # Ensure the answer belongs to the question
        if attrs['selected_answer'].question != attrs['question']:
            raise serializers.ValidationError("Answer does not belong to the question.")
        return attrs

class QuizResultSerializer(serializers.Serializer):
    """
    Serializer for displaying quiz results.
    """
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    score_percentage = serializers.FloatField()
    results = serializers.ListField()
