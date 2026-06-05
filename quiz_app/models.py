from django.db import models
from django.contrib.auth.models import User

class Quiz(models.Model):
    """
    Model representing a Quiz generated from a YouTube video.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    youtube_url = models.URLField()
    transcript = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class Question(models.Model):
    """
    Model representing a single question in a quiz.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()

    def __str__(self):
        return f"{self.quiz.title} - {self.text[:50]}"

class Answer(models.Model):
    """
    Model representing a possible answer for a question.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.text[:20]} - {self.text} ({self.is_correct})"

class UserQuizProgress(models.Model):
    """
    Model to track user progress on a quiz.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_progress")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "quiz")

class UserAnswer(models.Model):
    """
    Model to store user's selected answer for a question.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "question")
