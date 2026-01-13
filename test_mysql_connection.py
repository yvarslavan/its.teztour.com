#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для проверки доступности MySQL сервера"""

import os
import socket
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env
env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)
else:
    print("❌ Файл .env не найден!")
    exit(1)

mysql_host = os.getenv('MYSQL_HOST')
mysql_port = int(os.getenv('MYSQL_PORT', '3306'))

print("🔍 Проверка доступности MySQL сервера:")
print(f"   Хост: {mysql_host}")
print(f"   Порт: {mysql_port}")
print()

# Проверка DNS
try:
    ip = socket.gethostbyname(mysql_host)
    print(f"✅ DNS резолвинг: {mysql_host} -> {ip}")
except socket.gaierror as e:
    print(f"❌ Ошибка DNS: {e}")
    print("\n💡 Решение: Проверьте интернет-соединение или VPN")
    exit(1)

# Проверка доступности порта
print(f"🔌 Проверка подключения к {mysql_host}:{mysql_port}...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((mysql_host, mysql_port))
    sock.close()

    if result == 0:
        print(f"✅ Порт {mysql_port} доступен!")
    else:
        print(f"❌ Порт {mysql_port} недоступен (код ошибки: {result})")
        print("\n💡 Возможные решения:")
        print("   1. Проверьте VPN подключение к корпоративной сети")
        print("   2. Используйте SSH туннель для доступа к серверу")
        print("   3. Убедитесь, что сервер MySQL разрешает внешние подключения")
except socket.timeout:
    print(f"❌ Таймаут подключения к {mysql_host}:{mysql_port}")
    print("\n💡 Это означает, что сервер недоступен с вашей машины.")
    print("   Возможные причины:")
    print("   - Сервер находится во внутренней сети компании")
    print("   - Требуется VPN подключение")
    print("   - Сервер блокирует внешние подключения")
except Exception as e:
    print(f"❌ Ошибка: {e}")

