import os
import json
import shutil
import yt_dlp
import whisper
import google.generativeai as genai
from django.conf import settings
from .models import Quiz, Question, Answer

def get_ydl_opts(output_path):
    """Return yt_dlp options."""
    return {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
    }

def download_youtube_audio(url):
    """Download audio from YouTube."""
    if not shutil.which('ffmpeg'):
        raise RuntimeError("FFmpeg not found. Please install FFmpeg and add it to your PATH.")
    
    path = os.path.join(settings.AUDIO_FILES_DIR, '%(id)s.%(ext)s')
    opts = get_ydl_opts(path)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = os.path.join(settings.AUDIO_FILES_DIR, f"{info['id']}.mp3")
        return file, info.get('title', 'Unknown Title')

def transcribe_audio(file_path):
    """Transcribe audio using Whisper."""
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

def get_quiz_prompt(transcript):
    """Return the prompt for Gemini."""
    return f"""
    Based on the following transcript, create a quiz with 10 questions.
    Each question must have exactly 4 answer possibilities.
    Only one answer can be correct.
    Return result ONLY as JSON:
    {{
        "title": "Quiz Title", "description": "Desc",
        "questions": [
            {{
                "text": "Q?",
                "answers": [{{"text": "A", "is_correct": true}}, ...]
            }}
        ]
    }}
    Transcript: {transcript}
    """

def clean_json_response(text):
    """Extract JSON from AI response."""
    content = text.strip()
    if content.startswith("```json"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()
    return content

def generate_quiz_from_transcript(transcript):
    """Generate quiz using Gemini Flash."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = get_quiz_prompt(transcript)
    response = model.generate_content(prompt)
    json_text = clean_json_response(response.text)
    return json.loads(json_text)

def save_answers(question, answers_data):
    """Save answers for a question."""
    for a_data in answers_data:
        Answer.objects.create(
            question=question,
            text=a_data.get('text'),
            is_correct=a_data.get('is_correct', False)
        )

def create_quiz_in_db(user, url, data, transcript):
    """Save quiz to DB."""
    quiz = Quiz.objects.create(
        user=user, youtube_url=url, transcript=transcript,
        title=data.get('title', 'Generated Quiz'),
        description=data.get('description', '')
    )
    for q_data in data.get('questions', []):
        question = Question.objects.create(quiz=quiz, text=q_data.get('text'))
        save_answers(question, q_data.get('answers', []))
    return quiz
