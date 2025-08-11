import shutil
import logging
import os
from configparser import ConfigParser
from datetime import datetime, timedelta
import time
from apscheduler.jobstores.base import JobLookupError
import oracledb
import sqlalchemy
from sqlalchemy import func, or_, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import pytz
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
    jsonify,
    app,
    Response,
)
import requests
from flask_login import current_user, logout_user, login_required, login_user, AnonymousUserMixin
from sqlalchemy.orm import sessionmaker
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
    check_user_active_redmine,
    generate_email_signature,
)
from mysql_db import Issue, Session, init_quality_db
from flask_wtf.csrf import generate_csrf, CSRFProtect
csrf = CSRFProtect()
from blog.call.routes import get_db_connection
import pymysql
from pymysql.cursors import DictCursor
from blog.notification_service import check_notifications_improved


# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

users = Blueprint("users", __name__)
USERS_ACCOUNT_URL = "users.account"
config = ConfigParser()
config_path = os.path.join(os.getcwd(), "config.ini")
config.read(config_path)
url_recovery_password = config.get("RecoveryPassword", "url")
# Получение пути к ERP файлу
ERP_FILE_PATH = config.get("FilePaths", "erp_file_path")
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


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.blog"))
    form = RegistrationForm()

    if form.validate_on_submit():
        oracle_connection = None
        try:
            oracle_connection = connect_oracle(
                db_host, db_port, db_service_name, db_user_name, db_password
            )
            if oracle_connection is None:
                raise oracledb.DatabaseError(
                    "Failed to establish connection to Oracle DB"
                )
            # hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            # Получить данные ERP пользователя
            user_erp_data = get_user_erp_data(
                oracle_connection, form.username.data, form.password.data
            )

            # Проверяем, что данные получены успешно
            if user_erp_data is None:
                flash("Неверные учетные данные или ошибка подключения к ERP", "error")
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
            flash(f"Произошла ошибка при регистрации: {str(e)}", "error")
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
    print(f"Generated CSRF token: {generate_csrf()}")

    if form.validate_on_submit():
        user = authenticate_user(form.username.data, form.password.data)
        if user:
            return handle_successful_login(user, form)
        flash("Войти не удалось. Неверный пароль или пароль мог быть обновлен в ERP. Пожалуйста, попробуйте снова.",
            "error")

    return render_template(
        "login.html", form=form, title="Логин TEZ ERP", legend="Войти"
    )


def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user:
        # Проверяем пароль в SQLite
        if password == user.password:
            # Проверяем актуальность пароля в Oracle
            if check_and_update_password(user, password):
                return user
    return None

def check_and_update_password(user, provided_password):
    try:
        oracle_connection = connect_oracle(
            db_host, db_port, db_service_name, db_user_name, db_password
        )
        if oracle_connection is None:
            raise oracledb.DatabaseError("Failed to establish connection to Oracle DB")

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

        login_user(user, remember=form.remember.data, duration=timedelta(days=1))

        # Проверка, что текущий пользователь установлен
        if not current_user.is_authenticated:
            print("ВНИМАНИЕ: current_user не авторизован после login_user!")
            # Принудительное копирование ID пользователя в сессию
            session['_user_id'] = str(user.id)

        # Сохраняем данные в сессию
        session["user_password_erp"] = user.password
        session["user_id"] = user.id  # Дополнительная страховка

        # Принудительно сохраняем сессию
        session.modified = True

        # Здесь вызываем инициализацию quality базы,
        # чтобы соединение с ней устанавливалось только после авторизации
        init_quality_db()

        check_notifications_and_start_scheduler(user.email, user.id)

        # Принудительно обрабатываем уведомления при входе
        try:
            from blog.notification_service import check_notifications_improved
            notifications_processed = check_notifications_improved(user.email, user.id)
            current_app.logger.info(f"При входе обработано {notifications_processed} уведомлений для пользователя {user.username}")
        except Exception as e:
            current_app.logger.error(f"Ошибка при обработке уведомлений при входе: {e}")

        flash(f"Вы вошли как пользователь {user.username}", "success")

        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)

        return redirect(url_for("users.account"))
    except Exception as e:
        current_app.logger.error(f"Error in handle_successful_login: {str(e)}")
        flash("Произошла ошибка при входе в систему", "error")
        return redirect(url_for("users.login"))


