#!/usr/bin/env python
"""
Скрипт для диагностики проблем с Oracle Client
"""
import os
import sys
from pathlib import Path

def check_oracle_environment():
    """Проверяет окружение Oracle"""
    print("=== ДИАГНОСТИКА ORACLE CLIENT ===")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")

    # Проверяем переменные окружения
    print("\n--- ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ---")
    oracle_vars = [
        'ORACLE_CLIENT_PATH',
        'ORACLE_HOME',
        'LD_LIBRARY_PATH',
        'TNS_ADMIN',
        'SQLALCHEMY_DATABASE_URI_ORACLE_CRM',
        'SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES'
    ]

    for var in oracle_vars:
        value = os.environ.get(var, 'НЕ УСТАНОВЛЕНА')
        print(f"{var}: {value}")

    # Проверяем пути к Oracle Client
    print("\n--- ПРОВЕРКА ПУТЕЙ ---")
    oracle_client_path = os.environ.get('ORACLE_CLIENT_PATH')
    if oracle_client_path:
        print(f"ORACLE_CLIENT_PATH указан: {oracle_client_path}")
        if os.path.exists(oracle_client_path):
            print(f"✅ Путь существует")
            # Проверяем содержимое директории
            try:
                files = os.listdir(oracle_client_path)
                lib_files = [f for f in files if 'oracle' in f.lower() or f.endswith('.so')]
                print(f"📁 Файлы Oracle в директории: {len(lib_files)}")
                for f in lib_files[:10]:  # Показываем первые 10 файлов
                    print(f"   - {f}")
                if len(lib_files) > 10:
                    print(f"   ... и еще {len(lib_files) - 10} файлов")
            except Exception as e:
                print(f"❌ Ошибка чтения директории: {e}")
        else:
            print(f"❌ Путь НЕ существует")
    else:
        print("⚠️ ORACLE_CLIENT_PATH не установлен")

    # Возможные пути к Oracle Client
    possible_paths = [
        '/opt/oracle/instantclient',
        '/opt/oracle/instantclient_21_1',
        '/opt/oracle/instantclient_19_8',
        '/usr/lib/oracle',
        '/usr/local/oracle'
    ]

    print("\n--- ПОИСК ORACLE CLIENT ---")
    found_paths = []
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Найден: {path}")
            found_paths.append(path)
            try:
                files = os.listdir(path)
                oracle_files = [f for f in files if 'oracle' in f.lower()]
                print(f"   📁 Oracle файлов: {len(oracle_files)}")
            except:
                pass
        else:
            print(f"❌ Не найден: {path}")

    # Тестируем импорт oracledb
    print("\n--- ТЕСТИРОВАНИЕ БИБЛИОТЕК ---")
    try:
        import oracledb
        print(f"✅ oracledb импортирован успешно: версия {oracledb.__version__}")

        # Тестируем инициализацию
        if found_paths:
            for path in found_paths:
                print(f"\n🧪 Тестируем инициализацию с {path}...")
                try:
                    oracledb.init_oracle_client(lib_dir=path)
                    print(f"✅ Oracle Client инициализирован успешно с {path}")
                    break
                except Exception as e:
                    print(f"❌ Ошибка инициализации с {path}: {e}")
        else:
            print("🧪 Тестируем инициализацию без указания пути...")
            try:
                oracledb.init_oracle_client()
                print("✅ Oracle Client инициализирован успешно (по умолчанию)")
            except Exception as e:
                print(f"❌ Ошибка инициализации (по умолчанию): {e}")

    except ImportError as e:
        print(f"❌ Ошибка импорта oracledb: {e}")
        return False

    # Тестируем подключение к Oracle
    print("\n--- ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ ---")
    oracle_crm_uri = os.environ.get('SQLALCHEMY_DATABASE_URI_ORACLE_CRM')
    oracle_sales_uri = os.environ.get('SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES')

    if oracle_crm_uri:
        print(f"🧪 Тестируем подключение CRM...")
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(oracle_crm_uri)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 FROM DUAL")).fetchone()
                print(f"✅ Подключение CRM успешно: {result}")
        except Exception as e:
            print(f"❌ Ошибка подключения CRM: {e}")

    if oracle_sales_uri:
        print(f"🧪 Тестируем подключение SALES...")
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(oracle_sales_uri)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 FROM DUAL")).fetchone()
                print(f"✅ Подключение SALES успешно: {result}")
        except Exception as e:
            print(f"❌ Ошибка подключения SALES: {e}")

    print("\n=== ДИАГНОСТИКА ЗАВЕРШЕНА ===")
    return True

if __name__ == "__main__":
    # Загружаем переменные окружения
    try:
        from dotenv import load_dotenv
        # Проверяем разные файлы окружения
        env_files = ['.env', '.env.production', '.env.local']
        for env_file in env_files:
            if os.path.exists(env_file):
                print(f"📄 Загружаем {env_file}")
                load_dotenv(env_file)
                break
    except ImportError:
        print("⚠️ python-dotenv не установлен")

    check_oracle_environment()
