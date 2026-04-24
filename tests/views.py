from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required
from .forms import StudentLoginForm, TeacherLoginForm, CreateTestForm, QuestionForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Test, Question, Answer, Result, StudentAnswer, Tag
from django.core.paginator import Paginator
from .models import Invitation
from django.utils import timezone
from accounts.forms import RegisterForm
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model 

def test_list(request):
    # Очищаем старые сообщения, чтобы не висели
    storage = messages.get_messages(request)
    storage.used = True
    
    tests = Test.objects.all()
    return render(request, 'tests/test_list.html', {'tests': tests})
    
def test_detail(request, test_id):
    # Для гостевого режима (ученик)
    first_name = request.session.get('student_first_name', '')
    last_name = request.session.get('student_last_name', '')
    if not first_name and not last_name:
        return redirect('test_entry', test_id=test_id)
    
    test = get_object_or_404(Test, id=test_id)
    questions = Question.objects.filter(test=test)
    
    
    # Готовим вопросы для отображения (для всех)
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

def submit_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    
    questions = Question.objects.filter(test=test)
    score = 0
    total = questions.count()
    
    questions_details = []
    
    for question in questions:
        answer_key = f'question_{question.id}'
        answer_id = request.POST.get(answer_key)
        
        user_answer = None
        is_correct = False
        correct_answer = None
        
        if answer_id:
            try:
                user_answer = Answer.objects.get(id=answer_id)
                if user_answer.is_correct:
                    is_correct = True
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
    
    # Сохраняем результат
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
    
    # Сохраняем ответы ученика
    for qd in questions_details:
        question = qd['question']
        user_answer = qd['user_answer']
        is_correct = qd['is_correct']
        
        StudentAnswer.objects.create(
            result=result,
            question=question,
            selected_answer=user_answer,
            is_correct=is_correct
        )
    
    messages.success(request, f'✅ Вы набрали {score} из {total} баллов!')
    
        # Очищаем сессию
    request.session.pop('questions_details', None)
    
    # Обновляем дату последней активности теста
    test.last_activity = timezone.now()
    test.save(update_fields=['last_activity'])
    
    return redirect('test_result', result_id=result.id)

