from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required
from .forms import StudentLoginForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Test, Question, Answer, Result

def test_list(request):
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
    
    # Проверяем, проходил ли пользователь этот тест (только для авторизованных)
    if request.user.is_authenticated:
        existing_result = Result.objects.filter(student=request.user, test=test).first()
        if existing_result:
            print(f"=== DEBUG: User {request.user.username} already took test, score: {existing_result.score}/{existing_result.total} ===")
            messages.info(request, f'Вы уже проходили этот тест. Ваш результат: {existing_result.score} из {existing_result.total}')
            return redirect('test_list')
    
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
    
    messages.success(request, f'✅ Вы набрали {score} из {total} баллов!')
    
    # Сохраняем детали вопросов в сессию
    request.session['questions_details'] = [
        {
            'question_text': qd['question'].text,
            'user_answer_id': qd['user_answer'].id if qd['user_answer'] else None,
            'user_answer_text': qd['user_answer'].text if qd['user_answer'] else '(не выбран)',
            'is_correct': qd['is_correct'],
            'correct_answer_text': qd['correct_answer'].text if qd['correct_answer'] else '',
            'all_answers': [{'id': a.id, 'text': a.text, 'is_correct': a.is_correct} for a in qd['all_answers']]
        }
        for qd in questions_details
    ]
    
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
    
    # Получаем детали вопросов из сессии
    questions_details = request.session.get('questions_details', [])
    
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
    
    if request.method == 'POST':
        student_form = StudentLoginForm(request.POST)
        if student_form.is_valid():
            first_name = student_form.cleaned_data['first_name']
            last_name = student_form.cleaned_data['last_name']
            request.session['student_first_name'] = first_name
            request.session['student_last_name'] = last_name
            return redirect('test_detail', test_id=test_id)
    
    return render(request, 'tests/test_entry.html', {
        'test': test,
        'student_form': student_form,
    })

def test_results(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    results = Result.objects.filter(test=test).order_by('-completed_at')
    
    results_data = []
    for r in results:
        if r.first_name and r.last_name:
            student_name = f"{r.first_name} {r.last_name}"
        elif r.student:
            student_name = r.student.username
        else:
            student_name = "Аноним"
        
        results_data.append({
            'student_name': student_name,
            'score': r.score,
            'total': r.total,
            'percent': int(r.score / r.total * 100) if r.total > 0 else 0,
            'completed_at': r.completed_at,
        })
    
    return render(request, 'tests/test_results.html', {
        'test': test,
        'results': results_data,
    })

@staff_member_required
def teacher_home(request):
    tests = Test.objects.all().order_by('-created_at')
    return render(request, 'tests/teacher_home.html', {'tests': tests})