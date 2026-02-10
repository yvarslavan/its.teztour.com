import shutil
import logging
import os
import traceback
import unicodedata
from configparser import ConfigParser
from datetime import datetime, timedelta
import time
from apscheduler.jobstores.base import JobLookupError
import oracledb
import sqlalchemy
from sqlalchemy import func, or_, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
import pytz
from blog.user.forms import LoginForm, RegistrationForm, UpdateAccountForm, AddCommentRedmine
from flask import (
    Blueprint,
    render_template,
    flash,
    url_for,
    request,
    session,
    g,
    current_app,
    send_file,
    send_from_directory,
    jsonify,
    app,
    Response,
)
import requests
from flask_login import current_user, logout_user, login_required, login_user, AnonymousUserMixin
from sqlalchemy.orm import sessionmaker, load_only
from werkzeug.utils import redirect
from blog import db, scheduler
from blog.models import User, Post, PushSubscription
from blog.user.forms import RegistrationForm, LoginForm, UpdateAccountForm
from blog.user.utils import save_picture, random_avatar, quality_control_required, validate_user_image_path
from erp_oracle import (
    connect_oracle,
    db_host,
    db_port,
    db_service_name,
    db_user_name,
    db_password,
    get_user_erp_data,
    get_user_erp_password,
)
from redmine import (
    check_notifications,
    get_count_notifications,
    get_count_notifications_add_notes,
    get_connection,
    db_redmine_host,
    db_redmine_user_name,
    db_redmine_password,
    db_redmine_name,
    db_redmine_port,
    check_user_active_redmine,
    generate_email_signature,
)
from mysql_db import Issue, Session, init_quality_db
from flask_wtf.csrf import generate_csrf
from blog import csrf
from blog.call.routes import get_db_connection
import pymysql
from pymysql.cursors import DictCursor
from blog.notification_service import check_notifications_improved
from blog.utils.decorators import debug_only, development_only


# Настройка логгирования
logger = logging.getLogger(__name__)

users = Blueprint("users", __name__)
USERS_ACCOUNT_URL = "users.account"
# Используем переменные окружения напрямую
import os
# url_recovery_password = os.getenv('RECOVERY_PASSWORD_URL') or "" # DEPRECATED: Moved to Config
# Получение пути к ERP файлу
ERP_FILE_PATH = os.getenv('ERP_FILE_PATH') or ""
# Определение пути к файлу в зависимости от операционной системы
if os.name == "nt":  # Windows
    ERP_FILE_PATH = r"\\10.1.14.10\erp\ERP\TEZERP.exe"


@users.before_request
def set_current_user():
    g.current_user = current_user if current_user.is_authenticated else None


# Контекстный процессор для передачи количества уведомлений в каждый шаблон
@users.context_processor
def inject_notification_count():
    sum_count_notifications = 0
    if hasattr(g, "current_user") and g.current_user is not None:
        # Подсчет уведомлений для текущего пользователя
        count_notifications = get_count_notifications(g.current_user.id)
        count_notifications_add_notes = get_count_notifications_add_notes(
            g.current_user.id
        )
        sum_count_notifications = count_notifications + count_notifications_add_notes
    else:
        sum_count_notifications = 0  # Если пользователь не авторизован, уведомлений нет
    return dict(count_notifications=sum_count_notifications)

# Контекстный процессор для передачи функций утилит в шаблоны
@users.context_processor
def inject_util_functions():
    from blog.user.utils import get_user_image_url
    return dict(get_user_image_url=get_user_image_url)


@users.route("/register", methods=["GET", "POST"])
def register():
    logger.info("[REGISTER DEBUG] Register route accessed")
    if current_user.is_authenticated:
        return redirect(url_for("main.blog"))
    form = RegistrationForm()

    if request.method == "POST":
        logger.info(f"[REGISTER DEBUG] POST request received")
        logger.info(f"[REGISTER DEBUG] Form data: {dict(request.form)}")
        logger.info(f"[REGISTER DEBUG] CSRF token in form: {request.form.get('csrf_token', 'NOT FOUND')}")
        logger.info(f"[REGISTER DEBUG] Form errors: {form.errors}")
        logger.info(f"[REGISTER DEBUG] Form validate_on_submit: {form.validate_on_submit()}")
        logger.info(f"[REGISTER DEBUG] User-Agent: {request.headers.get('User-Agent', 'Unknown')}")

    if form.validate_on_submit():
        oracle_connection = None
        try:
            oracle_connection = connect_oracle(
                db_host, db_port, db_service_name, db_user_name, db_password
            )
            if oracle_connection is None:
                flash("Не удалось подключиться к TEZ ERP. Проверьте VPN соединение (Cisco Secure Client) и стабильность интернета. Если проблема persists, попробуйте позже.", "error")
                return render_template(
                    "register.html", form=form, title="Регистрация", legend="Регистрация"
                )
            # hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            # Получить данные ERP пользователя
            user_erp_data = get_user_erp_data(
                oracle_connection, form.username.data, form.password.data
            )

            # Проверяем, что данные получены успешно
            if user_erp_data is None:
                flash("Не удалось проверить учетные данные в TEZ ERP. Возможные причины: неверный логин/пароль, истек срок действия VPN, или временные проблемы соединения.", "error")
                return render_template(
                    "register.html", form=form, title="Регистрация", legend="Регистрация"
                )

            # Проверяем это пользовтель Redmine ? Если да, в поле is_redmine_user пишем True и в поле id_redmine_user id_user Redmine
            user_redmine_status, user_redmine_id = check_redmine_user(user_erp_data[2])
            # email
            user = User(
                username=form.username.data,
                password=user_erp_data[0],
                full_name=user_erp_data[1],
                email=user_erp_data[2],
                department=user_erp_data[4],
                position=user_erp_data[5],
                phone=user_erp_data[6],
                office=user_erp_data[3],
                vpn=user_erp_data[7],
                vpn_end_date=user_erp_data[8],
                is_redmine_user=user_redmine_status,
                id_redmine_user=user_redmine_id,
                image_file=random_avatar(form.username.data),
            )
            db.session.add(user)
            db.session.commit()
            flash("Спасибо за регистрацию. Теперь вы можете авторизоваться.", "success")
            return redirect(url_for("users.login"))
        except oracledb.DatabaseError as e:
            flash(f"Ошибка подключения к TEZ ERP. Проверьте VPN соединение и интернет. Если проблема повторяется, обратитесь в IT поддержку.", "error")
            logging.error(f"Oracle connection error during registration: {str(e)}")
        finally:
            if oracle_connection:
                oracle_connection.close()

    return render_template(
        "register.html", form=form, title="Регистрация", legend="Регистрация"
    )


