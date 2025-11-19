#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для настройки окружения разработки или продакшена"""

import shutil
import sys
from pathlib import Path

def setup_environment(env_type="development"):
    """Настройка окружения: development или production"""
    
    base_dir = Path(__file__).resolve().parent
    
    if env_type == "production":
        source_file = base_dir / ".env.production"
        target_file = base_dir / ".env"
        env_name = "продакшена"
    else:
        source_file = base_dir / ".env.development"
        target_file = base_dir / ".env"
        env_name = "разработки"
    
    if not source_file.exists():
        print(f"❌ Файл {source_file.name} не найден!")
        print(f"💡 Создайте файл {source_file.name} с настройками для {env_name}")
        return False
    
    # Копируем файл окружения в .env
    shutil.copy2(source_file, target_file)
    print(f"✅ Настроено окружение {env_name}")
    print(f"   {source_file.name} → .env")
    return True

if __name__ == "__main__":
    env_type = sys.argv[1] if len(sys.argv) > 1 else "development"
    
    if env_type not in ["development", "production"]:
        print("❌ Неверный тип окружения. Используйте: development или production")
        sys.exit(1)
    
    if setup_environment(env_type):
        print()
        print("🚀 Теперь можно запустить приложение:")
        print("   python3 app.py")
    else:
        sys.exit(1)