def check_notifications_and_start_scheduler(email, user_id):
    print(f"[DEBUG] Запуск функции check_notifications_and_start_scheduler для пользователя ID: {user_id}, Email: {email}")

    # Добавляем диагностику уведомлений
    try:
        from blog.notification_service import debug_notifications_for_user
        debug_result = debug_notifications_for_user(email, user_id)
        print(f"[DEBUG] Результат диагностики уведомлений: {debug_result}")
    except Exception as e:
        print(f"[DEBUG] Ошибка при диагностике уведомлений: {e}")

    # Добавляем подробное логирование перед вызовом функции check_notifications
    try:
        print(f"[DEBUG] Попытка вызова check_notifications_improved({email}, {user_id})")
        # Используем улучшенную функцию проверки уведомлений
        result = check_notifications_improved(email, user_id)
        print(f"[DEBUG] Результат вызова check_notifications_improved: {result}")
    except Exception as e:
        print(f"[DEBUG] Ошибка при вызове check_notifications_improved: {e}")
        import traceback
        print(traceback.format_exc())

    # Запускаем задачу планировщика
    try:
        print(f"[DEBUG] Запуск планировщика start_user_job({email}, {user_id}, 60)")
        start_user_job(email, user_id, 60)
    except Exception as e:
        print(f"[DEBUG] Ошибка при запуске планировщика: {e}")
        import traceback
        print(traceback.format_exc())


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
    print(f"[SCHEDULER] Попытка добавить/обновить задачу: {job_id} с интервалом {timeout} сек.")
    try:

        # Проверяем доступ к планировщику и модулю notification_service
        from blog.notification_service import check_notifications_improved
        print(f"[DEBUG] Модуль notification_service доступен, импортирован успешно")
        print(f"[DEBUG] Функция check_notifications_improved доступна: {hasattr(check_notifications_improved, '__call__')}")

        # Создаем обертку, которая будет выполняться в контексте приложения
        def job_function():
            with current_app.app_context():
                check_notifications_improved(current_user_email, current_user_id)

        scheduler.add_job( # <--- Используем импортированный scheduler
            func=job_function,  # Используем обернутую функцию
            trigger="interval",
            # args теперь не нужны, так как они передаются через замыкание в job_function
            seconds=timeout,
            id=job_id,  # Уникальный идентификатор для задачи этого пользователя
            replace_existing=True,  # Заменяем предыдущую задачу, если она существовала
        )
        print(f"[SCHEDULER] Задача {job_id} успешно добавлена/обновлена.")
    except Exception as e:
        print(f"[SCHEDULER] Ошибка при добавлении/обновлении задачи {job_id}: {e}")
        import traceback
        print(traceback.format_exc())
        logger.error(f"[SCHEDULER] Ошибка при добавлении/обновлении задачи {job_id}: {e}", exc_info=True)

    if not scheduler.running: # <--- Используем импортированный scheduler
        try:
            scheduler.start() # <--- Используем импортированный scheduler
            print("[SCHEDULER] Планировщик стартовал.")
        except Exception as e:
            print(f"[SCHEDULER] Ошибка при старте планировщика: {e}")
            logger.error(f"[SCHEDULER] Ошибка при старте планировщика: {e}", exc_info=True)

    # Это сообщение теперь должно появляться благодаря изменению уровня логирования
    logger.info(f"User-specific job {job_id} successfully started or updated.")


