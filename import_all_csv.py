import os
import sys
import re
import django

sys.path.append('/Users/vladislavtakhtau/Desktop/breakout_english')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')
django.setup()

from tests.models import Test, Question, Answer
from django.contrib.auth import get_user_model

User = get_user_model()

def import_from_csv(csv_file_path, test_title):
    """Импортирует вопросы из CSV-файла в новый тест"""
    
    # Проверяем, существует ли уже такой тест
    if Test.objects.filter(title=test_title).exists():
        print(f"⚠️ Тест '{test_title}' уже существует. Пропускаем.")
        return False
    
    # Получаем или создаём автора (администратора)
    author, _ = User.objects.get_or_create(
        username='admin',
        defaults={'is_staff': True, 'is_superuser': True}
    )
    
    # Создаём тест
    test = Test.objects.create(
        title=test_title,
        description=f'Импортирован из {os.path.basename(csv_file_path)}',
        author=author
    )
    
    print(f"\n📚 Создаём тест: {test_title}")
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_question = None
    question_text = None
    answers = []
    questions_added = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Если строка содержит вопрос (начинается с <p> и не с , или *)
        if line.startswith('<p>') and not line.startswith(',') and not line.startswith('*'):
            # Сохраняем предыдущий вопрос
            if current_question and answers:
                q = Question.objects.create(test=test, text=question_text)
                for ans_text, is_correct in answers:
                    Answer.objects.create(
                        question=q,
                        text=ans_text,
                        is_correct=is_correct
                    )
                questions_added += 1
            
            # Начинаем новый вопрос
            question_text = line.replace('<p>', '').replace('</p>', '')
            answers = []
            current_question = True
        
        # Если это ответ
        elif current_question and (line.startswith(',') or line.startswith('*')):
            is_correct = line.startswith('*')
            # Извлекаем текст ответа из HTML
            if '<p>' in line:
                answer_text = line.split('<p>', 1)[1].rsplit('</p>', 1)[0]
            else:
                answer_text = line.lstrip(',*')
            answers.append((answer_text, is_correct))
    
    # Сохраняем последний вопрос
    if current_question and answers:
        q = Question.objects.create(test=test, text=question_text)
        for ans_text, is_correct in answers:
            Answer.objects.create(
                question=q,
                text=ans_text,
                is_correct=is_correct
            )
        questions_added += 1
    
    print(f"✅ Импортировано {questions_added} вопросов в тест '{test_title}'")
    return True

def import_all_quizzes():
    """Импортирует все тесты из папки output"""
    output_dir = '/Users/vladislavtakhtau/Desktop/breakout_english/output'
    
    # Получаем список всех папок
    folders = [f for f in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, f))]
    
    print(f"📁 Найдено папок: {len(folders)}")
    print("=" * 50)
    
    success_count = 0
    skip_count = 0
    
    for folder_name in folders:
        folder_path = os.path.join(output_dir, folder_name)
        questions_file = os.path.join(folder_path, 'questions.csv')
        
        if not os.path.exists(questions_file):
            print(f"⚠️ Нет questions.csv в {folder_name}, пропускаем.")
            skip_count += 1
            continue
        
        # Название теста = имя папки без цифр в конце
        test_title = re.sub(r'-\s*\d+$', '', folder_name).strip()
        
        print(f"\n📂 Обрабатываем: {folder_name}")
        result = import_from_csv(questions_file, test_title)
        if result:
            success_count += 1
        else:
            skip_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Успешно импортировано: {success_count}")
    print(f"⏭️ Пропущено (уже есть или нет файла): {skip_count}")
    print("=" * 50)

if __name__ == '__main__':
    import_all_quizzes()
