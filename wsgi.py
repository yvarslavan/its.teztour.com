import os
from pathlib import Path
from dotenv import load_dotenv
from flask_cors import CORS
from blog import create_app

# Определяем базовый путь для приложения
BASE_DIR = Path(__file__).resolve().parent

# Определяем окружение
ENV = os.environ.get('FLASK_ENV', 'development')

# Принудительно загружаем .env.production если на сервере (проверка на Linux)
if os.name != 'nt':  # Не Windows - значит Linux
    env_path = BASE_DIR / '.env.production'
    ENV = 'production'
else:
    # Загружаем соответствующий .env файл для Windows-разработки
    if ENV == 'production':
        env_path = BASE_DIR / '.env.production'
    else:
        env_path = BASE_DIR / '.env.development'

print(f"Загружаем настройки из {env_path}, окружение: {ENV}")
load_dotenv(env_path)

# Создаем директорию для сессий, если её нет
db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blog', 'db')
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# Отладочный вывод для проверки переменных окружения
print(f"SQLALCHEMY_DATABASE_URI_ORACLE_CRM: {os.environ.get('SQLALCHEMY_DATABASE_URI_ORACLE_CRM')}")
print(f"SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES: {os.environ.get('SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES')}")

# Создаем приложение
app = create_app()

# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Принудительно включаем режим отладки для разработки
if ENV == 'development' or os.name == 'nt':  # Windows = разработка
    app.debug = True
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    print("🔧 ПРИНУДИТЕЛЬНО включен режим отладки для разработки")
    print(f"🔧 DEBUG: {app.debug}")
    print(f"🔧 TEMPLATES_AUTO_RELOAD: {app.config.get('TEMPLATES_AUTO_RELOAD')}")

# Настройки сессий и безопасности
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    REMEMBER_COOKIE_SECURE=True,
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SAMESITE='Lax'
)

# Настройка CORS
CORS(
    app,
    resources={
        r"/*": {
            "origins": ["http://localhost:5000", "http://127.0.0.1:5000", "*"],
            "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Headers",
                "Access-Control-Allow-Methods",
                "X-Requested-With",
            ],
            "supports_credentials": True,
            "expose_headers": ["Content-Range", "X-Total-Count"],
        }
    },
)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000,
            use_reloader=True,
            threaded=False)