def stop_user_job(user_id):
    """Остановка задачи планировщика для конкретного пользователя"""
    try:
        job_id = f"notification_job_{user_id}"
        print(f"[SCHEDULER] Попытка остановить задачу: {job_id}")

        # global scheduler_instance # Больше не нужна
        if scheduler is None: # <--- Проверяем импортированный scheduler
            print(f"[SCHEDULER] Планировщик не инициализирован, задача {job_id} не может быть остановлена")
            return

        # Проверяем, существует ли задача
        try:
            job = scheduler.get_job(job_id) # <--- Используем импортированный scheduler
            if job:
                scheduler.remove_job(job_id) # <--- Используем импортированный scheduler
                print(f"[SCHEDULER] Задача {job_id} успешно остановлена")
                logging.info(f"User-specific job {job_id} successfully stopped.")
        except JobLookupError:
            print(f"[SCHEDULER] Задача {job_id} не найдена (JobLookupError)")
            logging.warning(f"User-specific job {job_id} was not found when attempting to stop it.")
        except Exception as e:
            print(f"[SCHEDULER] Ошибка при остановке задачи {job_id}: {e}")
            logging.error(f"Error stopping user-specific job {job_id}: {e}")

    except Exception as e:
        print(f"[SCHEDULER] Общая ошибка при остановке задачи пользователя {user_id}: {e}")
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
    try:
        all_users_data = User.query.order_by(User.last_seen.desc()).all()

        # Проверяем и исправляем пути к изображениям
        for user in all_users_data:
            user.image_file = validate_user_image_path(user)

        return render_template(
            "users.html", title="Зарегистированные пользователи", users=all_users_data
        )
    except Exception as e:
        current_app.logger.error(f"Ошибка при загрузке страницы пользователей: {e}")
        flash("Произошла ошибка при загрузке списка пользователей", "error")
        return render_template("users.html", title="Пользователи", users=[])


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
    db_session = Session()
    try:
        user_data = User.query.filter_by(id=user_id).first_or_404()

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
            count_issues = result.scalar()
        else:
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
            count_issues = result.scalar()
        return render_template(
            "profile.html",
            title="Профиль",
            user=user_data,
            count_issues=count_issues
        )
    except Exception as e:
        current_app.logger.error(f"Ошибка при обработке профиля пользователя с ID {user_id}: {e}")
        return "Ошибка сервера", 500
    finally:
        db_session.close()


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
            # print(full_path)
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

    try:
        payload = {
            "FormCharset": "utf-8",
            "Username": username,
            "Send": "Отправить мне Пароль",
        }
        response = send_request(payload)

        if response is None:
            return jsonify({"message": "Ошибка при отправке запроса"}), 500

        if "Ваш пароль отправлен по E-mail" in response.text:
            print("Письмо с восстановлением пароля отправлено на:", username)
            return jsonify({"message": "Пароль отправлен на вашу почту"}), 200
        else:
            print(f"Ошибка при отправке письма: {response.text}")
            return jsonify({"message": f"{response.text}"}), 500
    except Exception as e:
        print("Произошла ошибка:", e)
        return jsonify({"message": "Произошла ошибка"}), 500


def send_request(payload):
    try:
        response = requests.post(
            url_recovery_password, data=payload, timeout=10
        )  # URL страницы восстановления пароля
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response
    except Exception as e:
        print("Произошла ошибка при отправке письма:", e)


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


@users.route('/auth_status')
def auth_status():
    return jsonify({
        'is_authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
        'user_id': current_user.id if hasattr(current_user, 'id') and current_user.is_authenticated else None,
        'session_keys': list(session.keys()) if session else [],
        'secure_cookie': current_app.config.get('SESSION_COOKIE_SECURE', False),
        'samesite_setting': current_app.config.get('SESSION_COOKIE_SAMESITE', None)
    })


