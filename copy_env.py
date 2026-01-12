#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для копирования .env.backup в .env"""

import shutil
import os
from pathlib import Path

# Пробуем разные варианты имени файла
possible_backup_files = ['.env.backup', 'env.backup', '.env.backup.bak', 'env.backup.bak']
env_file = Path('.env')

found = False
for backup_name in possible_backup_files:
    backup_file = Path(backup_name)
    if backup_file.exists():
        print(f"📂 Найден файл: {backup_file}")
        # Читаем содержимое
        with open(backup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Записываем в .env
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Файл {backup_file} успешно скопирован в {env_file}")
        print(f"📄 Содержимое файла {env_file}:")
        print("=" * 60)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("=" * 60)
        found = True
        break

if not found:
    print("❌ Файл резервной копии не найден!")
    print("🔍 Искали файлы:")
    for name in possible_backup_files:
        print(f"   - {name}")
    print("\n💡 Попробуйте указать точное имя файла или путь к нему.")

