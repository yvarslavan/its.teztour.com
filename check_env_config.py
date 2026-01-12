#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для проверки и исправления конфигурации .env"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)
    print("✅ Файл .env найден и загружен")
else:
    print("❌ Файл .env не найден!")
    exit(1)

print("\n" + "=" * 60)
print("ТЕКУЩИЕ НАСТРОЙКИ MySQL:")
print("=" * 60)

mysql_vars = {
    'MYSQL_HOST': os.getenv('MYSQL_HOST'),
    'MYSQL_DATABASE': os.getenv('MYSQL_DATABASE'),
    'MYSQL_USER': os.getenv('MYSQL_USER'),
    'MYSQL_PASSWORD': '***' if os.getenv('MYSQL_PASSWORD') else None,
}

mysql_quality_vars = {
    'MYSQL_QUALITY_HOST': os.getenv('MYSQL_QUALITY_HOST'),
    'MYSQL_QUALITY_DATABASE': os.getenv('MYSQL_QUALITY_DATABASE'),
    'MYSQL_QUALITY_USER': os.getenv('MYSQL_QUALITY_USER'),
    'MYSQL_QUALITY_PASSWORD': '***' if os.getenv('MYSQL_QUALITY_PASSWORD') else None,
}

for key, value in mysql_vars.items():
    status = "✅" if value else "❌"
    print(f"{status} {key}: {value}")

print("\n" + "=" * 60)
print("НАСТРОЙКИ MySQL Quality:")
print("=" * 60)

for key, value in mysql_quality_vars.items():
    status = "✅" if value else "❌"
    print(f"{status} {key}: {value}")

# Проверяем проблемный хост
mysql_host = os.getenv('MYSQL_HOST')
if mysql_host == 'helpdesk.teztour.com':
    print("\n" + "⚠️" * 30)
    print("ПРОБЛЕМА ОБНАРУЖЕНА!")
    print("⚠️" * 30)
    print(f"\nХост MySQL указан как: {mysql_host}")
    print("Этот хост недоступен (таймаут в логах).")
    print("\nВозможные решения:")
    print("1. Если это внутренний сервер компании - проверьте VPN подключение")
    print("2. Если нужен другой хост - укажите правильный MYSQL_HOST в .env")
    print("3. Если нужен локальный MySQL - используйте 'localhost' или '127.0.0.1'")
    print("\nДля разработки можно использовать:")
    print("  MYSQL_HOST=localhost")
    print("  или")
    print("  MYSQL_HOST=127.0.0.1")

