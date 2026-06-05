import os
import json
import shutil
import time
import yt_dlp
import whisper
from google import genai
from google.genai import errors
from django.conf import settings
from .models import Quiz, Question

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
    print(result["text"])
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
    """Generate quiz using Gemini with fallback and retries."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = get_quiz_prompt(transcript)
    
    # Models to try in order of preference
    # We include several versions to handle varying quota and availability
    models = [
        'gemini-2.0-flash', 
        'gemini-3-flash-preview', 
        'gemini-flash-latest', 
        'gemini-3.1-flash-lite',
        'gemini-flash-lite-latest'
    ]
    
    last_error = None
    for model_id in models:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt
                )
                json_text = clean_json_response(response.text)
                return json.loads(json_text)
            except (errors.APIError, errors.ClientError, errors.ServerError) as e:
                last_error = e
                # Attempt to extract status code
                status_code = getattr(e, 'code', None)
                err_msg = str(e).lower()
                
                if status_code is None:
                    if "429" in err_msg: status_code = 429
                    elif "503" in err_msg: status_code = 503
                    elif "500" in err_msg: status_code = 500

                # If limit is 0, don't bother retrying this model
                if status_code == 429 and "limit: 0" in err_msg:
                    print(f"Model {model_id} has 0 quota. Trying next model...")
                    break

                # 429 = Resource Exhausted, 503 = Service Unavailable, 500 = Internal Error
                if status_code in [429, 503, 500] or "quota" in err_msg:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 2
                        print(f"Retrying {model_id} (attempt {attempt + 1}/{max_retries}) in {wait_time}s due to error: {e}")
                        time.sleep(wait_time)
                        continue
                
                print(f"Model {model_id} failed: {e}. Trying next model if available...")
                break 
            except Exception as e:
                last_error = e
                print(f"Unexpected error with {model_id}: {last_error}")
                break
                
    if last_error:
        raise last_error
    raise RuntimeError("Failed to generate quiz from transcript after trying all available models.")

def create_quiz_in_db(user, url, data, transcript):
    """Save quiz to DB."""
    quiz = Quiz.objects.create(
        user=user, video_url=url, transcript=transcript,
        title=data.get('title', 'Generated Quiz'),
        description=data.get('description', '')
    )
    for q_data in data.get('questions', []):
        options = [a.get('text') for a in q_data.get('answers', [])]
        correct_answer = next((a.get('text') for a in q_data.get('answers', []) if a.get('is_correct')), None)
        Question.objects.create(
            quiz=quiz, 
            question_title=q_data.get('text'),
            question_options=options,
            answer=correct_answer
        )
    return quiz