def test_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)
    
    # Проверка прав
    if result.student and result.student != request.user:
        messages.error(request, 'Это не ваш результат!')
        return redirect('test_list')
    
    percent = int(result.score / result.total * 100) if result.total > 0 else 0
    
    # Имя для отображения
    if result.first_name and result.last_name:
        student_name = f"{result.first_name} {result.last_name}"
    elif result.student:
        student_name = result.student.username
    else:
        student_name = "Аноним"
    
    # Получаем ответы из БД
    student_answers = result.answers.all().select_related('question', 'selected_answer')
    questions_details = []
    for sa in student_answers:
        correct_answer = Answer.objects.filter(question=sa.question, is_correct=True).first()
        all_answers = Answer.objects.filter(question=sa.question)
        
        questions_details.append({
            'question_text': sa.question.text,
            'user_answer_id': sa.selected_answer.id if sa.selected_answer else None,  # ← добавил
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
    
def test_entry(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student_form = StudentLoginForm()
    teacher_form = TeacherLoginForm()
    
    if request.method == 'POST':
        if 'student_login' in request.POST:
            student_form = StudentLoginForm(request.POST)
            if student_form.is_valid():
                first_name = student_form.cleaned_data['first_name']
                last_name = student_form.cleaned_data['last_name']
                request.session['student_first_name'] = first_name
                request.session['student_last_name'] = last_name
                return redirect('test_detail', test_id=test_id)
        
        elif 'teacher_login' in request.POST:
            teacher_form = TeacherLoginForm(request.POST)
            if teacher_form.is_valid():
                username = teacher_form.cleaned_data['username']
                password = teacher_form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)
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
    
@staff_member_required
def test_results(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    results = Result.objects.filter(test=test).order_by('-completed_at')
    
    # Группируем по ученикам
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
    
def register_by_invite(request, code):
    try:
        invitation = Invitation.objects.get(code=code, used=False)
    except Invitation.DoesNotExist:
        return render(request, 'tests/invite_invalid.html', {'error': 'Недействительная или уже использованная ссылка.'})
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = invitation.role
            user.save()
            invitation.used = True
            invitation.save()
            login(request, user)
            messages.success(request, 'Вы успешно зарегистрированы и вошли в систему!')
            return redirect('teacher_home')
    else:
        form = RegisterForm()
    
    return render(request, 'tests/register_by_invite.html', {'form': form, 'role': invitation.get_role_display()})
        
@staff_member_required
def admin_panel(request):
    if request.user.role != 'admin':
        return redirect('teacher_home')
    
    if request.method == 'POST':
        role = request.POST.get('role')
        invitation = Invitation.objects.create(role=role)
        invite_link = request.build_absolute_uri(f'/register/invite/{invitation.code}/')
        messages.success(request, f'Ссылка-приглашение создана: {invite_link}')
        return redirect('admin_panel')
    
    invitations = Invitation.objects.all().order_by('-created_at')
    return render(request, 'tests/admin_panel.html', {'invitations': invitations})
        
@staff_member_required
def create_test(request):
    if request.method == 'POST':
        form = CreateTestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.author = request.user
            test.save()
            form.save_m2m()  # сохраняем выбранные теги
            messages.success(request, f'Тест "{test.title}" успешно создан!')
            return redirect('add_questions', test_id=test.id)
    else:
        form = CreateTestForm()
    
    return render(request, 'tests/create_test.html', {
        'form': form,
        'all_tags': Tag.objects.all(),  # ← обязательно
    })
    
@staff_member_required
def teacher_home(request):
    tests = Test.objects.all().order_by('-last_activity')
    
    # Поиск по названию
    search_query = request.GET.get('search', '')
    if search_query:
        tests = tests.filter(title__icontains=search_query)
    
    # Фильтр по тегам
    tag_filter = request.GET.get('tag', '')
    if tag_filter:
        tests = tests.filter(tags__name=tag_filter)
    
    # Пагинация (20 тестов на страницу)
    paginator = Paginator(tests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    
    return render(request, 'tests/teacher_home.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_tests': tests.count(),
        'all_tags': Tag.objects.all(),  # ← обязательно
        'current_tag': tag_filter,
    })

@staff_member_required
def test_questions(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    questions = Question.objects.filter(test=test).prefetch_related('answer_set')
    
    return render(request, 'tests/test_questions.html', {
        'test': test,
        'questions': questions,
    })    
    
@staff_member_required
def add_questions(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            # Создаём вопрос
            question = Question.objects.create(
                test=test,
                text=form.cleaned_data['question_text']
            )
            
            # Получаем количество ответов (из POST или по умолчанию 4)
            num_answers = int(request.POST.get('num_answers', 4))
            
            # Создаём ответы
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
            
            # Если нажата кнопка "Добавить ещё"
            if 'add_another' in request.POST:
                return redirect('add_questions', test_id=test.id)
            elif 'finish' in request.POST:
                return redirect('test_questions', test_id=test.id)
            else:
                return redirect('teacher_home')
    else:
        form = QuestionForm()
    
    return render(request, 'tests/add_questions.html', {
        'form': form,
        'test': test,
    })

@staff_member_required
def edit_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    
    if request.method == 'POST':
        test.title = request.POST.get('title')
        test.description = request.POST.get('description')
        test.save()
        # Сохраняем теги
        tag_ids = request.POST.getlist('tags')
        test.tags.set(tag_ids)
        messages.success(request, f'Тест "{test.title}" успешно обновлён!')
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
        # Обновляем текст вопроса
        question.text = request.POST.get('question_text')
        question.save()
        
        # Удаляем старые ответы
        question.answer_set.all().delete()
        
        # Создаём новые ответы
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
    
    # GET: показываем форму с текущими данными
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
def result_detail(request, result_id):
    result = get_object_or_404(Result, id=result_id)
    
    # Имя ученика
    if result.first_name and result.last_name:
        student_name = f"{result.first_name} {result.last_name}"
    elif result.student:
        student_name = result.student.username
    else:
        student_name = "Аноним"
    
    percent = int(result.score / result.total * 100) if result.total > 0 else 0
    
    # Получаем ответы ученика
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
    
@staff_member_required
def tags_list(request):
    tags = Tag.objects.all()
    return render(request, 'tests/tags_list.html', {'tags': tags})

@staff_member_required
def tag_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color')
        Tag.objects.create(name=name, color=color)
        messages.success(request, f'Тег "{name}" создан!')
        return redirect('tags_list')
    return render(request, 'tests/tag_form.html', {'tag': None})

@staff_member_required
def tag_edit(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag.name = request.POST.get('name')
        tag.color = request.POST.get('color')
        tag.save()
        messages.success(request, f'Тег "{tag.name}" обновлён!')
        return redirect('tags_list')
    return render(request, 'tests/tag_form.html', {'tag': tag})

@staff_member_required
def tag_delete(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    tag.delete()
    messages.success(request, 'Тег удалён!')
    return redirect('tags_list')
    
@staff_member_required
def delete_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав на удаление тестов.')
        return redirect('teacher_home')
    
    test_title = test.title
    test.delete()
    messages.success(request, f'Тест "{test_title}" успешно удалён!')
    return redirect('teacher_home')
    
@staff_member_required
def users_list(request):
    if request.user.role != 'admin':
        return redirect('teacher_home')
    
    User = get_user_model()  # получаем модель пользователя
    users = User.objects.all().exclude(username='admin')
    return render(request, 'tests/users_list.html', {'users': users})
    
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