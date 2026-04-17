import os
import sys
import django

sys.path.append('/Users/vladislavtakhtau/Desktop/breakout_english')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')
django.setup()

from import_from_html import import_quiz_from_html

# Путь к папке с тестами
output_dir = '/Users/vladislavtakhtau/Desktop/breakout_english/output'

# Получаем список всех папок
folders = [f for f in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, f))]

print(f"📁 Найдено папок: {len(folders)}")
print("=" * 50)

success_count = 0
skip_count = 0
error_count = 0

for folder_name in folders:
    folder_path = os.path.join(output_dir, folder_name)
    print(f"\n📂 Обрабатываем: {folder_name}")
    
    try:
        result = import_quiz_from_html(folder_path)
        if result:
            success_count += 1
        else:
            skip_count += 1
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        error_count += 1

print("\n" + "=" * 50)
print(f"✅ Успешно импортировано: {success_count}")
print(f"⏭️ Пропущено (уже есть): {skip_count}")
print(f"❌ Ошибок: {error_count}")
print("=" * 50)
