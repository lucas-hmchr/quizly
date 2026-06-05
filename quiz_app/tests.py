import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Quiz, Question, UserAnswer

@pytest.mark.django_db
class TestQuiz:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client.force_authenticate(user=self.user)
        self.quiz = Quiz.objects.create(
            user=self.user,
            title="Test Quiz",
            video_url="https://youtube.com/watch?v=123"
        )
        self.question = Question.objects.create(
            quiz=self.quiz, 
            question_title="What is Python?",
            question_options=["A language", "A snake", "Both"],
            answer="Both"
        )

    def test_list_quizzes(self):
        url = reverse('quiz-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_quiz_detail(self):
        url = reverse('quiz-detail', kwargs={'pk': self.quiz.id})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == "Test Quiz"
        assert len(response.data['questions']) == 1

    @patch('quiz_app.api.views.download_youtube_audio')
    @patch('quiz_app.api.views.transcribe_audio')
    @patch('quiz_app.api.views.generate_quiz_from_transcript')
    def test_generate_quiz(self, mock_gen, mock_trans, mock_dl):
        mock_dl.return_value = ("/tmp/audio.mp3", "Test Title")
        mock_trans.return_value = "This is a transcript."
        mock_gen.return_value = {
            "title": "New Quiz",
            "description": "Desc",
            "questions": [
                {
                    "text": "Q1",
                    "answers": [{"text": "A1", "is_correct": True}]
                }
            ]
        }
        
        url = reverse('quiz-list')
        response = self.client.post(url, {"url": "https://youtube.com/watch?v=abc"})
        assert response.status_code == status.HTTP_201_CREATED
        assert Quiz.objects.filter(title="New Quiz").exists()

    def test_submit_answer(self):
        url = reverse('quiz-answer', kwargs={'quiz_id': self.quiz.id})
        data = {
            "question": self.question.id,
            "selected_answer": "Both"
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert UserAnswer.objects.filter(user=self.user, question=self.question).exists()

    def test_get_result(self):
        UserAnswer.objects.create(user=self.user, question=self.question, selected_answer="Both")
        url = reverse('quiz-result', kwargs={'quiz_id': self.quiz.id})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['correct_answers'] == 1
        assert response.data['score_percentage'] == 100.0
