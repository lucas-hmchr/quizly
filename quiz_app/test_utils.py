import pytest
import os
from unittest.mock import patch, MagicMock
from django.conf import settings
from quiz_app.utils import download_youtube_audio, transcribe_audio, generate_quiz_from_transcript, create_quiz_in_db
from quiz_app.models import Quiz, Question, Answer
from django.contrib.auth.models import User

@pytest.mark.django_db
class TestQuizUtils:
    def setup_method(self):
        self.user = User.objects.create_user(username="utiluser", password="password123")

    @patch('shutil.which')
    @patch('yt_dlp.YoutubeDL')
    def test_download_youtube_audio(self, mock_ydl_class, mock_which):
        mock_which.return_value = '/usr/bin/ffmpeg'
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {'id': 'abc', 'title': 'Test Title'}
        
        path, title = download_youtube_audio("https://youtube.com/watch?v=abc")
        assert "abc.mp3" in path
        assert title == "Test Title"

    @patch('whisper.load_model')
    def test_transcribe_audio(self, mock_load):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello world"}
        mock_load.return_value = mock_model
        
        text = transcribe_audio("dummy_path")
        assert text == "Hello world"

    @patch('google.generativeai.GenerativeModel.generate_content')
    @patch('google.generativeai.configure')
    def test_generate_quiz_from_transcript(self, mock_config, mock_gen):
        mock_response = MagicMock()
        mock_response.text = '{"title": "AI Quiz", "description": "AI Desc", "questions": []}'
        mock_gen.return_value = mock_response
        
        data = generate_quiz_from_transcript("Some transcript")
        assert data['title'] == "AI Quiz"

    def test_create_quiz_in_db(self):
        quiz_data = {
            "title": "DB Quiz",
            "description": "DB Desc",
            "questions": [
                {
                    "text": "Q1",
                    "answers": [{"text": "A1", "is_correct": True}]
                }
            ]
        }
        quiz = create_quiz_in_db(self.user, "https://url.com", quiz_data, "transcript")
        assert Quiz.objects.count() == 1
        assert Question.objects.count() == 1
        assert Answer.objects.count() == 1
        assert quiz.title == "DB Quiz"