def connect_to_database():
    conn = get_connection(
        db_redmine_host,
        db_redmine_user_name,
        db_redmine_password,
        db_redmine_name,
        port=db_redmine_port
    )
    if conn is None:
        flash(
            "Ошибка подключения к HelpDesk (Easy Redmine). Проверьте ваше VPN соединение",
            "danger",
        )
        return None
    return conn


def check_redmine_user(email):
    conn = connect_to_database()
    if conn is None:
        # Обработка ситуации, когда соединение не установлено
        return False, None

    try:
        check_user_redmine = check_user_active_redmine(conn, email)
        if check_user_redmine == 4:
            return False, check_user_redmine
        return True, check_user_redmine
    finally:
        conn.close()


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.blog"))

    form = LoginForm()

    # Детальная отладка CSRF
    if request.method == "POST":
        logger.debug("🔍 [LOGIN DEBUG] POST Request Analysis")
        logger.debug(f"📝 Request form data: {dict(request.form)}")
        logger.debug(f"🔒 CSRF enabled: {current_app.config.get('WTF_CSRF_ENABLED')}")
        logger.debug(f"🔒 CSRF token in form: {request.form.get('csrf_token', 'NOT FOUND')}")
        logger.debug(f"🍪 Session ID: {session.get('_id', 'No session ID')}")
        logger.debug(f"🍪 Session keys: {list(session.keys())}")
        logger.debug(f"🍪 Cookies: {list(request.cookies.keys())}")
        logger.debug(f"🌐 Request headers: Origin={request.headers.get('Origin')}, Referer={request.headers.get('Referer')}")

        # Генерируем новый CSRF токен для отладки
        try:
            debug_csrf = generate_csrf()
            logger.debug(f"🔐 Generated CSRF token: {debug_csrf[:20]}...")
        except Exception as e:
            logger.error(f"❌ Error generating CSRF token: {e}")

        # Populate form data if not already set
        if not form.username.data and request.form.get('username'):
            form.username.data = request.form.get('username')
            logger.debug(f"✅ Manually set username: {form.username.data}")

        if not form.password.data and request.form.get('password'):
            form.password.data = request.form.get('password')
            logger.debug(f"✅ Manually set password (length: {len(form.password.data) if form.password.data else 0})")

        logger.debug(f"📋 Form errors: {form.errors}")
        logger.debug(f"✔️ Form validate: {form.validate()}")
        logger.debug(f"✔️ Form validate_on_submit: {form.validate_on_submit()}")

    if form.validate_on_submit():
        logger.debug(f"✅ Form validation passed")
        logger.debug(f"Username: {form.username.data}")
        logger.debug(f"Password length: {len(form.password.data) if form.password.data else 0}")

        user = authenticate_user(form.username.data, form.password.data)
        logger.debug(f"Authenticate result: {user}")

        if user:
            logger.debug(f"✅ User authenticated successfully: {user.username}")
            return handle_successful_login(user, form)
        else:
            logger.debug(f"❌ Authentication failed for user: {form.username.data}")
            flash("Войти не удалось. Неверный пароль или пароль мог быть обновлен в ERP. Пожалуйста, попробуйте снова.",
                "error")
    else:
        logger.debug(f"❌ Form validation failed")
        logger.debug(f"Form errors: {form.errors}")
        logger.debug(f"Form data: username={form.username.data}, password={'*' * len(form.password.data) if form.password.data else 'None'}")

    return render_template(
        "login.html", form=form, title="Логин TEZ ERP", legend="Войти"
    )


# Тестовый эндпоинт login-modern удален


def authenticate_user(username, password):
    logger.debug(f"🔐 authenticate_user called for username: {username}")
    user = User.query.filter_by(username=username).first()
    logger.debug(f"🔐 User found in SQLite: {user is not None}")

    if user:
        logger.debug(f"🔐 User ID: {user.id}, Username: {user.username}")
        # Проверяем пароль в SQLite
        password_match = password == user.password
        logger.debug(f"🔐 Password match in SQLite: {password_match}")

        if password_match:
            # Oracle-проверка пароля по умолчанию отключена ради скорости логина.
            # Включить можно через ORACLE_LOGIN_CHECK=on
            if os.getenv("ORACLE_LOGIN_CHECK", "off").lower() == "on":
                oracle_check = check_and_update_password(user, password)
                logger.debug(f"🔐 Oracle password check: {oracle_check}")
                if not oracle_check:
                    logger.debug(f"❌ Oracle password check failed for user: {username}")
                    return None
            logger.debug(f"✅ Authentication successful for user: {username}")
            return user
        else:
            logger.debug(f"❌ SQLite password mismatch for user: {username}")
    else:
        logger.debug(f"❌ User not found in SQLite: {username}")

    logger.debug(f"❌ Authentication failed for user: {username}")
    return None

def check_and_update_password(user, provided_password):
    logger.debug(f"🔐 check_and_update_password called for user: {user.username}")
    try:
        if os.getenv("ORACLE_LOGIN_CHECK", "off").lower() != "on":
            logger.info("ℹ️ Oracle password check skipped (ORACLE_LOGIN_CHECK!=on)")
            return True
        logger.debug(f"🔐 Attempting Oracle connection...")
        oracle_connection = connect_oracle(
            db_host, db_port, db_service_name, db_user_name, db_password
        )
        if oracle_connection is None:
            logger.error(f"❌ Oracle connection failed - allowing login with cached password")
            return True  # ВРЕМЕННО: разрешаем вход без Oracle-проверки
        logger.debug(f"✅ Oracle connection established")

        # Получаем актуальный пароль из Oracle - НЕ используем text() с cx_Oracle
        cursor = oracle_connection.cursor()
        query = """SELECT password FROM erp.t_user WHERE username = :username"""  # Используем обычную строку
        cursor.execute(query, username=user.username)
        result = cursor.fetchone()

        if result:
            oracle_password = result[0]
            if oracle_password != provided_password:
                # Обновляем пароль в SQLite
                user.password = oracle_password
                db.session.commit()
                return False  # Пароль обновлен, нужна повторная аутентификация
            return True  # Пароль актуален
        else:
            logging.error("Не удалось получить пароль для пользователя %s из Oracle", user.username)
            return True  # Позволяем вход с текущим паролем в случае ошибки
    except oracledb.DatabaseError as e:
        logging.error("Ошибка при проверке пароля в Oracle: %s", str(e))
        return True  # В случае ошибки, позволяем вход с текущим паролем
    finally:
        if oracle_connection:
            oracle_connection.close()


