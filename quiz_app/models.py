from django.db import models
from django.contrib.auth.models import User

class Quiz(models.Model):
    """
    Model representing a Quiz generated from a YouTube video.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField(default="")
    transcript = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

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
    question_title = models.TextField(default="")
    question_options = models.JSONField(default=list)
    answer = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.quiz.title} - {self.question_title[:50]}"

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
    selected_answer = models.CharField(max_length=255, default="")

    class Meta:
        unique_together = ("user", "question")
