from django.shortcuts import render, get_object_or_404, redirect
from .models import Quiz, Question, Answer, QuizSession, QuizMember, QuizResults
from .forms import JoinQuizForm, QuizForm, QuestionFormSet
from django.contrib.auth.decorators import login_required

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
            return redirect('edit_quiz', quiz_id=quiz.id)
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
            return redirect('home')
    else:
        form = QuizForm(instance=quiz)
        formset = QuestionFormSet(instance=quiz)
    return render(request, 'quiz/edit_quiz.html', {'form': form, 'formset': formset})

@login_required
def create_quiz_session(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    session = QuizSession.objects.create(quiz=quiz, host=request.user)
    return redirect('quiz_session_detail', session_id=session.id)

def join_quiz(request):
    if request.method == "POST":
        form = JoinQuizForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            nickname = form.cleaned_data['nickname']
            try:
                session = QuizSession.objects.get(code=code, finished=False)
            except QuizSession.DoesNotExist:
                form.add_error('code', 'Невірний код або сесія завершена.')
                return render(request, 'quiz/join_quiz.html', {'form': form})

            member = QuizMember.objects.create(
                quiz_session=session,
                nickname=nickname
            )
            return redirect('play_quiz', member_id=member.id)
    else:
        form = JoinQuizForm()
    return render(request, 'quiz/join_quiz.html', {'form': form})

@login_required
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
        return redirect('play_quiz', member_id=member.id)

    return render(request, 'quiz/play_quiz.html', {'question': question, 'member': member})