def handle_successful_login(user: User, form: LoginForm):
    logger.debug(f"🔐 Starting successful login for user: {user.username} (ID: {user.id})")
    try:
        session_maker = sessionmaker(bind=db.engine)
        local_session = session_maker()

        try:
            # Используйте text() для SQL выражений
            local_session.execute(text('PRAGMA busy_timeout = 10000'))
            user_obj = local_session.query(User).filter_by(id=user.id).first()
            if user_obj:
                user_obj.last_seen = datetime.now(pytz.timezone('Europe/Moscow'))
                user_obj.online = True
                local_session.commit()
                current_app.logger.info(f"Updated last_seen for user {user.username}")
        except SQLAlchemyError as e:
            local_session.rollback()
            current_app.logger.error(f"Database error during login: {str(e)}")
        finally:
            local_session.close()

        # Принудительно делаем сессию постоянной перед login_user
        session.permanent = True

        logger.debug(f"🔐 Calling login_user for user: {user.username}")
        login_user(user, remember=form.remember.data, duration=timedelta(days=1))
        logger.debug(f"🔐 login_user completed")

        # Проверка, что текущий пользователь установлен
        if not current_user.is_authenticated:
            logger.warning("❌ ВНИМАНИЕ: current_user не авторизован после login_user!")
            # Принудительное копирование ID пользователя в сессию
            session['_user_id'] = str(user.id)
            logger.debug(f"🔐 Manually set session _user_id: {user.id}")
        else:
            logger.debug(f"✅ current_user is authenticated: {current_user.username}")

        # Сохраняем данные в сессию
        session["user_password_erp"] = user.password
        session["user_id"] = user.id  # Дополнительная страховка

        # Принудительно сохраняем сессию
        session.modified = True

        # Здесь вызываем инициализацию quality базы,
        # чтобы соединение с ней устанавливалось только после авторизации
        init_quality_db()

        check_notifications_and_start_scheduler(user.email, user.id)

        flash(f"Вы вошли как пользователь {user.username}", "success")

        next_page = request.args.get("next")
        if next_page:
            logger.debug(f"🔐 Redirecting to next_page: {next_page}")
            return redirect(next_page)

        logger.debug(f"🔐 Redirecting to users.account")
        return redirect(url_for("users.account"))
    except Exception as e:
        current_app.logger.error(f"Error in handle_successful_login: {str(e)}")
        flash("Произошла ошибка при входе в систему", "error")
        return redirect(url_for("users.login"))


