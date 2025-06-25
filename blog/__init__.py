import atexit
import logging
import os
from pathlib import Path

from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask, request, session, Blueprint
from flask_apscheduler import APScheduler
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

from .db_config import db
from .settings import Config
from blog.scheduler_tasks import scheduled_check_all_user_notifications
from blog.notification_service import BrowserPushService
from blog.utils.logger import configure_blog_logger

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', force=True)
# force=True перезапишет любую существующую конфигурацию корневого логгера, что полезно для отладки.

bcrypt = Bcrypt()
migrate = Migrate()

login_manager = LoginManager()
login_manager.login_view = "users.login"  # type: ignore
login_manager.login_message_category = "info"
login_manager.login_message = "Авторизуйтесь, чтобы попасть на эту страницу!"

scheduler = APScheduler()

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

# Инициализация Oracle Client отключена - используем Thin Mode
# python-oracledb работает в Thin Mode (чистый Python) без Oracle Client
# Thick Mode отключен, так как не требует установки Oracle Instant Client
print("🟢 [INIT] Oracle DB работает в Thin Mode (без Oracle Client)")

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
            WTF_CSRF_ENABLED=True,  # Включаем CSRF защиту
            # Отключаем кэширование для разработки
            SEND_FILE_MAX_AGE_DEFAULT=0,
            TEMPLATES_AUTO_RELOAD=True
        )
        print("🔧 [INIT] Режим отладки активен - настройки разработки применены")
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

    # ДОПОЛНИТЕЛЬНОЕ ИСПРАВЛЕНИЕ: Принудительно устанавливаем настройки шаблонов
    # независимо от режима debug (для гарантии)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    # Настройка Jinja окружения для отключения кэширования
    app.jinja_env.auto_reload = True
    app.jinja_env.cache = {}  # Очищаем кэш шаблонов

    print(f"🔧 [INIT] Принудительные настройки шаблонов:")
    print(f"🔧 [INIT] TEMPLATES_AUTO_RELOAD: {app.config.get('TEMPLATES_AUTO_RELOAD')}")
    print(f"🔧 [INIT] jinja_env.auto_reload: {app.jinja_env.auto_reload}")
    print(f"🔧 [INIT] DEBUG: {app.debug}")

    # Инициализация компонентов
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    # Конфигурация логгера до первого использования app.logger
    configure_blog_logger()

    # Регистрируем user_loader здесь, после инициализации login_manager
    from blog.models import load_user
    login_manager.user_loader(load_user)

    # Инициализируем CSRF защиту
    csrf.init_app(app)

    # Настройка CORS - универсальная для всех сред
    cors_origins = ["*"] if app.debug else [
        "https://your-domain.com",
        "https://www.your-domain.com",
        "https://tez-tour.com",
        "https://www.tez-tour.com"
    ]

    CORS(
        app,
        resources={
            r"/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": [
                    "Content-Type",
                    "Authorization",
                    "X-Requested-With",
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Headers",
                    "Access-Control-Allow-Methods"
                ],
                "supports_credentials": True,
                "expose_headers": ["Content-Range", "X-Total-Count"]
            }
        }
    )
    print(f"🌐 [INIT] CORS настроен для origins: {cors_origins}")

    # Регистрируем blueprint'ы
    from blog.main.routes import main
    from blog.user.routes import users
    from blog.post.routes import posts
    from blog.call.routes import calls
    from blog.finesse.routes import finesse
    from blog.netmonitor.routes import netmonitor  # Импортируем маршруты
    from blog.tasks.routes import tasks_bp  # Импортируем блюпринт задач
    from blog.tasks.api_routes import api_bp  # Импортируем новый API блюпринт

    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(calls)
    app.register_blueprint(finesse, url_prefix="/finesse")
    app.register_blueprint(netmonitor)
    app.register_blueprint(tasks_bp, url_prefix="/tasks")  # Регистрируем блюпринт задач с префиксом
    app.register_blueprint(api_bp)  # Регистрируем новый API блюпринт (уже с префиксом /tasks/api)

    # ИСПРАВЛЕНИЕ: Регистрируем template helpers для устранения хардкода в шаблонах
    from blog.utils.template_helpers import register_template_helpers
    register_template_helpers(app)

    # Дополнительная инициализация в контексте приложения
    with app.app_context():
        # ВРЕМЕННО ОТКЛЮЧЕНА - Простая миграция базы данных для добавления недостающих полей
        # try:
        #     import sqlite3
        #     # Правильный путь к базе данных
        #     db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        #     if db_uri.startswith('sqlite:///'):
        #         db_path = db_uri.replace('sqlite:///', '')
        #         if os.path.exists(db_path):
        #             conn = sqlite3.connect(db_path)
        #             cursor = conn.cursor()
        #
        #             # Проверяем, есть ли поле notifications_widget_enabled
        #             cursor.execute("PRAGMA table_info(users)")
        #             columns = [col[1] for col in cursor.fetchall()]
        #
        #             if 'notifications_widget_enabled' not in columns:
        #                 cursor.execute("ALTER TABLE users ADD COLUMN notifications_widget_enabled BOOLEAN DEFAULT 1 NOT NULL")
        #                 cursor.execute("UPDATE users SET notifications_widget_enabled = 1")
        #                 conn.commit()
        #                 print("[INIT] Добавлено поле notifications_widget_enabled в таблицу users", flush=True)
        #             else:
        #                 print("[INIT] Поле notifications_widget_enabled уже существует", flush=True)
        #
        #             conn.close()
        #         else:
        #             print(f"[INIT] База данных не найдена: {db_path}", flush=True)
        #     else:
        #         print("[INIT] Миграция работает только с SQLite", flush=True)
        # except Exception as e:
        #     print(f"[INIT] Ошибка при миграции БД: {e}", flush=True)
        #     # НЕ прерываем инициализацию приложения из-за ошибки миграции

        print("[INIT] Миграция БД временно отключена для отладки", flush=True)

        # Push-уведомления больше не используются, CSRF исключения удалены
        print("[INIT] Инициализация завершена без push API.", flush=True)

    # Инициализация и запуск планировщика только в основном процессе Werkzeug
    # Это предотвратит запуск нескольких экземпляров планировщика в режиме отладки с автоперезагрузкой
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        if not scheduler.running:
            try:
                scheduler.init_app(app) # Инициализируем планировщик с приложением
                scheduler.start()
                app.logger.info("Scheduler initialized and started successfully ONLY in main process or production.")

                job_id = 'check_all_user_notifications_job'
                if not scheduler.get_job(job_id):
                    scheduler.add_job(
                        func=scheduled_check_all_user_notifications,
                        trigger=IntervalTrigger(minutes=1), # или app.config.get('SCHEDULER_INTERVAL_MINUTES', 1)
                        id=job_id,
                        name='Check all user notifications every 1 minute',
                        replace_existing=True
                    )
                    app.logger.info(f"Job '{job_id}' added to scheduler.")
                else:
                    app.logger.info(f"Job '{job_id}' already exists in scheduler.")
            except Exception as e_scheduler_init:
                app.logger.error(f"Error initializing or starting scheduler: {e_scheduler_init}", exc_info=True)
    else:
        if app.debug: # Только в режиме отладки, для дочернего процесса
            app.logger.info("Scheduler NOT started in Werkzeug reloader child process.")


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

        # Добавляем заголовки для отключения кэша в режиме отладки
        if app.debug:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

            # Специально для статических файлов CSS
            if response.content_type and 'text/css' in response.content_type:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'

        return response

    # Инициализация BrowserPushService
    # Это должно быть сделано до того, как какой-либо код попытается получить доступ к app.browser_push_service
    # Обычно это делается после всех основных инициализаций Flask, но до возврата app
    try:
        setattr(app, 'browser_push_service', BrowserPushService())
        app.logger.info("[INIT] BrowserPushService инициализирован и добавлен в app.")
    except Exception as e:
        app.logger.error(f"[INIT] Ошибка при инициализации BrowserPushService: {e}", exc_info=True)
        # Решаем, что делать в случае ошибки:
        # 1. Позволить приложению упасть (если сервис критичен)
        # 2. Установить в None и логировать (если сервис не критичен для старта)
        setattr(app, 'browser_push_service', None)

    return app
