import os
import sys
import django

sys.path.append('/Users/vladislavtakhtau/Desktop/breakout_english')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')
django.setup()

from import_from_html import import_quiz_from_html

# Папка с проектом
base_dir = '/Users/vladislavtakhtau/Desktop/breakout_english'

# Находим все папки, начинающиеся с "output"
output_folders = []
for item in os.listdir(base_dir):
    item_path = os.path.join(base_dir, item)
    if os.path.isdir(item_path) and item.startswith('output'):
        output_folders.append(item_path)

print(f"📁 Найдено папок output: {len(output_folders)}")
print("=" * 60)

total_success = 0
total_skip = 0
total_errors = 0

for folder in output_folders:
    print(f"\n📂 Обрабатываем папку: {os.path.basename(folder)}")
    
    # Проходим по всем подпапкам
    try:
        subfolders = [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]
    except Exception as e:
        print(f"  ❌ Не удалось прочитать папку: {e}")
        continue
    
    for sub in subfolders:
        sub_path = os.path.join(folder, sub)
        key_file = os.path.join(sub_path, 'key.html')
        
        # Проверяем, есть ли key.html
        if not os.path.exists(key_file):
            continue
        
        print(f"  📚 Импортируем: {sub}")
        try:
            result = import_quiz_from_html(sub_path)
            if result:
                total_success += 1
            else:
                total_skip += 1
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            total_errors += 1

print("\n" + "=" * 60)
print(f"✅ Успешно импортировано: {total_success}")
print(f"⏭️ Пропущено (уже есть): {total_skip}")
print(f"❌ Ошибок: {total_errors}")
print("=" * 60)