def check_notifications_and_start_scheduler(email, user_id):
    logger.debug(f"[DEBUG] Запуск функции check_notifications_and_start_scheduler для пользователя ID: {user_id}, Email: {email}")

    # Добавляем диагностику уведомлений
    try:
        from blog.notification_service import debug_notifications_for_user
        debug_result = debug_notifications_for_user(email, user_id)
        logger.debug(f"[DEBUG] Результат диагностики уведомлений: {debug_result}")
    except Exception as e:
        logger.error(f"[DEBUG] Ошибка при диагностике уведомлений: {e}")

    # Добавляем подробное логирование перед вызовом функции check_notifications
    try:
        logger.debug(f"[DEBUG] Попытка вызова check_notifications_improved({email}, {user_id})")
        # Используем улучшенную функцию проверки уведомлений
        result = check_notifications_improved(email, user_id)
        logger.debug(f"[DEBUG] Результат вызова check_notifications_improved: {result}")
    except Exception as e:
        logger.error(f"[DEBUG] Ошибка при вызове check_notifications_improved: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # Запускаем задачу планировщика
    try:
        logger.debug(f"[DEBUG] Запуск планировщика start_user_job({email}, {user_id}, 60)")
        start_user_job(email, user_id, 60)
    except Exception as e:
        logger.error(f"[DEBUG] Ошибка при запуске планировщика: {e}")
        import traceback
        logger.error(traceback.format_exc())


def setup_user_as_online(user):
    user.online = True
    db.session.commit()


def setup_user_as_offline(user):
    max_attempts = 3
    current_attempt = 0

    while current_attempt < max_attempts:
        try:
            # Создаем новую сессию для этой операции
            session_maker = sessionmaker(bind=db.engine)
            local_session = session_maker()

            try:
                local_session.execute(text('PRAGMA busy_timeout = 10000'))
                user_obj = local_session.query(User).filter_by(id=user.id).first()
                if user_obj:
                    user_obj.online = False
                    local_session.commit()
                break  # Выходим из цикла если операция успешна
            except SQLAlchemyError as e:
                local_session.rollback()
                current_app.logger.error(f"Attempt {current_attempt + 1} failed: {str(e)}")
                current_attempt += 1
                if current_attempt == max_attempts:
                    raise
                time.sleep(0.5)  # Пауза перед следующей попыткой
            finally:
                local_session.close()

        except Exception as e:
            current_app.logger.error(f"Error setting user offline: {str(e)}")
            break


def start_user_job(current_user_email, current_user_id, timeout):
    job_id = f"notification_job_{current_user_id}"
    logger.debug(f"[SCHEDULER] Попытка добавить/обновить задачу: {job_id} с интервалом {timeout} сек.")
    try:

        # Проверяем доступ к планировщику и модулю notification_service
        from blog.notification_service import check_notifications_improved
        logger.debug(f"[DEBUG] Модуль notification_service доступен, импортирован успешно")
        logger.debug(f"[DEBUG] Функция check_notifications_improved доступна: {hasattr(check_notifications_improved, '__call__')}")

        # Создаем обертку, которая будет выполняться в контексте приложения
        # Получаем реальный объект приложения, так как current_app недоступен в фоновом потоке
        app_obj = current_app._get_current_object()

        def job_function():
            with app_obj.app_context():
                check_notifications_improved(current_user_email, current_user_id)

        scheduler.add_job( # <--- Используем импортированный scheduler
            func=job_function,  # Используем обернутую функцию
            trigger="interval",
            # args теперь не нужны, так как они передаются через замыкание в job_function
            seconds=timeout,
            id=job_id,  # Уникальный идентификатор для задачи этого пользователя
            replace_existing=True,  # Заменяем предыдущую задачу, если она существовала
        )
        logger.debug(f"[SCHEDULER] Задача {job_id} успешно добавлена/обновлена.")
    except Exception as e:
        logger.error(f"[SCHEDULER] Ошибка при добавлении/обновлении задачи {job_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error(f"[SCHEDULER] Ошибка при добавлении/обновлении задачи {job_id}: {e}", exc_info=True)

    if not scheduler.running: # <--- Используем импортированный scheduler
        try:
            scheduler.start() # <--- Используем импортированный scheduler
            logger.debug("[SCHEDULER] Планировщик стартовал.")
        except Exception as e:
            logger.error(f"[SCHEDULER] Ошибка при старте планировщика: {e}")
            logger.error(f"[SCHEDULER] Ошибка при старте планировщика: {e}", exc_info=True)

    # Это сообщение теперь должно появляться благодаря изменению уровня логирования
    logger.info(f"User-specific job {job_id} successfully started or updated.")


def stop_user_job(user_id):
    """Остановка задачи планировщика для конкретного пользователя"""
    try:
        job_id = f"notification_job_{user_id}"
        logger.debug(f"[SCHEDULER] Попытка остановить задачу: {job_id}")

        # global scheduler_instance # Больше не нужна
        if scheduler is None: # <--- Проверяем импортированный scheduler
            logger.warning(f"[SCHEDULER] Планировщик не инициализирован, задача {job_id} не может быть остановлена")
            return

        # Проверяем, существует ли задача
        try:
            job = scheduler.get_job(job_id) # <--- Используем импортированный scheduler
            if job:
                scheduler.remove_job(job_id) # <--- Используем импортированный scheduler
                logger.debug(f"[SCHEDULER] Задача {job_id} успешно остановлена")
                logging.info(f"User-specific job {job_id} successfully stopped.")
        except JobLookupError:
            logger.warning(f"[SCHEDULER] Задача {job_id} не найдена (JobLookupError)")
            logging.warning(f"User-specific job {job_id} was not found when attempting to stop it.")
        except Exception as e:
            logger.error(f"[SCHEDULER] Ошибка при остановке задачи {job_id}: {e}")
            logging.error(f"Error stopping user-specific job {job_id}: {e}")

    except Exception as e:
        logger.error(f"[SCHEDULER] Общая ошибка при остановке задачи пользователя {user_id}: {e}")
        logging.error(f"General error stopping user-specific job for user {user_id}: {e}")


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    try:
        if "user_password_erp" in session:
            user_password_erp = session["user_password_erp"]
        else:
            # Если пароль не в сессии, попробуем получить его из Oracle
            try:
                oracle_connection = connect_oracle(
                    db_host, db_port, db_service_name, db_user_name, db_password
                )
                if oracle_connection:
                    user_password_erp = get_user_erp_password(oracle_connection, current_user.username)
                    if user_password_erp:
                        session["user_password_erp"] = user_password_erp
                        session.modified = True
                    oracle_connection.close()
                else:
                    user_password_erp = None
            except Exception as e:
                current_app.logger.error(f"Ошибка при получении пароля из Oracle: {e}")
                user_password_erp = None

        # Получаем пользователя через текущую сессию
        user_obj = db.session.query(User).filter_by(username=current_user.username).first()
        if user_obj is None:
            flash("Ошибка: пользователь не найден", "error")
            return redirect(url_for("users.login"))

        form = UpdateAccountForm()

        if form.validate_on_submit():
            # Обработка загрузки фото
            if form.picture.data:
                try:
                    picture_file = save_picture(form.picture.data)

                    # Обновляем image_file в объекте из базы данных
                    user_obj.image_file = picture_file

                    # Также обновляем current_user для совместимости
                    current_user.image_file = picture_file

                    # Сохраняем изменения в базе данных
                    db.session.commit()

                    flash('Ваше фото профиля было обновлено!', 'success')
                    current_app.logger.info(f"Фото профиля успешно обновлено для пользователя {current_user.username}: {picture_file}")

                    # Дополнительная проверка обновления в БД
                    db.session.refresh(user_obj)
                    current_app.logger.info(f"Проверка БД - image_file после обновления: {user_obj.image_file}")

                except Exception as e:
                    current_app.logger.error(f"Ошибка при сохранении фото для пользователя {current_user.username}: {e}")
                    flash(f'Ошибка при загрузке фото: {str(e)}. Обратитесь к администратору.', 'error')
            return redirect(url_for('users.account'))

        if request.method == "GET":
            form.username.data = current_user.username

        # Генерируем HTML подпись
        user_details_for_signature = {
            'full_name': user_obj.full_name,
            'position': user_obj.position,
            'department': user_obj.department,
            'phone': user_obj.phone,
            'email': user_obj.email
        }
        email_signature_html = generate_email_signature(user_details_for_signature)

        image_file = url_for(
            "static",
            filename="profile_pics/"
            + current_user.username
            + "/account_img/"
            + current_user.image_file,
        )

        # Получаем список пользователей через ту же сессию
        all_users = []
        if current_user.is_admin:
            all_users = db.session.query(User).all()

        # Проверяем наличие активной push-подписки
        push_subscription_active = PushSubscription.query.filter_by(user_id=current_user.id, is_active=True).first() is not None

        return render_template(
            "account.html",
            title="Профиль",
            form=form,
            image_file=image_file,
            user_obj=user_obj,  # user_obj используется в шаблоне для подписи
            current_user=current_user,  # Оставляем для обратной совместимости, если где-то используется
            user=current_user,  # Добавляем current_user как 'user'
            user_password_erp=user_password_erp,  # Передаем пароль ERP в шаблон
            default_office=user_obj.office if user_obj else "",
            default_email=user_obj.email if user_obj else "",
            default_department=user_obj.department if user_obj else "",
            default_position=user_obj.position if user_obj else "",
            default_phone=user_obj.phone if user_obj else "",
            default_vpn_end_date=user_obj.vpn_end_date if user_obj else "",
            all_users=all_users,
            email_signature_html=email_signature_html,
            push_subscription_active=push_subscription_active,  # Передаем статус подписки в шаблон
            notifications_widget_enabled=user_obj.notifications_widget_enabled  # Передаем состояние уведомлений
        )
    except Exception as e:
        db.session.rollback()  # Откатываем сессию в случае ошибки
        current_app.logger.error(f"Error in account route for user {current_user.username}:", exc_info=True)
        return f"Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже или обратитесь в поддержку. Ошибка: {str(e)}", 500


@users.route("/users")
@login_required
def all_users():
    start_time = time.time()
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 24, type=int)
        per_page = max(6, min(per_page, 60))

        # Загружаем только поля, реально используемые на странице /users
        users_pagination = (
            User.query.options(
                load_only(
                    User.id,
                    User.username,
                    User.email,
                    User.full_name,
                    User.position,
                    User.department,
                    User.office,
                    User.phone,
                    User.last_seen,
                    User.online,
                    User.image_file,
                )
            )
            .order_by(User.last_seen.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        # Используем пакетную валидацию вместо цикла
        from blog.user.utils import batch_validate_user_images
        users_pagination.items = batch_validate_user_images(users_pagination.items)

        # Логируем время выполнения
        execution_time = time.time() - start_time
        current_app.logger.info(
            f"Users page loaded in {execution_time:.3f}s "
            f"(page={users_pagination.page}, per_page={users_pagination.per_page}, total={users_pagination.total})"
        )

        return render_template(
            "users.html", title="Зарегистированные пользователи", users=users_pagination
        )
    except Exception as e:
        execution_time = time.time() - start_time
        current_app.logger.error(f"Ошибка при загрузке страницы пользователей за {execution_time:.3f}s: {e}")
        flash("Произошла ошибка при загрузке списка пользователей", "error")
        users_fallback = type(
            "UsersFallbackPagination",
            (),
            {
                "items": [],
                "total": 0,
                "pages": 0,
                "page": 1,
                "per_page": 24,
                "has_prev": False,
                "has_next": False,
                "prev_num": None,
                "next_num": None,
                "iter_pages": staticmethod(lambda **kwargs: []),
            },
        )()
        return render_template("users.html", title="Пользователи", users=users_fallback)


def _normalize_user_search_text(value):
    if value is None:
        return ""

    text = unicodedata.normalize("NFKD", str(value)).casefold()
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("ё", "е")
    return " ".join(text.split())


@users.get("/api/users/search")
@login_required
def users_search():
    try:
        query_text = request.args.get("q", "", type=str).strip()
        return_to = request.args.get("return_to", "/users", type=str)
        if not return_to.startswith("/users"):
            return_to = "/users"

        if not query_text:
            return jsonify({"success": True, "html": "", "count": 0})

        normalized_query = _normalize_user_search_text(query_text)

        users_data = (
            User.query.options(
                load_only(
                    User.id,
                    User.username,
                    User.email,
                    User.full_name,
                    User.position,
                    User.department,
                    User.office,
                    User.phone,
                    User.last_seen,
                    User.online,
                    User.image_file,
                )
            )
            .order_by(User.last_seen.desc())
            .all()
        )

        from blog.user.utils import batch_validate_user_images
        users_data = batch_validate_user_images(users_data)

        matched_users = []
        for user_obj in users_data:
            searchable_fields = [
                user_obj.username,
                user_obj.email,
                user_obj.full_name,
                user_obj.position,
                user_obj.department,
                user_obj.office,
                user_obj.phone,
            ]
            normalized_blob = " ".join(
                _normalize_user_search_text(field) for field in searchable_fields if field
            )
            if normalized_query in normalized_blob:
                matched_users.append(user_obj)

        rendered_cards = render_template(
            "partials/users_cards.html",
            users=matched_users,
            return_to=return_to,
        )

        return jsonify(
            {
                "success": True,
                "html": rendered_cards,
                "count": len(matched_users),
            }
        )
    except Exception as e:
        current_app.logger.error(f"Ошибка глобального поиска пользователей: {e}")
        return jsonify({"success": False, "html": "", "count": 0}), 500


@users.get("/user/<string:username>")
@login_required
def user_posts(username):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = (
        Post.query.filter_by(author=user)
        .order_by(Post.date_posted.desc())
        .paginate(page=page, per_page=9)
    )

    return render_template(
        "user_posts.html", title="Мои статьи", posts=posts, user=user
    )


@users.get("/user/<int:user_id>")
@login_required
def user_profile(user_id):
    try:
        user_data = User.query.filter_by(id=user_id).first_or_404()
        return_to = request.args.get("next", "", type=str)
        if not return_to.startswith("/users"):
            return_to = ""

        return render_template(
            "profile.html",
            title="Профиль",
            user=user_data,
            count_issues=None,
            return_to=return_to,
        )
    except Exception as e:
        current_app.logger.error(f"Ошибка при обработке профиля пользователя с ID {user_id}: {e}")
        return "Ошибка сервера", 500


def _get_user_issues_count(user_data):
    db_session = Session()
    try:
        # Используем прямой SQL запрос вместо ORM
        if user_data.is_redmine_user:
            sql = text("""
            SELECT COUNT(*) as count
            FROM issues
            WHERE easy_email_to = :email
               OR author_id = :redmine_id
            """)
            result = db_session.execute(
                sql,
                {"email": user_data.email, "redmine_id": user_data.id_redmine_user}
            )
            return result.scalar() or 0

        sql = text("""
        SELECT COUNT(*) as count
        FROM issues
        WHERE easy_email_to = :email
           OR easy_email_to = :alt_email
        """)
        result = db_session.execute(
            sql,
            {
                "email": user_data.email,
                "alt_email": user_data.email.replace("@tez-tour.com", "@msk.tez-tour.com")
            }
        )
        return result.scalar() or 0
    finally:
        db_session.close()


@users.get("/api/user/<int:user_id>/issues-count")
@login_required
def user_issues_count(user_id):
    try:
        user_data = User.query.filter_by(id=user_id).first_or_404()
        count_issues = _get_user_issues_count(user_data)
        return jsonify({"success": True, "count_issues": int(count_issues)})
    except Exception as e:
        current_app.logger.error(f"Ошибка получения количества задач пользователя с ID {user_id}: {e}")
        return jsonify({"success": False, "count_issues": 0}), 500


@users.get("/user-avatar/<string:username>/<string:image_file>")
@login_required
def user_avatar(username, image_file):
    # Basic traversal guard for filename segment.
    if os.path.basename(image_file) != image_file:
        return "Некорректное имя файла", 400

    avatar_dir = os.path.join(
        current_app.root_path,
        "static",
        "profile_pics",
        username,
        "account_img",
    )
    avatar_path = os.path.join(avatar_dir, image_file)

    if os.path.exists(avatar_path):
        return send_from_directory(avatar_dir, image_file)

    default_dir = os.path.join(current_app.root_path, "static", "profile_pics")
    return send_from_directory(default_dir, "default.jpg")


@users.route("/user_delete/<string:username>", methods=["GET", "POST"])
@login_required
def delete_user(username):
    try:
        user = User.query.filter_by(username=username).first_or_404()
        if user and user.id != 1:
            db.session.delete(user)
            db.session.commit()
            full_path = os.path.join(
                os.getcwd(), "blog/static", "profile_pics", user.username
            )

            shutil.rmtree(full_path)

            flash(f"Пользователь {username} был удалён!", "info")
            return redirect(url_for(USERS_ACCOUNT_URL))
    except IntegrityError:
        flash(f"У пользователя {username} есть контент!", "warning")
        return redirect(url_for(USERS_ACCOUNT_URL))
    except FileNotFoundError:
        return redirect(url_for(USERS_ACCOUNT_URL))

    # Добавляем явный возврат для всех случаев
    return redirect(url_for(USERS_ACCOUNT_URL))


def set_last_seen_time(user, timezone_str):
    user_timezone = pytz.timezone(timezone_str)
    utc_time = datetime.now(pytz.utc)
    user.last_seen = utc_time.astimezone(user_timezone)


@users.route("/logout")
@login_required
def logout():
    try:
        # Сохраняем ID пользователя до разлогинивания
        if not isinstance(current_user, AnonymousUserMixin):
            user_id = current_user.id

            # Останавливаем задачи пользователя
            stop_user_job(user_id)

            try:
                # Создаем новую сессию для операции
                session_maker = sessionmaker(bind=db.engine)
                local_session = session_maker()

                # Устанавливаем таймаут
                local_session.execute(text('PRAGMA busy_timeout = 10000'))

                # Получаем пользователя в новой сессии
                user = local_session.query(User).filter_by(id=user_id).first()
                if user:
                    user.last_seen = datetime.now(pytz.timezone('Europe/Moscow'))
                    user.online = False
                    local_session.commit()
                    current_app.logger.info(f"User {user_id} logged out successfully, online status set to False")
            except SQLAlchemyError as e:
                local_session.rollback()
                current_app.logger.error(f"Database error during logout: {str(e)}")
            finally:
                if local_session:
                    local_session.close()

        # Очищаем пользовательскую сессию Flask и выходим из системы
        session.clear()
        logout_user()

    except Exception as e:
        current_app.logger.error(f"Error during logout process: {str(e)}")

    return redirect(url_for('main.home'))


# путь к файлу ERP-приложения
# ERP_FILE_PATH = r"\\10.1.14.10\erp\ERP\TEZERP.exe" #Для Винды
# ERP_FILE_PATH = "/mnt/erp/ERP/TEZERP.exe"

@users.route("/download_erp", methods=["GET"])
def download_erp():
    try:
        logger.info("Attempting to download ERP file from path: %s", ERP_FILE_PATH)
        logger.info("Current working directory: %s", os.getcwd())

        if not os.path.exists(ERP_FILE_PATH):
            logger.error("File not found at path: %s", ERP_FILE_PATH)
            return "File not found", 404

        file_size = os.path.getsize(ERP_FILE_PATH)
        logger.info("File found. Size: %d bytes", file_size)

        response = send_file(
            ERP_FILE_PATH,
            as_attachment=True,
            download_name="TEZERP.exe",
            mimetype="application/vnd.microsoft.portable-executable",
        )

        response.headers["Content-Length"] = str(file_size)
        response.headers["Content-Type"] = "application/vnd.microsoft.portable-executable"

        logger.info("File download initiated successfully")
        return response

    except Exception as e:
        logger.exception("Error during file download: %s", str(e))
        return "Internal server error", 500

@users.route("/check_erp_file", methods=["GET"])
def check_erp_file():
    if os.path.exists(ERP_FILE_PATH):
        file_size = os.path.getsize(ERP_FILE_PATH)
        file_permissions = oct(os.stat(ERP_FILE_PATH).st_mode)[-3:]
        return (
            f"ERP file exists. Size: {file_size} bytes. Permissions: {file_permissions}"
        )
    else:
        return "ERP file not found", 404


def debug_file_path():
    app_root = current_app.root_path
    full_path = os.path.join(app_root, ERP_FILE_PATH)
    return f"""
    ERP_FILE_PATH: {ERP_FILE_PATH}
    Full path: {full_path}
    File exists: {os.path.exists(full_path)}
    Current working directory: {os.getcwd()}
    Application root: {app_root}
    """


@users.errorhandler(404)
def file_not_found(error):
    logging.error("404 ошибка: %s", error)  # Логируем ошибку
    return (
        "ERP-приложение не найдено. Пожалуйста, обратитесь к системному администратору.",
        404,
    )


@users.errorhandler(500)
def internal_error(error=None):  # Добавляем параметр error с значением по умолчанию
    return (
        "Произошла внутренняя ошибка сервера. Пожалуйста, попробуйте позже или обратитесь в службу поддержки.",
        500,
    )


@users.route("/send_password", methods=["POST"])
def send_password():
    # Получаем данные из запроса
    username = request.form.get("Username")
    if not username:
        return jsonify({"message": "Имя пользователя обязательно."}), 400

    # Проверяем, что URL восстановления пароля задан
    url_recovery_password = current_app.config.get("RECOVERY_PASSWORD_URL")
    print(f"[DEBUG] url_recovery_password = '{url_recovery_password}'", flush=True)
    if not url_recovery_password:
        logger.error("RECOVERY_PASSWORD_URL не задан в конфигурации")
        return jsonify({"message": "Сервис восстановления пароля временно недоступен"}), 503

    try:
        payload = {
            "FormCharset": "utf-8",
            "Username": username,
            "Send": "Отправить мне Пароль",
        }
        response = send_request(payload, url_recovery_password)

        if response is None:
            return jsonify({"message": "Ошибка при отправке запроса"}), 500

        if "Ваш пароль отправлен по E-mail" in response.text:
            logger.info("Письмо с восстановлением пароля отправлено на: %s", username)
            return jsonify({"message": "Пароль отправлен на вашу почту"}), 200
        else:
            logger.error("Ошибка при отправке письма: %s", response.text)
            return jsonify({"message": f"{response.text}"}), 500
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")

        # Принудительно пишем traceback в stderr для gunicorn
        print(f"\n=== ERROR in /send_password ===", flush=True)
        print(f"Username: {username}", flush=True)
        print(f"Error: {e}", flush=True)
        traceback.print_exc()
        print("=== END ERROR ===", flush=True)

        return jsonify({"message": "Произошла ошибка", "detail": str(e)}), 500


def send_request(payload, url_recovery_password=None):
    if not url_recovery_password:
        url_recovery_password = current_app.config.get("RECOVERY_PASSWORD_URL")
    try:
        # Для локальной разработки: отключаем прокси, если он вызывает 407
        proxies = {}
        if os.getenv('FLASK_ENV') == 'development':
            proxies = {'http': None, 'https': None}

        response = requests.post(
            url_recovery_password,
            data=payload,
            timeout=10,
            proxies=proxies
        )  # URL страницы восстановления пароля
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response
    except Exception as e:
        logger.error(f"Произошла ошибка при отправке письма: {e}")
        print(f"\n=== ERROR in send_request ===", flush=True)
        print(f"URL: {url_recovery_password}", flush=True)
        print(f"Error: {e}", flush=True)
        traceback.print_exc()
        print("=== END ERROR ===", flush=True)
        return None


@users.route("/update_vpn_date", methods=["POST"])
def update_vpn_date():
    if not current_user.is_authenticated:
        return redirect(url_for("users.login"))
    oracle_connection = None
    try:
        oracle_connection = connect_oracle(
            db_host, db_port, db_service_name, db_user_name, db_password
        )
        if oracle_connection is None:
            return (
                jsonify({"error": "Не удалось подключиться к базе данных Oracle"}),
                500,
            )

        # Получаем актуальную vpn_end_date для текущего пользователя из Oracle
        cursor = oracle_connection.cursor()
        query = """SELECT NVL(tu.vpn_end_date, '') as vpn_end_date, vu.VPN
            FROM erp.v_user vu, erp.t_user tu
            WHERE vu.USER_ID=tu.USER_ID AND (vu.AUTH_PERIOD_TYPE IS NOT NULL
                  AND vu.AUTH_PERIOD_TYPE <> 'Заблокированный сотрудник')
                  AND vu.NAME = :username"""
        cursor.execute(query, username=current_user.username)
        result = cursor.fetchone()

        if result:
            new_vpn_end_date = (
                result[0].strftime("%d.%m.%Y") if result[0] else "<Дата не определена>"
            )
            vpn_status = result[1]  # Получаем значение vu.VPN
        else:
            return jsonify({"error": "Пользователь не найден"}), 404

        # Получаем текущую дату из SQLite
        user = User.query.filter_by(username=current_user.username).first()
        if user:
            current_vpn_end_date = user.vpn_end_date
        else:
            return jsonify({"error": "Пользователь не найден"}), 404

        # Проверяем состояние VPN
        if vpn_status == 0:
            # Обновляем поле user.vpn_end_date на NULL
            user.vpn_end_date = None
            db.session.commit()  # Сохраняем изменения в базе данных
            message = "VPN сейчас отключен"
            return jsonify({"vpn_end_date": None, "message": message})

        # Сравниваем даты и обновляем при необходимости
        if new_vpn_end_date != current_vpn_end_date:
            user.vpn_end_date = new_vpn_end_date
            db.session.commit()
            message = f"Дата доступа к VPN обновлена. Новая дата действует до: {new_vpn_end_date}"
        else:
            message = f"Текущая дата доступа к VPN актуальна: {current_vpn_end_date}"

        # Возвращаем актуальную дату и сообщение в формате JSON
        return jsonify({"vpn_end_date": new_vpn_end_date, "message": message})

    except oracledb.DatabaseError as e:
        return jsonify({"error": f"Ошибка базы данных Oracle: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Произошла ошибка: {str(e)}"}), 500
    finally:
        if oracle_connection:
            oracle_connection.close()


@users.route("/update_user_permissions", methods=["POST"])
@login_required
def update_user_permissions():
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Доступ запрещен"}), 403

    # Изменяем способ получения данных с request.get_json() на request.form
    user_id = request.form.get("userId")
    permission_type = request.form.get("permissionType")
    # Преобразуем строковое значение 'true'/'false' в булево
    value_str = request.form.get("value")
    value = value_str.lower() == 'true' if isinstance(value_str, str) else None


    if user_id is None or permission_type is None or value is None:
        return jsonify({"success": False, "message": "Отсутствуют необходимые параметры: userId, permissionType или value"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"success": False, "message": "userId должен быть числом"}), 400


    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "Пользователь не найден"}), 404

    if permission_type == "admin":
        user.is_admin = value
    elif permission_type == "redmine_user":
        user.is_redmine_user = value
    elif permission_type == "quality_control":
        user.can_access_quality_control = value
    elif permission_type == "contact_center_moscow": # Новое разрешение
        user.can_access_contact_center_moscow = value
    elif permission_type == "redmine_report": # Новое разрешение для отчётов Redmine
        user.can_access_redmine_report = value
    else:
        return jsonify({"success": False, "message": "Неизвестный тип разрешения"}), 400

    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Разрешения обновлены"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка обновления разрешений: {e}")
        return jsonify({"success": False, "message": "Ошибка при обновлении разрешений"}), 500


