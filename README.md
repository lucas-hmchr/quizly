# Quizly Backend

Quizly is a Django-based REST API that generates interactive quizzes from YouTube videos using AI.

## Features

- **User Authentication**: JWT-based authentication using HttpOnly cookies.
- **AI Quiz Generation**: 
    - Downloads audio from YouTube URLs.
    - Transcribes audio using OpenAI Whisper.
    - Generates 10 questions with 4 options each using Google Gemini Flash AI.
- **Quiz Management**: Create, view, update, and delete quizzes.
- **Quiz Gameplay**: Questions include correct answers for frontend-side result calculation.
- **Resource Oriented**: Clean RESTful API structure.

## Prerequisites

- Python 3.10+
- **FFMPEG**: Must be installed globally on your system.
- Gemini API Key: Required for quiz generation.

## Installation

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   - Copy `.env.template` to `.env`.
   - Add your `GEMINI_API_KEY`.
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Project Structure

- `core/`: Project configuration and settings.
- `auth_app/`: User registration, login, and authentication logic.
- `quiz_app/`: Quiz generation logic, models, and API endpoints.
- `audio_files/`: Temporary storage for downloaded audio (gitignored).
- `transcripts/`: Storage for generated transcripts (gitignored).

## API Endpoints

### Authentication
- `POST /api/register/`: Register a new user.
- `POST /api/login/`: Login and receive tokens in cookies.
- `POST /api/logout/`: Logout and clear cookies.
- `GET /api/user/`: Get current user info.

### Quizzes
- `GET /api/quizzes/`: List user's quizzes (supports `?period=today` or `?period=week`).
- `POST /api/quizzes/`: Generate a quiz from a YouTube URL (send `{"url": "..."}`).
- `GET /api/quizzes/<id>/`: Get quiz details (includes questions with correct answers).
- `PATCH /api/quizzes/<id>/`: Update quiz title/description.
- `DELETE /api/quizzes/<id>/`: Delete a quiz.

## Testing

Run tests with coverage:
```bash
pytest --cov=.
```

## Note on Whisper AI
The first time you generate a quiz, Whisper will download its model (default: "base"). This may take a few minutes depending on your internet connection.