@users.route('/session_debug')
def session_debug():
    csrf_token = generate_csrf()

    return jsonify({
        'session_cookie_secure': current_app.config.get('SESSION_COOKIE_SECURE'),
        'session_cookie_samesite': current_app.config.get('SESSION_COOKIE_SAMESITE'),
        'wtf_csrf_ssl_strict': current_app.config.get('WTF_CSRF_SSL_STRICT'),
        'wtf_csrf_enabled': current_app.config.get('WTF_CSRF_ENABLED'),
        'wtf_csrf_time_limit': current_app.config.get('WTF_CSRF_TIME_LIMIT'),
        'csrf_token_available': True,
        'secret_key_set': current_app.secret_key is not None,
    })


@users.route('/check_session')
def check_session():
    """Отладочный метод для проверки сессии"""
    try:
        # Пробуем принудительно создать сессию
        if '_id' not in session:
            session['test_value'] = 'проверка сессии'
            session.modified = True

        # Безопасное получение данных о пользователе
        is_authenticated = current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False
        user_id = current_user.id if is_authenticated else None

        # Безопасное получение настроек Flask
        flask_session_enabled = current_app.config.get('SESSION_TYPE') == 'filesystem'

        session_data = {
            'authenticated': is_authenticated,
            'user_id': user_id,
            'session_keys': list(session.keys()) if session else [],
            'session_values': {k: str(v) for k, v in session.items()} if session else {},
            'session_id': request.cookies.get('helpdesk_session', None),
            'cookies': {k: v for k, v in request.cookies.items()},
            'flask_session_enabled': flask_session_enabled
        }
        return jsonify(session_data)
    except Exception as e:
        return jsonify({'error': str(e), 'message': 'Ошибка при проверке сессии'})


@users.route('/login_check')
def login_check():
    """Простая проверка авторизации"""
    if current_user.is_authenticated:
        return f"Вы авторизованы как {current_user.username}"
    else:
        return "Вы не авторизованы"


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
        return jsonify({'success': False, 'error': 'Database error'}), 500


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


@users.route("/test_xmpp_message", methods=["GET"])
@login_required
def test_xmpp_message():
    # Этот роут будет удален или закомментирован
    return "Функция недоступна", 404