@users.route("/quality-control")
@login_required
@quality_control_required
def quality_control():
    # код для страницы контроля качества
    return render_template('quality/quality_control.html')


# Тестовые эндпоинты auth_status, session_debug, check_session и login_check удалены


@users.route("/api/system/status")
def system_status():
    """Проверка статуса системы и доступности сервисов"""
    try:
        # Проверка соединения с базой данных
        db_status = "ok" if get_db_connection() else "error"

        # Тут можно добавить проверку других сервисов

        return jsonify({
            "status": "ok",
            "services": {
                "database": db_status,
                # другие сервисы...
            }
        })
    except Exception as e:
        logger.error(f"Ошибка проверки системы: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@users.route("/refresh_password", methods=["POST"])
@login_required
def refresh_password():
    """Обновляет пароль ERP из Oracle и возвращает его"""
    try:
        oracle_connection = connect_oracle(
            db_host, db_port, db_service_name, db_user_name, db_password
        )
        if oracle_connection is None:
            return jsonify({"success": False, "message": "Не удалось подключиться к Oracle"}), 500

        try:
            user_password_erp = get_user_erp_password(oracle_connection, current_user.username)
            if user_password_erp:
                # Обновляем пароль в сессии
                session["user_password_erp"] = user_password_erp
                session.modified = True

                # Обновляем пароль в базе данных
                user = User.query.filter_by(username=current_user.username).first()
                if user:
                    user.password = user_password_erp
                    db.session.commit()

                return jsonify({"success": True, "password": user_password_erp})
            else:
                return jsonify({"success": False, "message": "Пароль не найден в Oracle"}), 404
        finally:
            oracle_connection.close()
    except Exception as e:
        current_app.logger.error(f"Ошибка при обновлении пароля: {e}")
        return jsonify({"success": False, "message": f"Ошибка: {str(e)}"}), 500


@users.route("/api/notifications/toggle", methods=["POST"])
@login_required
@csrf.exempt
def toggle_notifications():
    """Переключает состояние уведомлений пользователя"""
    try:
        # Получаем текущее состояние из запроса
        data = request.get_json()
        enabled = data.get('enabled', None)

        if enabled is None:
            return jsonify({'success': False, 'error': 'Missing enabled parameter'}), 400

        # Получаем пользователя напрямую из базы данных
        user = User.query.filter_by(username=current_user.username).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Логируем текущее состояние
        logger.info(f"Toggle notifications: user={user.username}, current_enabled={user.notifications_widget_enabled}, new_enabled={enabled}")

        # Обновляем состояние в базе данных
        user.notifications_widget_enabled = enabled
        db.session.commit()

        # Обновляем current_user для совместимости
        current_user.notifications_widget_enabled = enabled

        # Логируем результат
        logger.info(f"Toggle notifications: user={user.username}, final_enabled={user.notifications_widget_enabled}")

        return jsonify({
            'success': True,
            'enabled': enabled,
            'message': 'Уведомления включены' if enabled else 'Уведомления отключены'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling notifications: {str(e)}")

        # Принудительно пишем traceback в stderr для gunicorn
        print(f"\n=== ERROR in /api/notifications/toggle ===", flush=True)
        print(f"User: {getattr(current_user, 'username', None)}", flush=True)
        print(f"Error: {e}", flush=True)
        traceback.print_exc()
        print("=== END ERROR ===", flush=True)

        return jsonify({'success': False, 'error': 'Database error', 'detail': str(e)}), 500


@users.route("/api/user/kanban-tips-preference", methods=["POST"])
@login_required
@csrf.exempt
def update_kanban_tips_preference():
    """Обновляет настройку показа баннера Kanban подсказок"""
    try:
        # Получаем данные из запроса
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400

        show_kanban_tips = data.get('show_kanban_tips', None)

        # Нормализуем значение к bool
        if isinstance(show_kanban_tips, str):
            show_kanban_tips = show_kanban_tips.strip().lower() in ('1', 'true', 'yes', 'on')
        elif isinstance(show_kanban_tips, (int, float)):
            show_kanban_tips = bool(show_kanban_tips)

        if show_kanban_tips is None:
            return jsonify({'success': False, 'error': 'Missing show_kanban_tips parameter'}), 400

        # Получаем пользователя напрямую из базы данных
        user = User.query.filter_by(username=current_user.username).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Логируем текущее состояние
        logger.info(f"Update Kanban tips preference: user={user.username}, current_show={getattr(user, 'show_kanban_tips', True)}, new_show={show_kanban_tips}")

        # Обновляем состояние в базе данных (SQLite может отдавать 'database is locked' при нескольких воркерах)
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                user.show_kanban_tips = show_kanban_tips
                db.session.commit()
                break
            except OperationalError as oe:
                db.session.rollback()
                msg = str(oe).lower()
                if 'database is locked' in msg and attempt < max_attempts:
                    logger.warning(f"SQLite database is locked while updating kanban tips (attempt {attempt}/{max_attempts})")
                    time.sleep(0.2 * attempt)
                    continue
                raise

        # Обновляем current_user для совместимости
        if hasattr(current_user, 'show_kanban_tips'):
            current_user.show_kanban_tips = show_kanban_tips

        # Логируем результат
        logger.info(f"Update Kanban tips preference: user={user.username}, final_show={user.show_kanban_tips}")

        return jsonify({
            'success': True,
            'show_kanban_tips': show_kanban_tips,
            'message': 'Настройка баннера сохранена успешно'
        })

    except Exception as e:
        db.session.rollback()
        # Логируем в два места: локальный logger и current_app.logger (gunicorn errorlog)
        logger.exception("Error updating Kanban tips preference")
        try:
            current_app.logger.exception(
                "Error updating Kanban tips preference (user=%s, payload=%s)",
                getattr(current_user, 'username', None),
                request.get_json(silent=True),
            )
        except Exception:
            pass

        # Принудительно пишем traceback в stderr для gunicorn
        print(f"\n=== ERROR in /api/user/kanban-tips-preference ===", flush=True)
        print(f"User: {getattr(current_user, 'username', None)}", flush=True)
        print(f"Error: {e}", flush=True)
        traceback.print_exc()
        print("=== END ERROR ===", flush=True)

        return jsonify({'success': False, 'error': 'Database error', 'detail': str(e)}), 500


@users.route("/api/notifications/status", methods=["GET"])
@login_required
@csrf.exempt
def get_notifications_status():
    """Получает текущее состояние уведомлений пользователя"""
    try:
        # Получаем пользователя напрямую из базы данных
        user = User.query.filter_by(username=current_user.username).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        return jsonify({
            'success': True,
            'enabled': user.notifications_widget_enabled
        })
    except Exception as e:
        logger.error(f"Error getting notifications status: {str(e)}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


# Тестовые эндпоинты test_xmpp_message, debug-photo-upload и fix-image-file удалены
