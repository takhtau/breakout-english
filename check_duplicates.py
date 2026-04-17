import os
import sys
import django

sys.path.append('/Users/vladislavtakhtau/Desktop/breakout_english')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')
django.setup()

from tests.models import Test, Question, Answer
from collections import defaultdict

def get_test_questions(test):
    """Возвращает набор вопросов для теста"""
    questions = []
    for q in Question.objects.filter(test=test).order_by('id'):
        answers = Answer.objects.filter(question=q).order_by('id')
        questions.append({
            'text': q.text,
            'answers': [(a.text, a.is_correct) for a in answers]
        })
    return questions

def compare_tests(test1, test2):
    """Сравнивает два теста"""
    q1 = get_test_questions(test1)
    q2 = get_test_questions(test2)
    
    if len(q1) != len(q2):
        return f"❌ Разное количество вопросов: {len(q1)} vs {len(q2)}"
    
    for i, (q1_data, q2_data) in enumerate(zip(q1, q2)):
        if q1_data['text'] != q2_data['text']:
            return f"❌ Вопрос {i+1} отличается: '{q1_data['text'][:50]}...' vs '{q2_data['text'][:50]}...'"
        
        if len(q1_data['answers']) != len(q2_data['answers']):
            return f"❌ Вопрос {i+1}: разное количество ответов"
        
        for j, (a1, a2) in enumerate(zip(q1_data['answers'], q2_data['answers'])):
            if a1 != a2:
                return f"❌ Вопрос {i+1}, ответ {j+1} отличается"
    
    return "✅ Тесты идентичны"

# Находим тесты с одинаковыми названиями
title_groups = defaultdict(list)
for test in Test.objects.all():
    title_groups[test.title].append(test)

print("=" * 60)
print("Проверка дубликатов по названию")
print("=" * 60)

duplicate_count = 0
for title, tests in title_groups.items():
    if len(tests) > 1:
        duplicate_count += 1
        print(f"\n📚 Тест: {title}")
        print(f"   Количество копий: {len(tests)}")
        print(f"   ID: {[t.id for t in tests]}")
        
        # Сравниваем первую и вторую копии
        if len(tests) >= 2:
            result = compare_tests(tests[0], tests[1])
            print(f"   Сравнение ID {tests[0].id} и {tests[1].id}: {result}")

print("\n" + "=" * 60)
print(f"Всего тестов: {Test.objects.count()}")
print(f"Уникальных названий: {len(title_groups)}")
print(f"Групп с дубликатами: {duplicate_count}")
print("=" * 60)
