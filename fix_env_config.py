#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для исправления конфигурации .env - замена недоступного хоста"""

import shutil
from pathlib import Path
import re

env_file = Path('.env')
backup_file = Path('.env.backup')

# Сначала проверяем, есть ли .env.backup
if backup_file.exists():
    print(f"📂 Найден файл резервной копии: {backup_file}")
    
    # Читаем содержимое .env.backup
    with open(backup_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, есть ли проблемный хост
    if 'helpdesk.teztour.com' in content:
        print("⚠️ Обнаружен проблемный хост 'helpdesk.teztour.com'")
        print("\nВарианты решения:")
        print("1. Если это внутренний сервер - убедитесь, что VPN подключен")
        print("2. Если нужен другой хост - укажите его ниже")
        print("3. Для локальной разработки используйте 'localhost'")
        
        # Создаем резервную копию текущего .env если он существует
        if env_file.exists():
            env_backup = Path('.env.before_fix')
            shutil.copy2(env_file, env_backup)
            print(f"\n✅ Создана резервная копия текущего .env в {env_backup}")
        
        # Копируем из .env.backup в .env
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Файл {backup_file} скопирован в {env_file}")
        print("\n⚠️ ВАЖНО: Проверьте настройки MYSQL_HOST в файле .env")
        print("Если хост 'helpdesk.teztour.com' недоступен, замените его на доступный.")
    else:
        # Просто копируем, если проблемного хоста нет
        if env_file.exists():
            env_backup = Path('.env.before_fix')
            shutil.copy2(env_file, env_backup)
            print(f"✅ Создана резервная копия текущего .env в {env_backup}")
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Файл {backup_file} скопирован в {env_file}")
else:
    print(f"❌ Файл {backup_file} не найден!")
    print("Убедитесь, что файл существует и имеет правильное имя.")

