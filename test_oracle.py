import os
import oracledb
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

print("🔍 Проверка подключения к Oracle...")
print(f"Host: {os.getenv('ORACLE_HOST')}")
print(f"Port: {os.getenv('ORACLE_PORT')}")
print(f"Service: {os.getenv('ORACLE_SERVICE_NAME')}")
print(f"User: {os.getenv('ORACLE_USER')}")

dsn = oracledb.makedsn(
    os.getenv('ORACLE_HOST'),
    os.getenv('ORACLE_PORT'),
    service_name=os.getenv('ORACLE_SERVICE_NAME')
)

try:
    connection = oracledb.connect(
        user=os.getenv('ORACLE_USER'),
        password=os.getenv('ORACLE_PASSWORD'),
        dsn=dsn
    )
    print("✅ Успешное подключение к Oracle!")
    
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM DUAL")
    result = cursor.fetchone()
    print(f"✅ Тестовый запрос вернул: {result}")
    
    connection.close()
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")