@users.route("/debug-photo-upload", methods=["GET"])
@login_required
def debug_photo_upload():
    """Диагностика загрузки фото профиля"""
    import os
    import stat

    results = []
    username = current_user.username

    # Проверяем базовую директорию
    base_path = os.path.join(current_app.root_path, 'static', 'profile_pics')
    results.append(f"🔍 Базовая директория: {base_path}")
    results.append(f"   Существует: {os.path.exists(base_path)}")

    if os.path.exists(base_path):
        try:
            base_perms = oct(os.stat(base_path).st_mode)[-3:]
            results.append(f"   Права доступа: {base_perms}")
        except Exception as e:
            results.append(f"   Ошибка получения прав: {e}")

    # Проверяем директорию пользователя
    user_path = os.path.join(base_path, username)
    results.append(f"🔍 Директория пользователя: {user_path}")
    results.append(f"   Существует: {os.path.exists(user_path)}")

    if os.path.exists(user_path):
        try:
            user_perms = oct(os.stat(user_path).st_mode)[-3:]
            results.append(f"   Права доступа: {user_perms}")
        except Exception as e:
            results.append(f"   Ошибка получения прав: {e}")

    # Проверяем директорию account_img
    account_img_path = os.path.join(user_path, 'account_img')
    results.append(f"🔍 Директория account_img: {account_img_path}")
    results.append(f"   Существует: {os.path.exists(account_img_path)}")

    if os.path.exists(account_img_path):
        try:
            account_perms = oct(os.stat(account_img_path).st_mode)[-3:]
            results.append(f"   Права доступа: {account_perms}")

            # Список файлов в директории
            files = os.listdir(account_img_path)
            results.append(f"   Файлы в директории: {files}")

            for file in files:
                file_path = os.path.join(account_img_path, file)
                try:
                    file_perms = oct(os.stat(file_path).st_mode)[-3:]
                    file_size = os.path.getsize(file_path)
                    results.append(f"   {file}: права {file_perms}, размер {file_size} байт")
                except Exception as e:
                    results.append(f"   {file}: ошибка {e}")

        except Exception as e:
            results.append(f"   Ошибка получения прав: {e}")

    # Проверяем текущий image_file
    results.append(f"🔍 Текущий image_file в БД: {current_user.image_file}")

    # Проверяем полный путь к файлу
    if current_user.image_file and current_user.image_file != 'default.jpg':
        full_image_path = os.path.join(account_img_path, current_user.image_file)
        results.append(f"🔍 Полный путь к файлу: {full_image_path}")
        results.append(f"   Существует: {os.path.exists(full_image_path)}")

        if os.path.exists(full_image_path):
            try:
                file_perms = oct(os.stat(full_image_path).st_mode)[-3:]
                file_size = os.path.getsize(full_image_path)
                results.append(f"   Права доступа: {file_perms}, размер: {file_size} байт")
            except Exception as e:
                results.append(f"   Ошибка получения информации: {e}")

    # Проверяем права на запись
    results.append(f"🔍 Проверка прав на запись:")
    try:
        test_file = os.path.join(account_img_path, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        results.append("   ✅ Права на запись есть")
    except Exception as e:
        results.append(f"   ❌ Ошибка записи: {e}")

    return f"""
    <html>
    <head><title>Диагностика загрузки фото</title></head>
    <body style="font-family: Arial; margin: 20px;">
        <h2>Диагностика загрузки фото для {username}</h2>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
            {'<br>'.join(results)}
        </div>
        <hr>
        <h3>Действия:</h3>
        <p><a href="/fix-image-file" style="background: #007bff; color: white; padding: 10px; text-decoration: none; border-radius: 5px;">Исправить image_file в БД</a></p>
    </body>
    </html>
    """


@users.route("/fix-image-file", methods=["GET"])
@login_required
def fix_image_file():
    """Исправление image_file в базе данных"""
    import os

    username = current_user.username
    results = []

    try:
        # Получаем пользователя из БД
        user = User.query.filter_by(username=username).first()
        if not user:
            return "Пользователь не найден", 404

        results.append(f"🔍 Исправление image_file для пользователя {username}")
        results.append(f"   Текущий image_file в БД: {user.image_file}")

        # Проверяем директорию с файлами
        account_img_path = os.path.join(current_app.root_path, 'static', 'profile_pics', username, 'account_img')

        if os.path.exists(account_img_path):
            files = os.listdir(account_img_path)
            results.append(f"   Файлы в директории: {files}")

            if files:
                # Берем самый новый файл (по времени изменения)
                newest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(account_img_path, f)))
                results.append(f"   Самый новый файл: {newest_file}")

                # Обновляем в БД
                old_image_file = user.image_file
                user.image_file = newest_file
                db.session.commit()

                results.append(f"   ✅ Обновлено в БД: {old_image_file} → {newest_file}")

                # Обновляем current_user
                current_user.image_file = newest_file

                results.append("   ✅ current_user также обновлен")
            else:
                results.append("   ❌ Файлы не найдены в директории")
        else:
            results.append("   ❌ Директория не существует")

    except Exception as e:
        results.append(f"   ❌ Ошибка: {e}")
        current_app.logger.error(f"Ошибка при исправлении image_file для {username}: {e}")

    return f"""
    <html>
    <head><title>Исправление image_file</title></head>
    <body style="font-family: Arial; margin: 20px;">
        <h2>Исправление image_file</h2>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
            {'<br>'.join(results)}
        </div>
        <hr>
        <p><a href="/account" style="background: #28a745; color: white; padding: 10px; text-decoration: none; border-radius: 5px;">Вернуться в профиль</a></p>
    </body>
    </html>
    """
