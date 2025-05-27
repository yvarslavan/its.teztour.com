import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', force=True)
# force=True перезапишет любую существующую конфигурацию корневого логгера, что полезно для отладки.
from flask import Flask, request, session, Blueprint
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pathlib import Path
import os
import cx_Oracle
from flask_cors import CORS
from flask_session import Session
import atexit

from .db_config import db  # Импортируем db из нового файла
from .settings import Config

# Импортируем нашу новую задачу
from blog.scheduler_tasks import scheduled_check_all_user_notifications

bcrypt = Bcrypt()
migrate = Migrate()

login_manager = LoginManager()
login_manager.login_view = "users.login"
login_manager.login_message_category = "info"
login_manager.login_message = "Авторизуйтесь, чтобы попасть на эту страницу!"

scheduler = BackgroundScheduler()

# Функция для корректной остановки планировщика
def shutdown_scheduler():
    if scheduler.running:
        try:
            scheduler.shutdown()
            print("Scheduler shutdown successfully.")
        except Exception as e:
            print(f"Error during scheduler shutdown: {e}")

# Регистрируем функцию для выполнения при выходе из приложения
atexit.register(shutdown_scheduler)

csrf = CSRFProtect()

# Определяем путь к базе данных
db_path = Path(__file__).parent / "db" / "blog.db"

# Создаем директорию для базы данных если её нет
if not db_path.parent.exists():
    db_path.parent.mkdir(parents=True, exist_ok=True)

# Инициализация Oracle Client
# Убираем путь по умолчанию, так как он задается в systemd или .env файлах
oracle_client_path = os.environ.get('ORACLE_CLIENT_PATH', None)

if oracle_client_path and os.path.exists(oracle_client_path):
    try:
        cx_Oracle.init_oracle_client(lib_dir=oracle_client_path)
        print(f"Oracle Client инициализирован успешно: {oracle_client_path}")
    except Exception as e:
        print(f"Ошибка инициализации Oracle Client: {e}")
else:
    print(f"ВНИМАНИЕ: Путь к Oracle Client не найден: {oracle_client_path}")

def create_app():
    app = Flask(__name__)

    # Загрузка конфигурации
    app.config.from_object(Config)

    # Фиксированный секретный ключ - используйте значение из окружения в продакшн
    app.secret_key = os.environ.get('SECRET_KEY', "e6914948deb30b6ece648d7ac6c81bc1fa822008d425dc38")

    # Разные настройки для разных окружений
    if app.debug:
        # Для локальной разработки
        app.config.update(
            SESSION_COOKIE_NAME='helpdesk_session',
            SESSION_COOKIE_SECURE=False,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            PERMANENT_SESSION_LIFETIME=86400,
            WTF_CSRF_ENABLED=True  # Включаем CSRF защиту
        )
    else:
        # Для продакшена
        app.config.update(
            SESSION_COOKIE_NAME='helpdesk_session',
            SESSION_COOKIE_SECURE=True,  # Включено для HTTPS
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',  # Более безопасная настройка
            SESSION_COOKIE_DOMAIN='.tez-tour.com',  # Домен для продакшена
            PERMANENT_SESSION_LIFETIME=86400,
            WTF_CSRF_ENABLED=True  # Включаем CSRF защиту
        )

    # Проверка критичных значений
    for key in ["SQLALCHEMY_DATABASE_URI", "SQLALCHEMY_DATABASE_URI_ORACLE_CRM",
                "SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES"]:
        if app.config.get(key) is None:
            print(f"ВНИМАНИЕ: Переменная {key} не определена в конфигурации!")

    # НОВОЕ: Минимальный набор настроек для SQLAlchemy
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Инициализация компонентов
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    # Регистрируем user_loader здесь, после инициализации login_manager
    from blog.models import load_user
    login_manager.user_loader(load_user)

    # Инициализируем CSRF защиту
    csrf.init_app(app)

    # Настройка CORS - поместите ДО регистрации blueprints
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # Регистрируем blueprint'ы
    from blog.main.routes import main
    from blog.user.routes import users
    from blog.post.routes import posts
    from blog.call.routes import calls
    from blog.finesse.routes import finesse
    from blog.netmonitor.routes import netmonitor  # Импортируем маршруты

    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(calls)
    app.register_blueprint(finesse, url_prefix="/finesse")
    app.register_blueprint(netmonitor)  # Используем Blueprint из routes.py

    with app.app_context():
        if not scheduler.running:
            try:
                scheduler.start()
                print("Scheduler started successfully.")

                # Добавляем нашу задачу в планировщик
                # Будет выполняться каждые 5 минут
                # Убедимся, что задача не добавляется многократно при перезапусках (особенно в debug режиме)
                if not scheduler.get_job('check_all_user_notifications_job'):
                    scheduler.add_job(
                        func=scheduled_check_all_user_notifications,
                        trigger=IntervalTrigger(minutes=1),
                        id='check_all_user_notifications_job',
                        name='Check all user notifications every 5 minutes',
                        replace_existing=True
                    )
                    print("Job 'check_all_user_notifications_job' added to scheduler.")
                else:
                    print("Job 'check_all_user_notifications_job' already exists in scheduler.")

            except Exception as e:
                print(f"Error starting scheduler or adding job: {e}")
        try:
            # Создаем только локальные таблицы SQLite
            # Исключаем Oracle таблицы
            db.create_all()  # Создадим только таблицы из default bind
        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")

    # <<< НАЧАЛО ИЗМЕНЕНИЯ: Явная инициализация Flask-Session >>>
    # Убедимся, что SESSION_TYPE установлен (например, из Config)
    if not app.config.get("SESSION_TYPE"):
        app.config["SESSION_TYPE"] = "filesystem" # Устанавливаем значение по умолчанию, если не задано
        print("WARNING: SESSION_TYPE not set in Config, defaulting to 'filesystem'")
    Session(app)
    # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

    @app.after_request
    def after_request(response):
        app.logger.debug(f"Session after request: {dict(session)}")
        return response

    return app
