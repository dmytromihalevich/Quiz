from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .models import Quiz, Question, Answer, QuizSession, QuizMember, QuizResults
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm, JoinQuizForm, QuizForm, QuestionFormSet



def home(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    return render(request, 'quiz/home.html', {'quizzes': quizzes})


@login_required
def create_quiz(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            return redirect('quiz:edit_quiz', quiz_id=quiz.id)
    else:
        form = QuizForm()
    return render(request, 'quiz/create_quiz.html', {'form': form})

@login_required
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        formset = QuestionFormSet(request.POST, request.FILES, instance=quiz)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('quiz:home')
    else:
        form = QuizForm(instance=quiz)
        formset = QuestionFormSet(instance=quiz)
    return render(request, 'quiz/edit_quiz.html', {'form': form, 'formset': formset})

@login_required
def create_quiz_session(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    session = QuizSession.objects.create(quiz=quiz, host=request.user)
    return redirect('quiz:quiz_session_detail', session_id=session.id)


def join_quiz(request, quiz_id=None):
    if request.method == "POST":
        if request.user.is_authenticated:
            nickname = request.user.username
        else:
            form = JoinQuizForm(request.POST)
            if form.is_valid():
                nickname = form.cleaned_data['nickname']
            else:
                return render(request, 'quiz/join_quiz.html', {'form': form})

        if quiz_id:
            session = get_object_or_404(QuizSession, quiz_id=quiz_id, finished=False)
        else:
            code = request.POST.get('code')
            session = get_object_or_404(QuizSession, code=code, finished=False)

        member = QuizMember.objects.create(
            quiz_session=session,
            nickname=nickname
        )
        return redirect('quiz:play_quiz', member_id=member.id)
    else:
        form = JoinQuizForm()
    return render(request, 'quiz/join_quiz.html', {'form': form})


def play_quiz(request, member_id):
    member = get_object_or_404(QuizMember, id=member_id)
    session = member.quiz_session
    questions = list(session.quiz.questions.all())

    if 'current_index' not in request.session:
        request.session['current_index'] = 0
        request.session['score'] = 0

    current_index = request.session['current_index']

    if current_index >= len(questions):
        score = request.session.pop('score')
        request.session.pop('current_index')
        return render(request, 'quiz/quiz_result.html', {'score': score, 'total': len(questions)})

    question = questions[current_index]

    if request.method == "POST":
        answer_id = request.POST.get('answer')
        if answer_id:
            answer = get_object_or_404(Answer, id=int(answer_id))
            if answer.is_correct:
                request.session['score'] += 1
            QuizResults.objects.create(
                quiz_member=member,
                question=question,
                answer=answer
            )
        request.session['current_index'] += 1
        return redirect('quiz:play_quiz', member_id=member.id)

    return render(request, 'quiz/play_quiz.html', {'question': question, 'member': member})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save() 
            login(request, user)  
            return redirect('quiz:home')
    else:
        form = RegisterForm()
    return render(request, 'quiz/register.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('quiz:home')
        else:
            messages.error(request, "Невірний логін або пароль")
    else:
        form = AuthenticationForm()
    return render(request, 'quiz/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('quiz:home')
