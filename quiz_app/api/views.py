from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from ..models import Quiz
from .serializers import QuizSerializer, QuizDetailSerializer
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
        if self.action in ['retrieve', 'update', 'partial_update']:
            return QuizDetailSerializer
        return QuizSerializer

