from django import forms
from .models import Quiz, Question, Answer

class JoinQuizForm(forms.Form):
    code = forms.IntegerField(label="Код вікторини")
    nickname = forms.CharField(label="Нікнейм", max_length=25)

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'is_active']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'image', 'video_url', 'time_limit']


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct', 'explanation']

