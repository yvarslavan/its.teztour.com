#!/usr/bin/env python3
import os
import re
import glob
import argparse
from pathlib import Path

def list_files_to_delete(base_dir='.'):
    """Находит файлы, которые нужно удалить"""
    files_to_delete = set()  # Используем множество вместо списка для предотвращения дубликатов

    # Директории, которые следует исключить из поиска
    excluded_dirs = [
        '.git',
        '.vscode',
        '__pycache__',
        'venv',
        'env',
        'node_modules',
        '.cursor'
    ]

    # Специфичные файлы, которые нужно исключить (шаблоны для регулярного выражения)
    excluded_files_patterns = [
        r'.*package.*\.json',  # Исключаем package.json и package-lock.json
        r'.*requirements\.txt',  # Исключаем requirements.txt
        r'.*config\.ini',  # Исключаем конфигурационные файлы
        r'.*\.env',  # Исключаем .env файлы
        r'.*\.gitignore',  # Исключаем .gitignore
    ]

    # Компилируем шаблоны для исключаемых файлов для более быстрой проверки
    excluded_patterns_compiled = [re.compile(pattern) for pattern in excluded_files_patterns]

    # Рекурсивный проход по файлам
    for root, dirs, files in os.walk(base_dir):
        # Исключаем директории, которые не нужно сканировать
        dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith('.')]

        for filename in files:
            filepath = os.path.join(root, filename)

            # Проверяем, не соответствует ли файл шаблонам для исключения
            should_exclude = any(pattern.match(filename) for pattern in excluded_patterns_compiled)
            if should_exclude:
                continue

            # HTML файлы с префиксом "test", "demo_", "sample_"
            if (filename.startswith(('test', 'demo_', 'sample_')) and
                filename.endswith(('.html', '.htm', '.xhtml'))):
                files_to_delete.add(filepath)

            # JS-файлы с расширениями, указывающими на резервные копии
            if filename.endswith(('.js.bak', '.js.old', '.js.backup', '.js.tmp')) or re.match(r'.*\.js\.v\d+$', filename):
                files_to_delete.add(filepath)

            # Python файлы с префиксом "test" (исключая тесты в стандартной директории tests)
            if (filename.startswith(('test_', 'test-')) and
                filename.endswith('.py') and
                not any(d == 'tests' for d in Path(filepath).parts)):
                files_to_delete.add(filepath)

            # Другие распространенные форматы резервных копий
            if any(filename.endswith(ext) for ext in ('.bak', '.backup', '.old', '.tmp', '.temp', '~')):
                files_to_delete.add(filepath)

            # Файлы с указанием версий в имени
            if re.match(r'.*\.(v|V)\d+$', filename) and not filename.startswith('.'):
                files_to_delete.add(filepath)

            # Другие известные временные файлы
            if filename.endswith(('.swp', '.swo', '.pyc', '.pyo')):
                files_to_delete.add(filepath)

    return sorted(list(files_to_delete))  # Преобразуем обратно в отсортированный список

def delete_files(files_list, dry_run=True):
    """Удаляет файлы из списка"""
    deleted_count = 0

    for filepath in files_list:
        if dry_run:
            print(f"[СИМУЛЯЦИЯ] Удаляется: {filepath}")
        else:
            try:
                os.remove(filepath)
                deleted_count += 1
                print(f"Удален: {filepath}")
            except OSError as e:
                print(f"Ошибка при удалении {filepath}: {e}")

    return deleted_count

def print_file_groups(files_to_delete):
    """Выводит список файлов, сгруппированных по типам"""
    # Группируем файлы по типам для удобства просмотра
    html_test_files = [f for f in files_to_delete if any(f.endswith(ext) for ext in ('.html', '.htm', '.xhtml'))]
    js_backup_files = [f for f in files_to_delete if '.js.' in f]
    python_test_files = [f for f in files_to_delete if f.endswith('.py')]
    other_backup_files = [f for f in files_to_delete
                        if f not in html_test_files
                        and f not in js_backup_files
                        and f not in python_test_files]

    # Выводим список файлов по категориям
    print(f"Найдено {len(files_to_delete)} файлов для удаления:")

    if html_test_files:
        print(f"\nHTML тестовые файлы ({len(html_test_files)}):")
        for file in html_test_files:
            print(f" - {file}")

    if js_backup_files:
        print(f"\nРезервные копии JS-файлов ({len(js_backup_files)}):")
        for file in js_backup_files:
            print(f" - {file}")

    if python_test_files:
        print(f"\nPython тестовые файлы ({len(python_test_files)}):")
        for file in python_test_files:
            print(f" - {file}")

    if other_backup_files:
        print(f"\nПрочие резервные и временные файлы ({len(other_backup_files)}):")
        for file in other_backup_files:
            print(f" - {file}")

def parse_arguments():
    """Обрабатывает аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description='Скрипт для очистки проекта от тестовых и резервных файлов.'
    )
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Автоматически подтверждать удаление без запроса (неинтерактивный режим)'
    )
    parser.add_argument(
        '-d', '--directory',
        default='.',
        help='Базовая директория для поиска файлов (по умолчанию: текущая директория)'
    )
    parser.add_argument(
        '--no-dry-run',
        action='store_true',
        help='Пропустить режим симуляции и сразу выполнить удаление (работает только с --yes)'
    )
    parser.add_argument(
        '--include-test-py',
        action='store_true',
        help='Включить тестовые Python-файлы (test_*.py) в список удаляемых файлов'
    )

    return parser.parse_args()

def main():
    # Получаем аргументы командной строки
    args = parse_arguments()
    base_dir = os.path.abspath(args.directory)

    print(f"Поиск файлов для удаления в: {base_dir}")

    # Получаем список файлов для удаления
    files_to_delete = list_files_to_delete(base_dir)

    # Если не включаем тестовые Python-файлы, удаляем их из списка
    if not args.include_test_py:
        files_to_delete = [f for f in files_to_delete
                          if not (f.endswith('.py') and (Path(f).name.startswith('test_') or Path(f).name.startswith('test-')))]

    if not files_to_delete:
        print("Файлы для удаления не найдены.")
        return

    # Выводим сгруппированный список файлов
    print_file_groups(files_to_delete)

    # Режим симуляции (если не указан флаг --no-dry-run)
    if not args.no_dry_run:
        print("\n=== Симуляция удаления (без реального удаления) ===")
        delete_files(files_to_delete, dry_run=True)

    # Определяем, нужно ли запрашивать подтверждение
    if args.yes:
        # Автоматический режим без запроса
        print("\n=== Выполняется удаление файлов (автоматический режим) ===")
        deleted_count = delete_files(files_to_delete, dry_run=False)
        print(f"\nУдалено {deleted_count} из {len(files_to_delete)} файлов")
    else:
        # Интерактивный режим с запросом подтверждения
        confirm = input("\nВы действительно хотите удалить эти файлы? (y/n): ")
        if confirm.lower() == "y":
            print("\n=== Выполняется удаление файлов ===")
            deleted_count = delete_files(files_to_delete, dry_run=False)
            print(f"\nУдалено {deleted_count} из {len(files_to_delete)} файлов")
        else:
            print("Операция отменена.")

if __name__ == "__main__":
    main()
