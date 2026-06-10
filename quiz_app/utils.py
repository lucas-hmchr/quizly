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


QUIZ_MODELS = [
    "gemini-2.0-flash",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
]

RETRY_STATUS_CODES = [429, 503, 500]
MAX_RETRIES = 3


def get_ydl_opts(output_path):
    """Return yt_dlp options."""
    return {
        "format": "bestaudio/best",
        "postprocessors": [get_audio_postprocessor()],
        "outtmpl": output_path,
    }


def get_audio_postprocessor():
    """Return audio postprocessor settings."""
    return {
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }


def download_youtube_audio(url):
    """Download audio from YouTube."""
    ensure_ffmpeg_installed()
    path = os.path.join(settings.AUDIO_FILES_DIR, "%(id)s.%(ext)s")
    opts = get_ydl_opts(path)

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    return get_download_result(info)


def ensure_ffmpeg_installed():
    """Check if FFmpeg is installed."""
    if shutil.which("ffmpeg"):
        return

    raise RuntimeError(
        "FFmpeg not found. Please install FFmpeg and add it to your PATH."
    )


def get_download_result(info):
    """Return downloaded file path and video title."""
    file = os.path.join(settings.AUDIO_FILES_DIR, f"{info['id']}.mp3")
    title = info.get("title", "Unknown Title")
    return file, title


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
        return content[7:-3].strip()
    if content.startswith("```"):
        return content[3:-3].strip()

    return content


def generate_quiz_from_transcript(transcript):
    """Generate quiz using Gemini with fallback and retries."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = get_quiz_prompt(transcript)
    last_error = None

    for model_id in QUIZ_MODELS:
        result, error = try_model(client, model_id, prompt)
        last_error = error or last_error
        if result is not None:
            return result

    raise_generation_error(last_error)


def try_model(client, model_id, prompt):
    """Try one Gemini model with retries."""
    last_error = None

    for attempt in range(MAX_RETRIES):
        result, should_continue, error = try_model_attempt(
            client, model_id, prompt, attempt
        )
        last_error = error or last_error
        if result is not None or not should_continue:
            return result, last_error

    return None, last_error


def try_model_attempt(client, model_id, prompt, attempt):
    """Try one generation attempt."""
    try:
        result = generate_with_model(client, model_id, prompt)
        return result, False, None
    except (errors.APIError, errors.ClientError, errors.ServerError) as error:
        return handle_gemini_error(model_id, attempt, error)
    except Exception as error:
        print(f"Unexpected error with {model_id}: {error}")
        return None, False, error


def generate_with_model(client, model_id, prompt):
    """Generate quiz JSON with a Gemini model."""
    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
    )
    json_text = clean_json_response(response.text)
    return json.loads(json_text)


def handle_gemini_error(model_id, attempt, error):
    """Handle retryable Gemini API errors."""
    status_code = get_error_status_code(error)
    error_message = str(error).lower()

    if should_skip_model(status_code, error_message):
        print(f"Model {model_id} has 0 quota. Trying next model...")
        return None, False, error

    if can_retry(status_code, error_message, attempt):
        retry_model_later(model_id, attempt, error)
        return None, True, error

    print(f"Model {model_id} failed: {error}. Trying next model if available...")
    return None, False, error


def get_error_status_code(error):
    """Extract status code from Gemini error."""
    status_code = getattr(error, "code", None)
    error_message = str(error).lower()

    if status_code is not None:
        return status_code

    return get_status_code_from_message(error_message)


def get_status_code_from_message(error_message):
    """Extract status code from error message."""
    if "429" in error_message:
        return 429
    if "503" in error_message:
        return 503
    if "500" in error_message:
        return 500

    return None


def should_skip_model(status_code, error_message):
    """Check if model should be skipped."""
    return status_code == 429 and "limit: 0" in error_message


def can_retry(status_code, error_message, attempt):
    """Check if request should be retried."""
    if attempt >= MAX_RETRIES - 1:
        return False

    return status_code in RETRY_STATUS_CODES or "quota" in error_message


def retry_model_later(model_id, attempt, error):
    """Wait before retrying a model."""
    wait_time = get_wait_time(attempt)
    print_retry_message(model_id, attempt, wait_time, error)
    time.sleep(wait_time)


def get_wait_time(attempt):
    """Return exponential backoff wait time."""
    return (2 ** attempt) + 2


def print_retry_message(model_id, attempt, wait_time, error):
    """Print retry message."""
    print(
        f"Retrying {model_id} "
        f"(attempt {attempt + 1}/{MAX_RETRIES}) "
        f"in {wait_time}s due to error: {error}"
    )


def raise_generation_error(last_error):
    """Raise final generation error."""
    if last_error:
        raise last_error

    raise RuntimeError(
        "Failed to generate quiz from transcript after trying all available models."
    )


def create_quiz_in_db(user, url, data, transcript):
    """Save quiz to DB."""
    quiz = create_quiz(user, url, data, transcript)
    create_questions(quiz, data)
    return quiz


def create_quiz(user, url, data, transcript):
    """Create quiz object."""
    return Quiz.objects.create(
        user=user,
        video_url=url,
        transcript=transcript,
        title=data.get("title", "Generated Quiz"),
        description=data.get("description", ""),
    )


def create_questions(quiz, data):
    """Create all question objects."""
    for question_data in data.get("questions", []):
        create_question(quiz, question_data)


def create_question(quiz, question_data):
    """Create one question object."""
    answers = question_data.get("answers", [])
    Question.objects.create(
        quiz=quiz,
        question_title=question_data.get("text"),
        question_options=get_answer_options(answers),
        answer=get_correct_answer(answers),
    )


def get_answer_options(answers):
    """Return answer option texts."""
    return [answer.get("text") for answer in answers]


def get_correct_answer(answers):
    """Return correct answer text."""
    return next(
        (answer.get("text") for answer in answers if answer.get("is_correct")),
        None,
    )