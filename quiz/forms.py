from django import forms
from .models import Quiz, Question, Answer
from django.forms import inlineformset_factory

class JoinQuizForm(forms.Form):
    nickname = forms.CharField(
        max_length=25,
        label="Нікнейм",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть ваш нікнейм'})
    )
    code = forms.IntegerField(
        label="Код вікторини",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введіть код вікторини'})
    )

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Назва вікторини'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Опис вікторини', 'rows': 3}),
        }

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


