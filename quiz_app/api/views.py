from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Quiz, UserAnswer
from .serializers import QuizSerializer, QuizDetailSerializer, UserAnswerSerializer
from .permissions import IsOwner
from ..utils import (
    download_youtube_audio, transcribe_audio, 
    generate_quiz_from_transcript, create_quiz_in_db
)

class QuizViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quizzes."""
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        qs = Quiz.objects.filter(user=self.request.user)
        period = self.request.query_params.get('period')
        if period == 'today':
            return qs.filter(created_at__date=timezone.now().date())
        if period == 'week':
            return qs.filter(created_at__gte=timezone.now() - timedelta(days=7))
        return qs

    def create(self, request, *args, **kwargs):
        url = request.data.get('url')
        if not url:
            return super().create(request, *args, **kwargs)
        try:
            path, _ = download_youtube_audio(url)
            text = transcribe_audio(path)
            data = generate_quiz_from_transcript(text)
            quiz = create_quiz_in_db(request.user, url, data, text)
            return Response(self.get_serializer(quiz).data, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def get_serializer_class(self):
        return QuizDetailSerializer if self.action == 'retrieve' else QuizSerializer

class QuizAnswerView(APIView):
    """API View to submit an answer."""
    def post(self, request, quiz_id):
        quiz = Quiz.objects.get(id=quiz_id, user=request.user)
        serializer = UserAnswerSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data['question'].quiz != quiz:
                return Response({"error": "Wrong quiz"}, status=400)
            UserAnswer.objects.update_or_create(
                user=request.user, question=serializer.validated_data['question'],
                defaults={'selected_answer': serializer.validated_data['selected_answer']}
            )
            return Response({"message": "Saved"})
        return Response(serializer.errors, status=400)

def get_question_result(question, user_answers):
    """Calculate result for a single question."""
    user_ans = user_answers.filter(question=question).first()
    selected_answer = user_ans.selected_answer if user_ans else None
    correct_answer = question.answer
    is_correct = (selected_answer == correct_answer) if selected_answer else False
    return {
        "question_id": question.id, "question_text": question.question_title,
        "selected_answer": selected_answer, "correct_answer": correct_answer,
        "is_correct": is_correct
    }

class QuizResultView(APIView):
    """API View to get results."""
    def get(self, request, quiz_id):
        quiz = Quiz.objects.get(id=quiz_id, user=request.user)
        questions = quiz.questions.all()
        user_ans = UserAnswer.objects.filter(user=request.user, question__quiz=quiz)
        results = [get_question_result(q, user_ans) for q in questions]
        correct_count = sum(1 for r in results if r['is_correct'])
        total = questions.count()
        return Response({
            "total_questions": total, "correct_answers": correct_count,
            "score_percentage": (correct_count / total * 100) if total else 0,
            "results": results
        })
