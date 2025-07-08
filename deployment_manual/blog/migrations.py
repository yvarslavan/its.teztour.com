from sqlalchemy import create_engine
from blog.settings import Config
import os
import oracledb
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Oracle Client инициализация отключена - используем Thin Mode
# python-oracledb работает в Thin Mode без дополнительных библиотек
print("🟢 [MIGRATIONS] Oracle DB работает в Thin Mode (без Oracle Client)")

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
