from django import forms
from .models import Quiz, Question, Answer
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login




class JoinQuizForm(forms.Form):
    nickname = forms.CharField(
        max_length=25,
        label="Нікнейм",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть ваш нікнейм'})
    )
    code = forms.IntegerField(
        label="Код вікторини",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введіть код вікторини'})
    )
    ROLE_CHOICES = [
        ('player', 'Гравець'),
        ('host', 'Ведучий'),
    ]
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial='player',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Роль'
    )

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


QuestionFormSet = inlineformset_factory(
    Quiz,
    Question,
    fields=['text', 'question_type', 'image', 'video_url', 'time_limit'],
    extra=1,
    widgets={
        'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Текст запитання'}),
        'question_type': forms.Select(attrs={'class': 'form-select'}),
        'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL відео'}),
        'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'placeholder': 'Час на відповідь'}),
    }
)

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    fields=['text', 'is_correct'],
    extra=1,
    can_delete=True,
    widgets={
        'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Текст відповіді'}),
        'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)