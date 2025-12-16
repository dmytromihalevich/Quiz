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


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'image', 'image_url', 'video_url', 'time_limit']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Текст запитання'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Посилання на зображення'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL відео'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'placeholder': 'Час на відповідь'}),
        }

    def clean(self):
        cleaned = super().clean()
        qtype = cleaned.get('question_type')
        image = cleaned.get('image')
        image_url = cleaned.get('image_url')
        if qtype == Question.IMAGE and not image and not image_url:
            raise forms.ValidationError('Для питань з типом "Зображення" потрібно завантажити зображення або вказати посилання на нього.')
        return cleaned


QuestionFormSet = inlineformset_factory(
    Quiz,
    Question,
    form=QuestionForm,
    extra=1,
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