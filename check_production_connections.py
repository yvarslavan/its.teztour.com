#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностический скрипт для проверки всех подключений к БД на production.
Запускать на сервере Red Hat: python3 check_production_connections.py
"""

import os
import sys
import socket
from pathlib import Path

# Загружаем .env
try:
    from dotenv import load_dotenv
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print("✅ Файл .env загружен")
    else:
        print("⚠️  Файл .env не найден, используются системные переменные")
except ImportError:
    print("⚠️  python-dotenv не установлен, используются системные переменные")

print("\n" + "=" * 70)
print("ДИАГНОСТИКА ПОДКЛЮЧЕНИЙ К БАЗАМ ДАННЫХ")
print("=" * 70)

# ============================================================
# 1. Проверка переменных окружения
# ============================================================
print("\n📋 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
print("-" * 50)

env_vars = {
    'FLASK_ENV': os.getenv('FLASK_ENV'),
    'MYSQL_HOST': os.getenv('MYSQL_HOST'),
    'MYSQL_PORT': os.getenv('MYSQL_PORT', '3306'),
    'MYSQL_DATABASE': os.getenv('MYSQL_DATABASE'),
    'MYSQL_USER': os.getenv('MYSQL_USER'),
    'MYSQL_QUALITY_HOST': os.getenv('MYSQL_QUALITY_HOST'),
    'MYSQL_QUALITY_PORT': os.getenv('MYSQL_QUALITY_PORT', '3306'),
    'MYSQL_QUALITY_DATABASE': os.getenv('MYSQL_QUALITY_DATABASE'),
    'MYSQL_VOIP_HOST': os.getenv('MYSQL_VOIP_HOST'),
    'MYSQL_VOIP_PORT': os.getenv('MYSQL_VOIP_PORT', '3306'),
    'ORACLE_HOST': os.getenv('ORACLE_HOST'),
    'ORACLE_PORT': os.getenv('ORACLE_PORT', '1521'),
    'ORACLE_SERVICE_NAME': os.getenv('ORACLE_SERVICE_NAME'),
    'REDMINE_URL': os.getenv('REDMINE_URL'),
}

for key, value in env_vars.items():
    if value:
        # Скрываем пароли
        display_value = '***' if 'PASSWORD' in key else value
        print(f"  ✅ {key}: {display_value}")
    else:
        print(f"  ❌ {key}: НЕ УСТАНОВЛЕНА")

# ============================================================
# 2. Проверка сетевой доступности
# ============================================================
print("\n🔌 ПРОВЕРКА СЕТЕВОЙ ДОСТУПНОСТИ:")
print("-" * 50)

def check_port(host, port, name):
    """Проверяет доступность порта"""
    if not host:
        print(f"  ⚠️  {name}: хост не указан")
        return False

    try:
        # DNS резолвинг
        ip = socket.gethostbyname(host)
        print(f"  📍 {name}: {host} -> {ip}")
    except socket.gaierror as e:
        print(f"  ❌ {name}: DNS ошибка для {host}: {e}")
        return False

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, int(port)))
        sock.close()

        if result == 0:
            print(f"  ✅ {name}: {host}:{port} - ДОСТУПЕН")
            return True
        else:
            print(f"  ❌ {name}: {host}:{port} - НЕДОСТУПЕН (код: {result})")
            return False
    except socket.timeout:
        print(f"  ❌ {name}: {host}:{port} - ТАЙМАУТ")
        return False
    except Exception as e:
        print(f"  ❌ {name}: {host}:{port} - ОШИБКА: {e}")
        return False

# Проверяем все хосты
mysql_ok = check_port(
    os.getenv('MYSQL_HOST'),
    os.getenv('MYSQL_PORT', '3306'),
    "MySQL Redmine"
)
quality_ok = check_port(
    os.getenv('MYSQL_QUALITY_HOST'),
    os.getenv('MYSQL_QUALITY_PORT', '3306'),
    "MySQL Quality"
)
voip_ok = check_port(
    os.getenv('MYSQL_VOIP_HOST'),
    os.getenv('MYSQL_VOIP_PORT', '3306'),
    "MySQL VoIP"
)
oracle_ok = check_port(
    os.getenv('ORACLE_HOST'),
    os.getenv('ORACLE_PORT', '1521'),
    "Oracle ERP"
)

# ============================================================
# 3. Проверка подключений к MySQL
# ============================================================
print("\n🗄️  ПРОВЕРКА ПОДКЛЮЧЕНИЙ К MySQL:")
print("-" * 50)

try:
    import pymysql

    def test_mysql_connection(host, port, user, password, database, name):
        """Тестирует подключение к MySQL"""
        if not all([host, user, password, database]):
            print(f"  ⚠️  {name}: неполные параметры подключения")
            return False

        try:
            conn = pymysql.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=database,
                connect_timeout=10
            )
            conn.close()
            print(f"  ✅ {name}: подключение успешно")
            return True
        except pymysql.Error as e:
            print(f"  ❌ {name}: ошибка подключения: {e}")
            return False

    # Тест MySQL Redmine
    test_mysql_connection(
        os.getenv('MYSQL_HOST'),
        os.getenv('MYSQL_PORT', '3306'),
        os.getenv('MYSQL_USER'),
        os.getenv('MYSQL_PASSWORD'),
        os.getenv('MYSQL_DATABASE'),
        "MySQL Redmine"
    )

    # Тест MySQL Quality
    test_mysql_connection(
        os.getenv('MYSQL_QUALITY_HOST'),
        os.getenv('MYSQL_QUALITY_PORT', '3306'),
        os.getenv('MYSQL_QUALITY_USER'),
        os.getenv('MYSQL_QUALITY_PASSWORD'),
        os.getenv('MYSQL_QUALITY_DATABASE'),
        "MySQL Quality"
    )

    # Тест MySQL VoIP
    test_mysql_connection(
        os.getenv('MYSQL_VOIP_HOST'),
        os.getenv('MYSQL_VOIP_PORT', '3306'),
        os.getenv('MYSQL_VOIP_USER'),
        os.getenv('MYSQL_VOIP_PASSWORD'),
        os.getenv('MYSQL_VOIP_DATABASE'),
        "MySQL VoIP"
    )

except ImportError:
    print("  ⚠️  pymysql не установлен, пропускаем тест MySQL")

# ============================================================
# 4. Проверка подключения к Oracle
# ============================================================
print("\n🗄️  ПРОВЕРКА ПОДКЛЮЧЕНИЯ К ORACLE:")
print("-" * 50)

try:
    import oracledb

    oracle_host = os.getenv('ORACLE_HOST')
    oracle_port = os.getenv('ORACLE_PORT', '1521')
    oracle_service = os.getenv('ORACLE_SERVICE_NAME')
    oracle_user = os.getenv('ORACLE_USER')
    oracle_password = os.getenv('ORACLE_PASSWORD')

    if all([oracle_host, oracle_service, oracle_user, oracle_password]):
        try:
            conn = oracledb.connect(
                user=oracle_user,
                password=oracle_password,
                host=oracle_host,
                port=int(oracle_port),
                service_name=oracle_service
            )
            conn.close()
            print(f"  ✅ Oracle ERP: подключение успешно")
        except oracledb.Error as e:
            print(f"  ❌ Oracle ERP: ошибка подключения: {e}")
    else:
        print("  ⚠️  Oracle ERP: неполные параметры подключения")

except ImportError:
    print("  ⚠️  oracledb не установлен, пропускаем тест Oracle")

# ============================================================
# 5. Проверка HTTPS доступа к Redmine
# ============================================================
print("\n🌐 ПРОВЕРКА HTTPS ДОСТУПА К REDMINE:")
print("-" * 50)

try:
    import requests

    redmine_url = os.getenv('REDMINE_URL')
    if redmine_url:
        try:
            response = requests.get(redmine_url, timeout=10, verify=False)
            print(f"  ✅ {redmine_url}: статус {response.status_code}")
        except requests.RequestException as e:
            print(f"  ❌ {redmine_url}: ошибка: {e}")
    else:
        print("  ⚠️  REDMINE_URL не установлен")

    quality_url = os.getenv('REDMINE_QUALITY_URL')
    if quality_url:
        try:
            response = requests.get(quality_url, timeout=10, verify=False)
            print(f"  ✅ {quality_url}: статус {response.status_code}")
        except requests.RequestException as e:
            print(f"  ❌ {quality_url}: ошибка: {e}")

except ImportError:
    print("  ⚠️  requests не установлен, пропускаем тест HTTPS")

# ============================================================
# 6. Итоговый отчет
# ============================================================
print("\n" + "=" * 70)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 70)

issues = []

# Проверка критических ошибок в конфигурации
mysql_host = os.getenv('MYSQL_HOST', '')
mysql_port = os.getenv('MYSQL_PORT', '3306')

if mysql_host and 'helpdesk.teztour.com' in mysql_host and mysql_port != '3306':
    issues.append(f"❌ КРИТИЧНО: MYSQL_HOST={mysql_host} но MYSQL_PORT={mysql_port}. "
                  f"Для прямого подключения к helpdesk.teztour.com используйте порт 3306!")

if mysql_host == '127.0.0.1' and mysql_port != '3306':
    issues.append(f"⚠️  MYSQL_HOST=127.0.0.1 с портом {mysql_port} - "
                  f"убедитесь, что SSH-туннель/прокси запущен на этом порту!")

quality_host = os.getenv('MYSQL_QUALITY_HOST', '')
quality_port = os.getenv('MYSQL_QUALITY_PORT', '3306')

if quality_host == '127.0.0.1' and not os.getenv('MYSQL_QUALITY_PORT'):
    issues.append("⚠️  MYSQL_QUALITY_HOST=127.0.0.1 но MYSQL_QUALITY_PORT не указан - "
                  "будет использован порт 3306 по умолчанию!")

flask_env = os.getenv('FLASK_ENV', '')
if flask_env == 'development':
    issues.append("⚠️  FLASK_ENV=development на production сервере! "
                  "Рекомендуется установить FLASK_ENV=production")

if issues:
    print("\n🚨 ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
    for issue in issues:
        print(f"   {issue}")
else:
    print("\n✅ Критических проблем в конфигурации не обнаружено")

print("\n" + "=" * 70)
print("Для исправления проблем отредактируйте файл .env")
print("Пример правильной конфигурации: env.production.example")
print("=" * 70)
