from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from .models import Quiz, Question, Answer, QuizSession, QuizMember, QuizResults
from .forms import RegisterForm, JoinQuizForm, QuizForm, QuestionFormSet, AnswerFormSet


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
    """
    Edit quiz with nested Question (formset) and per-question Answer formsets.
    QuestionFormSet should be an inlineformset_factory(Quiz, Question, ...) (prefix 'questions' used).
    AnswerFormSet should be an inlineformset_factory(Question, Answer, ...) (we'll use prefixes 'answers-0', 'answers-1', ...)
    """
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)

    # use explicit prefix for question formset so template + JS can target it
    QUESTION_PREFIX = 'questions'

    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        q_formset = QuestionFormSet(request.POST, request.FILES, instance=quiz, prefix=QUESTION_PREFIX)

        # Build answer formsets (bound) for validation/rendering — prefix per question index
        answer_formsets = []
        for idx, q_form in enumerate(q_formset.forms):
            prefix = f'answers-{idx}'
            # bind answers to the question instance (may not yet be saved)
            a_fs = AnswerFormSet(request.POST, request.FILES, instance=q_form.instance, prefix=prefix)
            answer_formsets.append(a_fs)

        # attach answer formsets to question forms so template can render errors and management_form
        for qf, afs in zip(q_formset.forms, answer_formsets):
            qf.answers = afs

        # validate all
        all_answers_valid = all(a.is_valid() for a in answer_formsets)
        if form.is_valid() and q_formset.is_valid() and all_answers_valid:
            # save quiz and questions
            form.save()
            q_formset.save()

            # After questions saved, re-bind answer formsets to the saved question instances and save them
            for idx, qf in enumerate(q_formset.forms):
                question_instance = qf.instance  # should now have pk
                prefix = f'answers-{idx}'
                a_fs = AnswerFormSet(request.POST, request.FILES, instance=question_instance, prefix=prefix)
                if a_fs.is_valid():
                    a_fs.save()

            return redirect('quiz:home')
        # if invalid -> fall through to render with error messages (q_formset forms already contain errors)

    else:
        form = QuizForm(instance=quiz)
        q_formset = QuestionFormSet(instance=quiz, prefix=QUESTION_PREFIX)
        # create answer formsets for existing question forms
        answer_formsets = []
        for idx, q_form in enumerate(q_formset.forms):
            prefix = f'answers-{idx}'
            a_fs = AnswerFormSet(instance=q_form.instance, prefix=prefix)
            answer_formsets.append(a_fs)
            # attach for template
            q_form.answers = a_fs

    return render(request, 'quiz/edit_quiz.html', {
        'form': form,
        'formset': q_formset,
    })


@login_required
def create_quiz_session(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    session = QuizSession.objects.create(quiz=quiz, host=request.user)
    return redirect('quiz:quiz_session_detail', session_id=session.id)


def join_quiz(request, quiz_id=None):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    # New behavior: user can choose role 'host' or 'player'.
    # - Host: must be authenticated; creates a new QuizSession and becomes a member.
    # - Player: must provide a session `code` (or will join an existing open session) and a nickname (if anonymous).

    if request.method == "POST":
        form = JoinQuizForm(request.POST)
        if not form.is_valid():
            return render(request, 'quiz/join_quiz.html', {'form': form, 'quiz': quiz})

        role = form.cleaned_data.get('role')
        # Host flow
        if role == 'host':
            if not request.user.is_authenticated:
                messages.error(request, "Ви повинні увійти в систему, щоб створити сесію як ведучий.")
                return redirect('quiz:login')

            # create a new session (always create a fresh one for this host)
            session = QuizSession.objects.create(quiz=quiz, host=request.user)
            member = QuizMember.objects.create(quiz_session=session, nickname=request.user.username)
            messages.success(request, f"Сесію створено. Код сесії: {session.code}")
            return redirect('quiz:quiz_session_detail', session_id=session.id)

        # Player flow: validate code and nickname if needed
        code = form.cleaned_data.get('code')
        if not code:
            form.add_error('code', 'Введіть код сесії')
            return render(request, 'quiz/join_quiz.html', {'form': form, 'quiz': quiz})

        if request.user.is_authenticated:
            nickname = request.user.username
        else:
            nickname = form.cleaned_data.get('nickname')
            if not nickname:
                form.add_error('nickname', 'Введіть нікнейм')
                return render(request, 'quiz/join_quiz.html', {'form': form, 'quiz': quiz})

        try:
            session = QuizSession.objects.get(quiz=quiz, code=code, finished=False)
        except QuizSession.DoesNotExist:
            form.add_error('code', 'Сесія з таким кодом не знайдена або вже завершена.')
            return render(request, 'quiz/join_quiz.html', {'form': form, 'quiz': quiz})

        member = QuizMember.objects.create(quiz_session=session, nickname=nickname)
        # remember this member id in the user's session so lobby can show an "Enter quiz" button
        request.session[f'member_{session.id}'] = member.id
        # If session already started, send player straight to the quiz; otherwise send to lobby
        if session.started:
            return redirect('quiz:play_quiz', member_id=member.id)
        return redirect('quiz:quiz_session_detail', session_id=session.id)

    # GET
    form = JoinQuizForm()
    return render(request, 'quiz/join_quiz.html', {'form': form, 'quiz': quiz})


def quiz_session_detail(request, session_id):
    """Lobby/detail view for a quiz session. Shows session code and current members.

    Only the host (session.host) can access management features here.
    """
    session = get_object_or_404(QuizSession, id=session_id)

    # Basic access: allow host and any member of the session to view. Hosts get extra controls.
    is_host = request.user == session.host
    members = QuizMember.objects.filter(quiz_session=session)

    # find this user's member id for this session (if any)
    member_session_key = f'member_{session.id}'
    current_member_id = request.session.get(member_session_key)

    return render(request, 'quiz/quiz_session_detail.html', {
        'session': session,
        'members': members,
        'is_host': is_host,
        'current_member_id': current_member_id,
    })


def session_status(request, session_id):
    """Return JSON with session started status. Used by lobby polling."""
    session = get_object_or_404(QuizSession, id=session_id)
    return JsonResponse({'started': bool(session.started)})


@login_required
def start_session(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id)
    if request.user != session.host:
        messages.error(request, 'Тільки ведучий може запускати сесію.')
        return redirect('quiz:quiz_session_detail', session_id=session.id)

    # mark started
    session.started = True
    session.save()
    messages.success(request, 'Сесію запущено. Гравці можуть почати гру.')
    return redirect('quiz:quiz_session_detail', session_id=session.id)


@login_required
def quiz_session_results(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id)
    if request.user != session.host:
        messages.error(request, 'Тільки ведучий може переглядати результати.')
        return redirect('quiz:quiz_session_detail', session_id=session.id)

    members = QuizMember.objects.filter(quiz_session=session)
    # compute scores per member
    results = []
    for m in members:
        correct_count = QuizResults.objects.filter(quiz_member=m, answer__is_correct=True).count()
        total = QuizResults.objects.filter(quiz_member=m).count()
        results.append({'member': m, 'correct': correct_count, 'total': total})

    return render(request, 'quiz/quiz_session_results.html', {
        'session': session,
        'results': results,
    })


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
