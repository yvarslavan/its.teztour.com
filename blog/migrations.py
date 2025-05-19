from sqlalchemy import create_engine
from blog.settings import Config
import os
import cx_Oracle
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем путь к Oracle Client
oracle_client_path = os.getenv('ORACLE_CLIENT_PATH')

# # Настраиваем Oracle Client только если путь указан и существует
# # Этот блок удален, так как инициализация происходит в blog/__init__.py
# if oracle_client_path and os.path.exists(oracle_client_path):
#     try:
#         cx_Oracle.init_oracle_client(lib_dir=oracle_client_path)
#         print(f"Oracle Client инициализирован: {oracle_client_path}")
#     except Exception as e:
#         print(f"Ошибка при инициализации Oracle Client: {e}")
# else:
#     print(f"ВНИМАНИЕ: Путь к Oracle Client не найден: {oracle_client_path}")

# Строки подключения к базам данных
oracle_crm_uri = os.getenv('SQLALCHEMY_DATABASE_URI_ORACLE_CRM')
oracle_sales_uri = os.getenv('SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES')

# Проверяем наличие строк подключения
if not oracle_crm_uri:
    print("ВНИМАНИЕ: SQLALCHEMY_DATABASE_URI_ORACLE_CRM не установлена!")
else:
    print(f"SQLALCHEMY_DATABASE_URI_ORACLE_CRM: {oracle_crm_uri}")

if not oracle_sales_uri:
    print("ВНИМАНИЕ: SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES не установлена!")
else:
    print(f"SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES: {oracle_sales_uri}")

# Создаем движок Oracle CRM
if oracle_crm_uri:
    try:
        engine_oracle_crm = create_engine(oracle_crm_uri)
        print(f"Соединение с Oracle CRM инициализировано: {oracle_crm_uri}")
    except Exception as e:
        print(f"Ошибка инициализации Oracle CRM: {e}")
        # Создаем фиктивный движок для безопасности импорта
        engine_oracle_crm = create_engine("sqlite:///blog/db/dummy_oracle.db")
else:
    print("ВНИМАНИЕ: Oracle CRM URL не задан, используем фиктивное соединение")
    engine_oracle_crm = create_engine("sqlite:///blog/db/dummy_oracle.db")

# Создаем движок Oracle SALES
if oracle_sales_uri:
    try:
        engine_sales_schema = create_engine(oracle_sales_uri)
        print(f"Соединение с Oracle SALES инициализировано: {oracle_sales_uri}")
    except Exception as e:
        print(f"Ошибка инициализации Oracle SALES: {e}")
        # Создаем фиктивный движок для безопасности импорта
        engine_sales_schema = create_engine("sqlite:///blog/db/dummy_sales.db")
else:
    print("ВНИМАНИЕ: Oracle SALES URL не задан, используем фиктивное соединение")
    engine_sales_schema = create_engine("sqlite:///blog/db/dummy_sales.db")
