import os
import re
import sys
import django

# Настройка Django
sys.path.append('/Users/vladislavtakhtau/Desktop/breakout_english')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')
django.setup()

from bs4 import BeautifulSoup
from tests.models import Test, Question, Answer
from django.contrib.auth import get_user_model

User = get_user_model()

def parse_key_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    title_tag = soup.find('h1', id='title')
    test_title = title_tag.text.strip() if title_tag else os.path.basename(os.path.dirname(file_path))
    
    questions = []
    question_blocks = soup.find_all('table', class_='question-block')
    
    for block in question_blocks:
        question_td = block.find('td', width='100%')
        if not question_td:
            continue
        
        question_text = question_td.get_text(strip=True)
        question_text = re.sub(r'^\d+\.\s*', '', question_text)
        
        answer_div = block.find_next_sibling('div', class_='answer')
        if not answer_div:
            continue
        
        answers = []
        rows = answer_div.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                marker_cell = cells[1]
                marker = marker_cell.get_text(strip=True)
                answer_cell = cells[2]
                answer_text = answer_cell.get_text(strip=True)
                is_correct = '⚫' in marker or '●' in marker or marker == '●'
                
                if answer_text:
                    answers.append({'text': answer_text, 'is_correct': is_correct})
        
        if question_text and answers:
            questions.append({'text': question_text, 'answers': answers})
    
    return test_title, questions

def import_quiz_from_html(folder_path):
    html_file = os.path.join(folder_path, 'key.html')
    
    if not os.path.exists(html_file):
        print(f"❌ Файл key.html не найден в {folder_path}")
        return False
    
    print(f"📖 Парсим {html_file}...")
    
    try:
        test_title, questions = parse_key_html(html_file)
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        return False
    
    if not questions:
        print(f"❌ Не удалось найти вопросы в {html_file}")
        return False
    
    if Test.objects.filter(title=test_title).exists():
        print(f"⚠️ Тест '{test_title}' уже существует. Пропускаем.")
        return False
    
    # Получаем или создаём пользователя для автора
    author, _ = User.objects.get_or_create(
        username='import_bot',
        defaults={'is_active': True}
    )
    
    test = Test.objects.create(
        title=test_title,
        description=f'Импортирован из {os.path.basename(folder_path)}',
        author=author
    )
    
    print(f"\n📚 Создаём тест: {test_title}")
    print(f"📊 Найдено вопросов: {len(questions)}")
    
    for i, q_data in enumerate(questions, 1):
        question = Question.objects.create(test=test, text=q_data['text'])
        for a_data in q_data['answers']:
            Answer.objects.create(
                question=question,
                text=a_data['text'],
                is_correct=a_data['is_correct']
            )
        print(f"  ✅ {i}. {q_data['text'][:60]}...")
    
    print(f"\n✅ Импортирован тест '{test_title}' с {len(questions)} вопросами!")
    return True

if __name__ == '__main__':
    folder = '/Users/vladislavtakhtau/Desktop/breakout_english/output/А.1.1 Present simple _все глаголы_ - 2711909'
    import_quiz_from_html(folder)
