import random
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'
    QUESTION_TYPES = [
        (TEXT, 'Текст'),
        (IMAGE, 'Зображення'),
        (VIDEO, 'Відео'),
    ]

    quiz = models.ForeignKey(Quiz, related_name="questions", on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default=TEXT)
    image = models.ImageField(upload_to="questions/", blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    time_limit = models.IntegerField(default=30)

    def __str__(self):
        return f"{self.quiz.title} — {self.text[:50]}"

    def clean(self):
        # Ensure image questions have either an uploaded image or an image URL
        if self.question_type == self.IMAGE and not self.image and not self.image_url:
            raise ValidationError({'image': 'Provide an uploaded image or an image URL for image questions.'})

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class QuizSession(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    host = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.IntegerField(unique=True, blank=True)
    started = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    finished = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = random.randint(100000, 999999)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quiz.title} — Код: {self.code}"

class QuizMember(models.Model):
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=25)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nickname} ({self.quiz_session.code})"

class QuizResults(models.Model):
    quiz_member = models.ForeignKey(QuizMember, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quiz_member.nickname} — {self.question.text[:30]} — {self.answer.text}"

