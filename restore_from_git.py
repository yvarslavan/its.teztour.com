#!/usr/bin/env python3
"""
Восстановление всех файлов из git для исправления синтаксических ошибок
"""

import os
import subprocess
from pathlib import Path

print("🔧 Восстановление файлов из git...")

# Список файлов для восстановления
files_to_restore = [
    'blog/__init__.py',
    'blog/user/forms.py',
    'blog/user/routes.py',
    'blog/templates/login.html'
]

for file_path in files_to_restore:
    path = Path(file_path)
    if path.exists():
        # Восстанавливаем файл из git
        result = subprocess.run(
            ["git", "checkout", "HEAD", "--", file_path],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        if result.returncode == 0:
            print(f"✅ Файл {file_path} восстановлен из git")
        else:
            print(f"❌ Ошибка восстановления {file_path}: {result.stderr}")
    else:
        print(f"❌ Файл не найден: {file_path}")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
print("\n💡 Если все еще есть ошибки, попробуйте:")
print("1. git reset --hard HEAD (полный сброс к последнему коммиту)")
print("2. git clean -fd (удаление неотслеживаемых файлов)")
print("3. git pull (получение последних изменений)")
