from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from datetime import timedelta

from .forms import StudentLoginForm, TeacherLoginForm, CreateTestForm, QuestionForm
from .models import Test, Question, Answer, Result, StudentAnswer, Tag, Invitation
from accounts.forms import RegisterForm

User = get_user_model()


# ──────────────────────────────────────────────
# 🔐 СТРАНИЦА ЛОГИНА
# ──────────────────────────────────────────────
def teacher_results_redirect(request, test_id):
    """Если залогинен staff — сразу на результаты теста, иначе на логин с возвратом"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('test_results', test_id=test_id)
    return redirect(f'/tests/login/?next=/tests/test/{test_id}/results/')

def login_page(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('teacher_home')

    form = TeacherLoginForm()
    if request.method == 'POST':
        form = TeacherLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('teacher_home')
            else:
                form.add_error(None, 'Неверный логин, пароль или недостаточно прав.')

    return render(request, 'tests/login_page.html', {'form': form})

# ──────────────────────────────────────────────
# 📋 ПУБЛИЧНОЕ
# ──────────────────────────────────────────────

def test_entry(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student_form = StudentLoginForm()
    teacher_form = TeacherLoginForm()

    if request.method == 'POST':
        if 'student_login' in request.POST:
            student_form = StudentLoginForm(request.POST)
            if student_form.is_valid():
                request.session['student_first_name'] = student_form.cleaned_data['first_name']
                request.session['student_last_name'] = student_form.cleaned_data['last_name']
                return redirect('test_detail', test_id=test_id)

        elif 'teacher_login' in request.POST:
            teacher_form = TeacherLoginForm(request.POST)
            if teacher_form.is_valid():
                user = authenticate(
                    request,
                    username=teacher_form.cleaned_data['username'],
                    password=teacher_form.cleaned_data['password']
                )
                if user is not None:
                    login(request, user)
                    return redirect('teacher_home')
                else:
                    teacher_form.add_error(None, 'Неверный логин или пароль.')

    return render(request, 'tests/test_entry.html', {
        'test': test,
        'student_form': student_form,
        'teacher_form': teacher_form,
    })


def test_detail(request, test_id):
    first_name = request.session.get('student_first_name', '')
    last_name = request.session.get('student_last_name', '')
    if not first_name and not last_name:
        return redirect('test_entry', test_id=test_id)

    test = get_object_or_404(Test, id=test_id)
    questions = Question.objects.filter(test=test)

    questions_list = []
    for question in questions:
        answers = Answer.objects.filter(question=question)
        questions_list.append({
            'question': question,
            'answers': answers,
        })

    return render(request, 'tests/test_detail.html', {
        'test': test,
        'questions_list': questions_list,
    })


@transaction.atomic
def submit_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    questions = Question.objects.filter(test=test)
    score = 0
    total = questions.count()

    questions_details = []
    for question in questions:
        answer_id = request.POST.get(f'question_{question.id}')
        user_answer = None
        is_correct = False

        if answer_id:
            try:
                user_answer = Answer.objects.get(id=answer_id)
                is_correct = user_answer.is_correct
                if is_correct:
                    score += 1
            except Answer.DoesNotExist:
                pass

        correct_answer = Answer.objects.filter(question=question, is_correct=True).first()
        all_answers = Answer.objects.filter(question=question)

        questions_details.append({
            'question': question,
            'user_answer': user_answer,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'all_answers': all_answers,
        })

    first_name = request.session.get('student_first_name', '')
    last_name = request.session.get('student_last_name', '')

    if request.user.is_authenticated:
        result = Result.objects.create(
            student=request.user,
            test=test,
            score=score,
            total=total
        )
    else:
        result = Result.objects.create(
            first_name=first_name,
            last_name=last_name,
            test=test,
            score=score,
            total=total
        )

    for qd in questions_details:
        StudentAnswer.objects.create(
            result=result,
            question=qd['question'],
            selected_answer=qd['user_answer'],
            is_correct=qd['is_correct']
        )

    messages.success(request, f'✅ Вы набрали {score} из {total} баллов!')
    request.session.pop('questions_details', None)

    test.last_activity = timezone.now()
    test.save(update_fields=['last_activity'])

    return redirect('test_result', result_id=result.id)


def test_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)

    if result.student and result.student != request.user:
        messages.error(request, 'Это не ваш результат!')
        return redirect('teacher_home')

    percent = int(result.score / result.total * 100) if result.total > 0 else 0

    if result.first_name and result.last_name:
        student_name = f"{result.first_name} {result.last_name}"
    elif result.student:
        student_name = result.student.username
    else:
        student_name = "Аноним"

    student_answers = result.answers.all().select_related('question', 'selected_answer')
    questions_details = []
    for sa in student_answers:
        correct_answer = Answer.objects.filter(question=sa.question, is_correct=True).first()
        all_answers = Answer.objects.filter(question=sa.question)
        questions_details.append({
            'question_text': sa.question.text,
            'user_answer_id': sa.selected_answer.id if sa.selected_answer else None,
            'user_answer_text': sa.selected_answer.text if sa.selected_answer else '(не выбран)',
            'is_correct': sa.is_correct,
            'correct_answer_text': correct_answer.text if correct_answer else '',
            'all_answers': [{'id': a.id, 'text': a.text, 'is_correct': a.is_correct} for a in all_answers],
        })

    return render(request, 'tests/test_result.html', {
        'result': result,
        'test': result.test,
        'score': result.score,
        'total': result.total,
        'percent': percent,
        'student_name': student_name,
        'questions_details': questions_details,
    })


# ──────────────────────────────────────────────
# 👑 DASHBOARD УЧИТЕЛЯ
# ──────────────────────────────────────────────
@staff_member_required
def teacher_home(request):
    from django.db.models import Count, Q

    tests = Test.objects.all().order_by('-last_activity')

    # Аннотация: уникальные ученики для каждого теста
    tests = tests.annotate(
        students_count=Count(
            'result',
            filter=~Q(result__first_name='') & ~Q(result__last_name=''),
            distinct=True
        )
    )

    search_query = request.GET.get('search', '')
    if search_query:
        tests = tests.filter(title__icontains=search_query)

    tag_filter = request.GET.get('tag', '')
    if tag_filter:
        tests = tests.filter(tags__name=tag_filter)

    paginator = Paginator(tests, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tests/teacher_home.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_tests': paginator.count,
        'all_tags': Tag.objects.all(),
        'current_tag': tag_filter,
    })

# ──────────────────────────────────────────────
# 🔗 РЕЗУЛЬТАТЫ ТЕСТА (список попыток)
# ──────────────────────────────────────────────
@staff_member_required
def test_results(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    results = Result.objects.filter(test=test).order_by('-completed_at')

    students = {}
    for r in results:
        if r.first_name and r.last_name:
            name = f"{r.first_name} {r.last_name}"
        elif r.student:
            name = r.student.username
        else:
            name = "Аноним"

        if name not in students:
            students[name] = []

        students[name].append({
            'id': r.id,
            'score': r.score,
            'total': r.total,
            'percent': int(r.score / r.total * 100) if r.total > 0 else 0,
            'completed_at': r.completed_at,
        })

    return render(request, 'tests/test_results.html', {
        'test': test,
        'students': students,
    })


# ──────────────────────────────────────────────
# 🔍 ДЕТАЛИ ОДНОЙ ПОПЫТКИ (карточка ученика)
# ──────────────────────────────────────────────
@staff_member_required
def result_detail(request, result_id):
    result = get_object_or_404(Result, id=result_id)

    if result.first_name and result.last_name:
        student_name = f"{result.first_name} {result.last_name}"
    elif result.student:
        student_name = result.student.username
    else:
        student_name = "Аноним"

    percent = int(result.score / result.total * 100) if result.total > 0 else 0

    student_answers = result.answers.all().select_related('question', 'selected_answer')
    questions_data = []
    for sa in student_answers:
        correct_answer = Answer.objects.filter(question=sa.question, is_correct=True).first()
        questions_data.append({
            'question': sa.question,
            'user_answer': sa.selected_answer,
            'is_correct': sa.is_correct,
            'correct_answer': correct_answer,
        })

    return render(request, 'tests/result_detail.html', {
        'result': result,
        'student_name': student_name,
        'percent': percent,
        'questions_data': questions_data,
    })


# ──────────────────────────────────────────────
# 🗑️ УДАЛЕНИЕ РЕЗУЛЬТАТОВ
# ──────────────────────────────────────────────

@staff_member_required
def delete_result(request, result_id):
    """Удалить одну попытку"""
    result = get_object_or_404(Result, id=result_id)
    result.delete()
    messages.success(request, 'Попытка удалена.')
    return redirect('test_results', test_id=result.test.id)


@staff_member_required
def delete_test_results(request, test_id):
    """Удалить все результаты одного теста"""
    test = get_object_or_404(Test, id=test_id)
    Result.objects.filter(test=test).delete()
    messages.success(request, f'Все результаты теста «{test.title}» удалены.')
    return redirect('teacher_home')


@staff_member_required
def delete_all_results(request):
    """Только админ: удалить все результаты всех тестов"""
    if request.user.role != 'admin':
        messages.error(request, 'Только администратор может это сделать.')
        return redirect('teacher_home')

    Result.objects.all().delete()
    messages.success(request, 'Все результаты удалены.')
    return redirect('teacher_home')


# ──────────────────────────────────────────────
# 👥 Пользователи (админ)
# ──────────────────────────────────────────────
@staff_member_required
def users_list(request):
    if request.user.role != 'admin':
        return redirect('teacher_home')

    role_filter = request.GET.get('role', '')
    users = User.objects.all().exclude(username='admin')

    if role_filter in ['teacher', 'moderator']:
        users = users.filter(role=role_filter)

    return render(request, 'tests/users_list.html', {
        'users': users,
        'current_role': role_filter,
    })


@staff_member_required
def change_role(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'Доступ запрещён.')
        return redirect('teacher_home')

    user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role')
    if new_role in ['teacher', 'moderator']:
        user.role = new_role
        user.save()
        messages.success(request, f'Роль пользователя {user.username} изменена на {user.get_role_display()}')
    return redirect('users_list')


@staff_member_required
def delete_user(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'Доступ запрещён.')
        return redirect('teacher_home')

    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, 'Пользователь удалён.')
    return redirect('users_list')


# ──────────────────────────────────────────────
# 🧪 СОЗДАНИЕ И РЕДАКТИРОВАНИЕ ТЕСТОВ
# ──────────────────────────────────────────────
@staff_member_required
def create_test(request):
    if request.user.role not in ['admin', 'moderator']:
        messages.error(request, 'У вас нет прав на создание тестов.')
        return redirect('teacher_home')

    if request.method == 'POST':
        form = CreateTestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.author = request.user
            test.save()
            form.save_m2m()
            messages.success(request, f'Тест «{test.title}» успешно создан!')
            return redirect('add_questions', test_id=test.id)
    else:
        form = CreateTestForm()

    return render(request, 'tests/create_test.html', {
        'form': form,
        'all_tags': Tag.objects.all(),
    })


@staff_member_required
def add_questions(request, test_id):
    test = get_object_or_404(Test, id=test_id)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = Question.objects.create(
                test=test,
                text=form.cleaned_data['question_text']
            )
            num_answers = int(request.POST.get('num_answers', 4))
            correct_index = int(request.POST.get('correct_answer'))
            for i in range(1, num_answers + 1):
                answer_text = request.POST.get(f'answer_{i}')
                if answer_text:
                    Answer.objects.create(
                        question=question,
                        text=answer_text,
                        is_correct=(i == correct_index)
                    )
            messages.success(request, 'Вопрос добавлен!')
            if 'add_another' in request.POST:
                return redirect('add_questions', test_id=test.id)
            elif 'finish' in request.POST:
                return redirect('test_questions', test_id=test.id)
            return redirect('teacher_home')
    else:
        form = QuestionForm()

    return render(request, 'tests/add_questions.html', {'form': form, 'test': test})


@staff_member_required
def test_questions(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    questions = Question.objects.filter(test=test).prefetch_related('answer_set')
    return render(request, 'tests/test_questions.html', {
        'test': test,
        'questions': questions,
    })


@staff_member_required
def edit_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    if request.method == 'POST':
        test.title = request.POST.get('title')
        test.description = request.POST.get('description')
        test.save()
        tag_ids = request.POST.getlist('tags')
        test.tags.set(tag_ids)
        messages.success(request, f'Тест «{test.title}» успешно обновлён!')
        return redirect('test_questions', test_id=test.id)

    return render(request, 'tests/edit_test.html', {
        'test': test,
        'all_tags': Tag.objects.all(),
    })


@staff_member_required
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = question.answer_set.all()
    test = question.test

    if request.method == 'POST':
        question.text = request.POST.get('question_text')
        question.save()
        question.answer_set.all().delete()
        num_answers = int(request.POST.get('num_answers', 4))
        correct_index = int(request.POST.get('correct_answer'))
        for i in range(1, num_answers + 1):
            answer_text = request.POST.get(f'answer_{i}')
            if answer_text:
                Answer.objects.create(
                    question=question,
                    text=answer_text,
                    is_correct=(i == correct_index)
                )
        messages.success(request, 'Вопрос обновлён!')
        return redirect('test_questions', test_id=test.id)

    num_answers = answers.count()
    correct_index = None
    for i, ans in enumerate(answers, 1):
        if ans.is_correct:
            correct_index = i

    return render(request, 'tests/edit_question.html', {
        'question': question,
        'answers': answers,
        'num_answers': num_answers,
        'correct_index': correct_index,
        'test': test,
    })


@staff_member_required
def delete_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав на удаление тестов.')
        return redirect('teacher_home')
    test_title = test.title
    test.delete()
    messages.success(request, f'Тест «{test_title}» успешно удалён!')
    return redirect('teacher_home')


# ──────────────────────────────────────────────
# 🏷️ ТЕГИ
# ──────────────────────────────────────────────
@staff_member_required
def tags_list(request):
    return render(request, 'tests/tags_list.html', {'tags': Tag.objects.all()})


@staff_member_required
def tag_add(request):
    if request.user.role != 'admin':
        messages.error(request, 'Нет доступа')
        return redirect('teacher_home')

    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color')
        if not name:
            messages.error(request, 'Введите название тега')
        elif Tag.objects.filter(name=name).exists():
            messages.error(request, 'Такой тег уже есть')
        else:
            Tag.objects.create(name=name, color=color or '#e0e0e0')
            messages.success(request, f'Тег «{name}» создан!')
    return redirect('teacher_home')


@staff_member_required
def tag_edit(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag.name = request.POST.get('name')
        tag.color = request.POST.get('color')
        tag.save()
        messages.success(request, f'Тег «{tag.name}» обновлён!')
        return redirect('tags_list')
    return render(request, 'tests/tag_form.html', {'tag': tag})


@staff_member_required
def tag_delete(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    tag.delete()
    messages.success(request, 'Тег удалён!')
    return redirect('tags_list')


@staff_member_required
def tag_add_inline(request):
    if request.user.role != 'admin':
        return redirect('teacher_home')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color')
        if name:
            Tag.objects.get_or_create(name=name, defaults={'color': color or '#4CAF50'})
    return redirect('teacher_home')


# ──────────────────────────────────────────────
# 🔗 ИНВАЙТ-СИСТЕМА (МНОГОРАЗОВАЯ, 7 ДНЕЙ)
# ──────────────────────────────────────────────
def register_by_invite(request, code):
    try:
        invitation = Invitation.objects.get(code=code)
    except Invitation.DoesNotExist:
        return render(request, 'tests/invite_invalid.html', {
            'error': 'Недействительная ссылка.'
        })

    if invitation.expires_at and invitation.expires_at < timezone.now():
        return render(request, 'tests/invite_invalid.html', {
            'error': 'Срок действия ссылки истёк.'
        })

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = invitation.role
            user.save()
            login(request, user)
            messages.success(request, '✅ Вы успешно зарегистрированы и вошли в систему!')
            return redirect('teacher_home')
    else:
        form = RegisterForm()

    return render(request, 'tests/register_by_invite.html', {
        'form': form,
        'role': invitation.get_role_display(),
    })


@staff_member_required
def admin_panel(request):
    if request.user.role != 'admin':
        return redirect('teacher_home')

    if request.method == 'POST':
        role = request.POST.get('role')
        if role not in ['teacher', 'moderator']:
            messages.error(request, 'Недопустимая роль')
            return redirect('admin_panel')
        invitation = Invitation.objects.create(
            role=role,
            expires_at=timezone.now() + timedelta(days=7)
        )
        invite_url = request.build_absolute_uri(f'/register/invite/{invitation.code}/')
        messages.success(request, f'✅ Ссылка создана: {invite_url}')
        return redirect('admin_panel')

    invitations = Invitation.objects.all().order_by('-created_at')
    invitations_with_urls = []
    for inv in invitations:
        invitations_with_urls.append({
            'id': inv.id,
            'code': inv.code,
            'role': inv.role,
            'used': inv.used,
            'created_at': inv.created_at,
            'expires_at': inv.expires_at,
            'url': request.build_absolute_uri(f'/register/invite/{inv.code}/'),
        })

    # Счётчики
    total_students = (
        Result.objects
        .exclude(first_name='', last_name='')
        .values('first_name', 'last_name')
        .distinct()
        .count()
    )
    total_teachers = User.objects.filter(role='teacher').count()
    total_moderators = User.objects.filter(role='moderator').count()

    return render(request, 'tests/admin_panel.html', {
        'invitations': invitations_with_urls,
        'tags': Tag.objects.all(),
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_moderators': total_moderators,
        'now': timezone.now(),
    })

@staff_member_required
def change_role(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'Доступ запрещён.')
        return redirect('teacher_home')

    user = get_object_or_404(User, id=user_id)
    
    # Защита админов от смены роли
    if user.role == 'admin':
        messages.error(request, 'Нельзя изменить роль администратора.')
        return redirect('users_list')
    
    new_role = request.POST.get('role')
    if new_role in ['teacher', 'moderator']:
        user.role = new_role
        user.save()
        messages.success(request, f'Роль пользователя {user.username} изменена на {user.get_role_display()}')
    return redirect('users_list')

@staff_member_required
def delete_invite(request, invite_id):
    if request.user.role != 'admin':
        return redirect('teacher_home')
    invite = get_object_or_404(Invitation, id=invite_id)
    invite.delete()
    messages.success(request, 'Ссылка удалена')
    return redirect('admin_panel')