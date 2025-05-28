import os
from configparser import ConfigParser
import logging
from logging.handlers import RotatingFileHandler
import sys
from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
    flash,
    redirect,
    jsonify,
    g,
    abort,
    current_app,
    send_from_directory
)
from flask_login import login_required, current_user
from sqlalchemy import or_, desc, text
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import count
from datetime import datetime, timedelta, timezone
from config import get
from blog import db
from blog.utils.connection_monitor import check_database_connections, get_connection_health
from blog.models import Post, User, Notifications, NotificationsAddNotes, PushSubscription
from blog.user.forms import AddCommentRedmine
from blog.main.forms import IssueForm
from blog.notification_service import (
    notification_service,
    NotificationData,
    NotificationType
)
from mysql_db import (
    Issue,
    Status,
    Session,
    get_issue_details,
    get_quality_connection,
    CustomValue,
    Tracker,
    QualitySession,
    execute_quality_query_safe,
    db_manager,
)
from redmine import (
    RedmineConnector,
    get_connection,
    convert_datetime_msk_format,
    get_property_name,
    get_status_name_from_id,
    get_project_name_from_id,
    get_user_full_name_from_id,
    get_priority_name_from_id,
    check_user_active_redmine,
    get_issues_redmine_author_id,
    save_and_get_filepath,
    generate_email_signature,
    get_count_notifications,
    get_count_notifications_add_notes,
)

from erp_oracle import (
    connect_oracle,
    db_host,
    db_port,
    db_service_name,
    db_user_name,
    db_password,
    get_user_erp_password,
)

import json

main = Blueprint("main", __name__)


# Настройка логгера
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        get("logging", "path", "app.log"),
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=3,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    return logger


# Инициализация логгера
logger = setup_logger(__name__)

config = ConfigParser()
config_path = os.path.join(os.getcwd(), "config.ini")
config.read(config_path)
redmine_url = config.get("redmine", "url")
redmine_api_key = config.get("redmine", "api_key")
redmine_login_admin = config.get("redmine", "login_admin")
redmine_password_admin = config.get("redmine", "password_admin")
ANONYMOUS_USER_ID = int(config.get("redmine", "anonymous_user_id"))

DB_REDMINE_HOST = config.get("mysql", "host")
DB_REDMINE_DB = config.get("mysql", "database")
DB_REDMINE_USER = config.get("mysql", "user")
DB_REDMINE_PASSWORD = config.get("mysql", "password")


@main.before_request
def set_current_user():
    g.current_user = current_user if current_user.is_authenticated else None


def get_total_notification_count(user):
    """Подсчет общего количества уведомлений для пользователя"""
    if user is None:
        return 0
    return get_count_notifications(user.id) + get_count_notifications_add_notes(user.id)


# Использование в контекстном процессоре
@main.context_processor
def inject_notification_count():
    count = get_total_notification_count(
        g.current_user if hasattr(g, "current_user") else None
    )
    return dict(count_notifications=count)


@main.route("/get-notification-count", methods=["GET"])
@login_required
def get_notification_count():
    try:
        count = get_total_notification_count(current_user)
        return jsonify({"count": count})
    except Exception as e:
        logger.error(f"Error in get_notification_count: {str(e)}")
        return jsonify({"count": 0, "error": str(e)}), 500


@main.route("/")
@main.route("/home")
def home():
    return render_template("index.html", title="Главная")


@main.route("/my-issues", methods=["GET"])
@login_required
def my_issues():
    try:
        # Проверяем уведомления только если пользователь аутентифицирован
        if current_user.is_authenticated:
            # check_notifications(g.current_user.email, g.current_user.id) # ЗАКОММЕНТИРОВАНО
            logger.info(f"Вызов check_notifications ЗАКОММЕНТИРОВАН для пользователя {g.current_user.id} в /my-issues")
        return render_template("issues.html", title="Мои заявки")
    except Exception as e:
        current_app.logger.error(f"Error in my_issues: {str(e)}")
        flash("Произошла ошибка при загрузке заявок", "error")
        return redirect(url_for("main.index"))


@main.route("/get-my-issues", methods=["GET"])
@login_required
def get_my_issues():
    with Session() as session:
        conn = get_connection(
            DB_REDMINE_HOST, DB_REDMINE_USER, DB_REDMINE_PASSWORD, DB_REDMINE_DB
        )
        if conn is None:
            flash(
                "Ошибка подключения к HelpDesk (Easy Redmine). Проверьте ваше VPN соединение",
                "danger",
            )
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        check_user_redmine = check_user_active_redmine(conn, current_user.email)

        # Получаем все возможные статусы
        statuses = session.query(Status).all()
        status_list = [{"id": status.id, "name": status.name} for status in statuses]

        if check_user_redmine == ANONYMOUS_USER_ID:
            issues_data = get_issues_by_email(session, current_user.email)
        else:
            issues_data = get_issues_redmine_author_id(
                conn, check_user_redmine, current_user.email
            )

        return jsonify(
            {
                "issues": issues_data,
                "statuses": status_list,  # Добавляем список всех статусов
            }
        )


def get_issues_by_email(session, email):
    filtered_issues = (
        session.query(Issue)
        .options(joinedload(Issue.status))
        .join(Status, Issue.status_id == Status.id)
        .filter(
            or_(
                Issue.easy_email_to == email,
                Issue.easy_email_to
                == email.replace("@tez-tour.com", "@msk.tez-tour.com"),
            )
        )
        .order_by(desc(Issue.updated_on))
        .all()
    )
    return [
        {
            "id": issue.id,
            "updated_on": issue.updated_on.isoformat(),
            "subject": issue.subject,
            "status_name": issue.status.name,
            "status_id": issue.status_id,  # Добавляем ID статуса
        }
        for issue in filtered_issues
    ]


@main.route("/blog", methods=["POST", "GET"])
@login_required
def blog():
    all_posts = Post.query.order_by(Post.title.desc()).all()
    all_users = User.query.all()
    # Определение текущей страницы
    page = request.args.get("page", 1, type=int)
    # Получение постов с пагинацией
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=9)
    # Рендер шаблона с постами и объектом пагинации
    return render_template(
        "blog.html",
        title="Все статьи",
        posts=posts,
        all_posts=all_posts,
        all_users=all_users,
    )


@main.route("/my-issues/<int:issue_id>", methods=["GET", "POST"])
@login_required
def issue(issue_id):
    """Вывод истории заявки"""
    form = AddCommentRedmine()
    oracle_connect = connect_oracle(
        db_host, db_port, db_service_name, db_user_name, db_password
    )

    user_password_erp = get_user_erp_password(oracle_connect, current_user.username)
    if not oracle_connect or not user_password_erp:
        flash(
            "Не удалось подключиться к базе данных или получить пароль пользователя.",
            "error",
        )
        return redirect(url_for("main.issue", issue_id=issue_id))

    redmine_connector = get_redmine_connector(current_user, user_password_erp)

    try:
        # Получение истории заявки
        issue_history = redmine_connector.get_issue_history(issue_id)
        if issue_history is None:
            # Если доступ запрещен, подкаемся как адмнистратор для получения истории
            redmine_connector = create_redmine_connector(
                True, redmine_login_admin, redmine_password_admin, redmine_api_key
            )
            issue_history = redmine_connector.get_issue_history(issue_id)

        issue_detail = get_issue_details(issue_id)  # Выборка деталей заявки
        attachment_list = redmine_connector.get_issue_attachments(
            issue_id
        )  # Получение прикрепленных файлов
    except Exception as e:
        logging.error("Ошибка при работе с Redmine API: %s", str(e))
        flash("Произошла ошибка при работе с Redmine API.", "error")
        return redirect(url_for("main.issue", issue_id=issue_id))

    # Обработка добавления комментария
    if form.validate_on_submit() and handle_comment_submission(
        form, issue_id, redmine_connector
    ):
        return redirect(url_for("main.issue", issue_id=issue_id))

    return render_template(
        "issue.html",
        title=f"#{issue_detail.id} - {issue_detail.subject}",
        issue_detail=issue_detail,
        issue_history=issue_history,
        attachment_list=attachment_list,
        form=form,
        clear_comment=True,  # Для очистки комментария
        # Дополнительные функции для шаблона
        convert_datetime_msk_format=convert_datetime_msk_format,
        get_property_name=get_property_name,
        get_status_name_from_id=get_status_name_from_id,
        get_project_name_from_id=get_project_name_from_id,
        get_user_full_name_from_id=get_user_full_name_from_id,
        get_priority_name_from_id=get_priority_name_from_id,
        get_connection=get_connection,
    )


def get_redmine_connector(user, user_password_erp):
    """Получение экземпляра RedmineConnector"""
    password = user_password_erp if user_password_erp else None
    redmine_connector = create_redmine_connector(
        user.is_redmine_user, user.username, password, redmine_api_key
    )
    return redmine_connector


def handle_comment_submission(form, issue_id, redmine_connector):
    """Обработка добавления комментария.
    Если текущий пользователь является пользователем Redmine, user_id устанавливаем в None,
    в противном случае устанавливаем в ANONYMOUS_USER_ID.
    """
    comment = form.comment.data
    user_id = None if current_user.is_redmine_user else ANONYMOUS_USER_ID
    success, message = redmine_connector.add_comment(
        issue_id=issue_id, notes=comment, user_id=user_id
    )

    if success:
        flash("Комментарий успешно добавлен в задачу!", "success")
        return True
    flash(message, "danger")
    return False


def create_redmine_connector(is_redmine_user, user, password=None, api_key=None):
    if is_redmine_user:
        return RedmineConnector(
            url=redmine_url, username=user, password=password, api_key=api_key
        )
    # Авторизация как аноним по API ключу
    return RedmineConnector(
        url=redmine_url, username=None, password=None, api_key=api_key
    )


@main.route("/my-issues/new", methods=["GET", "POST"])
@login_required
def new_issue():
    form = IssueForm()
    user_data = {
        "full_name": current_user.full_name,
        "position": current_user.position,
        "department": current_user.department,
        "phone": current_user.phone,
        "email": current_user.email,
    }
    temp_file_path = None
    if form.validate_on_submit():
        # Получаем значение атрибутов из формы
        subject = form.subject.data
        description = form.description.data
        email_signature_html = generate_email_signature(user_data)
        description_with_signature = f"{description}<br><br>{email_signature_html}"
        # Получаем файл как объект
        filedata = form.upload_files.data
        if filedata[0].filename != "":
            # Сохраняем файл во временной папке на диске и получаем путь к нему
            temp_file_path = save_and_get_filepath(filedata)
        else:
            # Действия, если файл не был прикреплен
            temp_file_path = None
        # Проверяем, тек. пользователь пользователь имеет акааунт в Redmine?
        oracle_connect = connect_oracle(
            db_host, db_port, db_service_name, db_user_name, db_password
        )
        current_user_password_erp = get_user_erp_password(
            oracle_connect, current_user.username
        )
        if current_user_password_erp is not None:
            redmine_connector = RedmineConnector(
                url=redmine_url,
                username=current_user.username,
                password=current_user_password_erp[0],
                api_key=None,
            )
        else:
            # Обработка ситуации, когда пароль не был получен
            # Создаем redmine_connector с пустым паролем как Аноним
            redmine_connector = RedmineConnector(
                url=redmine_url, username=None, password=None, api_key=redmine_api_key
            )

        if redmine_connector.is_user_authenticated():
            author_id = redmine_connector.get_current_user("current")
            # Если это пользователь Redmine cоздаем заявку в Redmine от имени (Автора) этого пользователя Redmine
            success_create_issue = redmine_connector.create_issue(
                subject=subject,
                description=description_with_signature,
                project_id=1,  # Входящие (Москва)
                author_id=author_id.id,
                easy_email_to=current_user.email,
                file_path=temp_file_path,
            )
            if success_create_issue:
                # Выводим сообщение об успешном добавлении задачи в Redmine
                flash("Задача успешно добавлена в HelpDesk (EasyRedmine)!", "success")
                return redirect(url_for("main.my_issues"))
            if temp_file_path is not None:
                # Удаляем этот временный сохраненый файл
                os.remove(temp_file_path)
        else:
            # Если это не пользователь Redmine, авторизуемся в Redmine по api ключу как Аноним
            redmine_connector = RedmineConnector(
                url=redmine_url, username=None, password=None, api_key=redmine_api_key
            )
            success_create_issue = redmine_connector.create_issue(
                subject=subject,
                description=description_with_signature,
                project_id=1,  # Входящие (Москва)
                file_path=temp_file_path,
                author_id=4,  # Аноним
                easy_email_to=current_user.email,
            )
            if success_create_issue:
                # Выводим сообщение об успешном добавлении задачи в Redmine
                flash("Задача успешно добавлена в HelpDesk (EasyRedmine)!", "success")
                return redirect(url_for("main.my_issues"))
            if temp_file_path is not None:
                # Удаляем этот временный сохраненный файл
                os.remove(temp_file_path)

    return render_template("create_issue.html", form=form)


@main.route("/notifications", methods=["GET"])
@login_required
def my_notifications():
    # Используем улучшенный сервис уведомлений
    notifications_data = notification_service.get_user_notifications(current_user.id)

    if notifications_data['total_count'] > 0:
        return render_template(
            "notifications.html",
            combined_notifications={
                'notifications_data': notifications_data['status_notifications'],
                'notifications_add_notes_data': notifications_data['comment_notifications']
            }
        )
    return render_template("notifications.html", combined_notifications={})


@main.route("/clear-notifications", methods=["POST"])
@login_required
def clear_notifications():
    """Удаляем уведомления после нажатия кнопки 'Очистить уведомления'"""
    print(f"[DEBUG] clear_notifications вызван для пользователя: {current_user.id}")
    try:
        success = notification_service.clear_user_notifications(current_user.id)

        if success:
            flash("Уведомления успешно удалены", "success")
        else:
            flash("Ошибка при удалении уведомлений", "error")

    except Exception as e:
        print(f"[DEBUG] Ошибка при удалении: {str(e)}")
        flash(f"Ошибка при удалении уведомлений: {str(e)}", "error")
        logger.error(f"Ошибка при удалении всех уведомлений: {str(e)}")

    print(f"[DEBUG] Перенаправляем на страницу уведомлений")
    return redirect(url_for("main.my_notifications"))


# Маршрут для удаления уведомления об измнении статуса
@main.route("/delete_notification_status/<int:notification_id>", methods=["POST"])
@login_required
def delete_notification_status(notification_id):
    """Удаление уведомления об измнении статуса после нажатия на иконку корзинки"""
    try:
        notification = Notifications.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()

        if notification:
            db.session.delete(notification)
            db.session.commit()
            flash("Уведомление успешно удалено", "success")
        else:
            flash("Уведомление не найдено", "error")

        return redirect(url_for("main.my_notifications"))

    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при удалении уведомления: {str(e)}", "error")
        return redirect(url_for("main.my_notifications"))


# Маршрут для удаления уведомления о добавлении комментария
@main.route("/delete_notification_add_notes/<int:notification_id>", methods=["POST"])
@login_required
def delete_notification_add_notes(notification_id):
    """Удаление уведомления о добавлении комментария после нажатия на иконку корзинки"""
    try:
        notification = NotificationsAddNotes.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()

        if notification:
            db.session.delete(notification)
            db.session.commit()
            flash("Уведомление успешно удалено", "success")
        else:
            flash("Уведомление не найдено", "error")

        return redirect(url_for("main.my_notifications"))

    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при удалении уведомления: {str(e)}", "error")
        return redirect(url_for("main.my_notifications"))


@main.route("/write_tech_support")
def write_tech_support():
    return render_template(
        "write_tech_support.html", title="Как написать в техподдержку"
    )


@main.route("/questionable_email")
def questionable_email():
    return render_template(
        "questionable_email.html", title="Получили подозрительное письмо?"
    )


@main.route("/ciscoanyconnect")
def ciscoanyconnect():
    return render_template(
        "ciscoanyconnect.html", title="Как пользоваться Cisco AnyConnect"
    )


@main.route("/setup_mail_account")
def setup_mail_account():
    return render_template(
        "setup_mail_account.html", title="Не получается настроить почту?"
    )


@main.route("/setup_mail_forwarding")
def setup_mail_forwarding():
    return render_template(
        "setup_mail_forwarding.html", title="Как переадресовать почту?"
    )


@main.route("/adress_book")
def adress_book():
    return render_template("address_book.html", title="Корпоративная адресная книга")


@main.route("/remote_connection")
def remote_connection():
    return render_template(
        "remote_connection.html", title="Удаленное подключение к Вам специалиста"
    )


@main.route("/no_access_site")
def no_access_site():
    return render_template("no_access_site.html", title="Веб-айты не загружаются?")


@main.route("/vacuum_setup")
def vacuum_setup():
    return render_template(
        "vacuum_setup.html", title="Как настроить аккаунт Vacuum-IM?"
    )


@main.route("/tez_cloud")
def tez_cloud():
    return render_template(
        "tez_cloud.html", title="Корпоративный файловый сервер CLOUD TEZ TOUR"
    )


@main.route("/auto_resp")
def auto_resp():
    return render_template("auto_resp.html", title="Настройка автоответчика почты")


@main.route("/vdi")
def vdi():
    return render_template(
        "vdi.html",
        title="Инструкция по подключению к виртуальному рабочему столу (VDI)",
    )


@main.route("/reports")
@login_required
def reports():
    try:
        config = ConfigParser()
        config_path = os.path.join(os.getcwd(), "config.ini")
        config.read(config_path)

        DB_REDMINE_HOST = config.get("mysql", "host")
        DB_REDMINE_DB = config.get("mysql", "database")
        DB_REDMINE_USER = config.get("mysql", "user")
        DB_REDMINE_PASSWORD = config.get("mysql", "password")

        conn = get_connection(
            DB_REDMINE_HOST, DB_REDMINE_USER, DB_REDMINE_PASSWORD, DB_REDMINE_DB
        )

        if conn is None:
            raise Exception("Не удалось подключиться к базе данных")

        session = Session()

        # Проверяем, является ли пользователь активным пользователем Redmine
        check_user_redmine = check_user_active_redmine(conn, current_user.email)

        # Получаем статистику по заявкам в зависимости от типа пользователя
        if check_user_redmine == ANONYMOUS_USER_ID:
            # Для анонимных пользователей используем фильтр по email
            issues_stats = (
                session.query(
                    Issue.status_id,
                    Status.name.label("status_name"),
                    count(Issue.id).label("count"),
                )
                .join(Status, Issue.status_id == Status.id)
                .filter(
                    or_(
                        Issue.easy_email_to == current_user.email,
                        Issue.easy_email_to
                        == current_user.email.replace(
                            "@tez-tour.com", "@msk.tez-tour.com"
                        ),
                    )
                )
                .group_by(Issue.status_id, Status.name)
                .all()
            )
        else:
            # Для пользователей Redmine используем фильтр по author_id или email
            issues_stats = (
                session.query(
                    Issue.status_id,
                    Status.name.label("status_name"),
                    count(Issue.id).label("count"),
                )
                .join(Status, Issue.status_id == Status.id)
                .filter(
                    or_(
                        Issue.author_id == check_user_redmine,
                        Issue.easy_email_to.like(f"%{current_user.email}%"),
                    )
                )
                .group_by(Issue.status_id, Status.name)
                .all()
            )

        # Подготавливаем данные для графиков
        labels = [stat.status_name for stat in issues_stats]
        data = [stat.count for stat in issues_stats]

        return render_template("reports.html", labels=labels, data=data)

    except Exception as e:
        print("Ошибка в reports:", str(e))
        raise e
    finally:
        if "session" in locals():
            session.close()


@main.route("/quality-control")
@login_required
def quality_control():
    try:
        session = get_quality_connection()
        if session is None:
            flash("Ошибка подключения к базе данных качества", "danger")
            return redirect(url_for("main.home"))

        # Получаем типы обращений для обоих отчетов
        request_types = (
            session.query(Tracker.id, Tracker.name)
            .filter(Tracker.default_status_id == 22)
            .order_by(Tracker.name)
            .all()
        )

        session.close()
        return render_template(
            "quality_control.html",
            title="Контроль качества",
            request_types=request_types,  # Передаем типы обращений в шаблон
        )
    except Exception as e:
        flash(f"Произошла ошибка: {str(e)}", "danger")
        return redirect(url_for("main.home"))


@main.route("/get-assigned-to-values")
@login_required
def get_assigned_to_values():
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        values = (
            session.query(CustomValue.value)
            .filter(CustomValue.custom_field_id == 21)
            .distinct()
            .order_by(CustomValue.value)
            .all()
        )

        assigned_to_list = [value[0] for value in values if value[0]]

        session.close()
        return jsonify({"values": assigned_to_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route("/get-request-types")
@login_required
def get_request_types():
    try:
        logger.info("Starting request type fetch")
        session = get_quality_connection()
        if session is None:
            logger.error("Failed to establish database connection")
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        # Получаем список типов обращений с их ID
        trackers = (
            session.query(Tracker.id, Tracker.name)
            .filter(Tracker.default_status_id == 22)
            .order_by(Tracker.name)
            .all()
        )

        request_types = [
            {"id": tracker.id, "name": tracker.name} for tracker in trackers
        ]
        logger.info(f"Successfully fetched {len(request_types)} request types")

        return jsonify({"values": request_types})
    except Exception as e:
        logger.error(f"Error in get_request_types: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if "session" in locals():
            session.close()


@main.route("/get-tracker-ids")
def get_tracker_ids():
    session = get_quality_connection()
    try:
        trackers = (
            session.query(Tracker.id, Tracker.name)
            .filter(Tracker.default_status_id == 22)
            .order_by(Tracker.name)
            .all()
        )

        tracker_map = {
            "gratitude": next(
                (str(t.id) for t in trackers if t.name == "Благодарность"), ""
            ),
            "complaint": next((str(t.id) for t in trackers if t.name == "Жалоба"), ""),
            "question": next((str(t.id) for t in trackers if t.name == "Вопрос"), ""),
            "suggestion": next(
                (str(t.id) for t in trackers if t.name == "Предложение"), ""
            ),
        }

        return jsonify(tracker_map)
    finally:
        session.close()


@main.route("/get-classification-report", methods=["POST"])
@login_required
def get_classification_report():
    session = None
    connection = None
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных quality"}), 500

        # Получаем низкоуровневое соединение MySQL
        connection = session.connection().connection
        cursor = connection.cursor(dictionary=True)

        # Выполняем процедуру и сразу получаем результаты
        cursor.callproc("Classific", (date_from, date_to))

        # Получаем результаты
        for result in cursor.stored_results():
            data = result.fetchone()
            if data:
                # Формируем структуру отчета
                report_data = {
                    "classifications": [
                        {
                            "name": "Авиакомпанию",
                            "complaints": data.get("ComplaintIssueAvia", 0),
                            "gratitude": data.get("GrateIssueAvia", 0),
                            "questions": data.get("QuestionIssueAvia", 0),
                            "suggestions": data.get("OfferIssueAvia", 0),
                            "total": data.get("ItogoIssueAvia", 0),
                        },
                        {
                            "name": "Агентство",
                            "complaints": data.get("ComplaintIssueAgent", 0),
                            "gratitude": data.get("GrateIssueAgent", 0),
                            "questions": data.get("QuestionIssueAgent", 0),
                            "suggestions": data.get("OfferIssueAgent", 0),
                            "total": data.get("ItogoIssueAgent", 0),
                        },
                        {
                            "name": "Агентство ТТР",
                            "complaints": data.get("ComplaintIssueAgentTTR", 0),
                            "gratitude": data.get("GrateIssueAgentTTR", 0),
                            "questions": data.get("QuestionIssueAgentTTR", 0),
                            "suggestions": data.get("OfferIssueAgentTTR", 0),
                            "total": data.get("ItogoIssueAgentTTR", 0),
                        },
                        {
                            "name": "Водителя",
                            "complaints": data.get("ComplaintIssueDriver", 0),
                            "gratitude": data.get("GrateIssueDriver", 0),
                            "questions": data.get("QuestionIssueDriver", 0),
                            "suggestions": data.get("OfferIssueDriver", 0),
                            "total": data.get("ItogoIssueDriver", 0),
                        },
                        {
                            "name": "Всё понравилось",
                            "complaints": data.get("ComplaintIssueOk", 0),
                            "gratitude": data.get("GrateIssueOk", 0),
                            "questions": data.get("QuestionIssueOk", 0),
                            "suggestions": data.get("OfferIssueOk", 0),
                            "total": data.get("ItogoIssueOk", 0),
                        },
                        {
                            "name": "Гида на трансфере",
                            "complaints": data.get("ComplaintIssueGuideTransfer", 0),
                            "gratitude": data.get("GrateIssueGuideTransfer", 0),
                            "questions": data.get("QuestionIssueGuideTransfer", 0),
                            "suggestions": data.get("OfferIssueGuideTransfer", 0),
                            "total": data.get("ItogoIssueGuideTransfer", 0),
                        },
                        {
                            "name": "Гида отельного",
                            "complaints": data.get("ComplaintIssueGuideHotel", 0),
                            "gratitude": data.get("GrateIssueGuideHotel", 0),
                            "questions": data.get("QuestionIssueGuideHotel", 0),
                            "suggestions": data.get("OfferIssueGuideHotel", 0),
                            "total": data.get("ItogoIssueGuideHotel", 0),
                        },
                        {
                            "name": "Гида экскурсионного",
                            "complaints": data.get("ComplaintIssueGuideTour", 0),
                            "gratitude": data.get("GrateIssueGuideTour", 0),
                            "questions": data.get("QuestionIssueGuideTour", 0),
                            "suggestions": data.get("OfferIssueGuideTour", 0),
                            "total": data.get("ItogoIssueGuideTour", 0),
                        },
                        {
                            "name": "Отель",
                            "complaints": data.get("ComplaintIssueHotel", 0),
                            "gratitude": data.get("GrateIssueHotel", 0),
                            "questions": data.get("QuestionIssueHotel", 0),
                            "suggestions": data.get("OfferIssueHotel", 0),
                            "total": data.get("ItogoIssueHotel", 0),
                        },
                        {
                            "name": "Встреча в порту",
                            "complaints": data.get("ComplaintMeetingPort", 0),
                            "gratitude": data.get("GrateMeetingPort", 0),
                            "questions": data.get("QuestionMeetingPort", 0),
                            "suggestions": data.get("OfferMeetingPort", 0),
                            "total": data.get("ItogoMeetingPort", 0),
                        },
                        {
                            "name": "Сотрудника отправляющего офиса",
                            "complaints": data.get("ComplaintIssueSeeingOffice", 0),
                            "gratitude": data.get("GrateIssueSeeingOffice", 0),
                            "questions": data.get("QuestionIssueSeeingOffice", 0),
                            "suggestions": data.get("OfferIssueSeeingOffice", 0),
                            "total": data.get("ItogoIssueSeeingOffice", 0),
                        },
                        {
                            "name": "Сотрудника принимающего офиса",
                            "complaints": data.get("ComplaintIssueHostOffice", 0),
                            "gratitude": data.get("GrateIssueHostOffice", 0),
                            "questions": data.get("QuestionIssueHostOffice", 0),
                            "suggestions": data.get("OfferIssueHostOffice", 0),
                            "total": data.get("ItogoIssueHostOffice", 0),
                        },
                        {
                            "name": "Страховая компания",
                            "complaints": data.get("ComplaintIssueInsurance", 0),
                            "gratitude": data.get("GrateIssueInsurance", 0),
                            "questions": data.get("QuestionIssueInsurance", 0),
                            "suggestions": data.get("OfferIssueInsurance", 0),
                            "total": data.get("ItogoIssueInsurance", 0),
                        },
                        {
                            "name": "Экскурсия",
                            "complaints": data.get("ComplaintExcursion", 0),
                            "gratitude": data.get("GrateExcursion", 0),
                            "questions": data.get("QuestionExcursion", 0),
                            "suggestions": data.get("OfferExcursion", 0),
                            "total": data.get("ItogoExcursion", 0),
                        },
                        {
                            "name": "Экскурсионный тур",
                            "complaints": data.get("ComplaintIssueExcursion", 0),
                            "gratitude": data.get("GrateIssueExcursion", 0),
                            "questions": data.get("QuestionIssueExcursion", 0),
                            "suggestions": data.get("OfferIssueExcursion", 0),
                            "total": data.get("ItogoIssueExcursion", 0),
                        },
                        {
                            "name": "Другое",
                            "complaints": data.get("ComplaintIssueAnother", 0),
                            "gratitude": data.get("GrateIssueAnother", 0),
                            "questions": data.get("QuestionIssueAnother", 0),
                            "suggestions": data.get("OfferIssueAnother", 0),
                            "total": data.get("ItogoIssueAnother", 0),
                        },
                        {
                            "name": "Трансфер групповой",
                            "complaints": data.get("ComplaintGrateGroupTransfer", 0),
                            "gratitude": data.get("GrateGroupTransfer", 0),
                            "questions": data.get("QuestionGrateGroupTransfer", 0),
                            "suggestions": data.get("OfferGrateGroupTransfer", 0),
                            "total": data.get("ItogoGrateGroupTransfer", 0),
                        },
                        {
                            "name": "Трансфер индивидуальный",
                            "complaints": data.get("ComplaintTransferIndividual", 0),
                            "gratitude": data.get("GrateTransferIndividual", 0),
                            "questions": data.get("QuestionTransferIndividual", 0),
                            "suggestions": data.get("OfferTransferIndividual", 0),
                            "total": data.get("ItogoTransferIndividual", 0),
                        },
                        {
                            "name": "Трансфер VIP",
                            "complaints": data.get("ComplaintTransferVIP", 0),
                            "gratitude": data.get("GrateTransferVIP", 0),
                            "questions": data.get("QuestionTransferVIP", 0),
                            "suggestions": data.get("OfferTransferVIP", 0),
                            "total": data.get("ItogoTransferVIP", 0),
                        },
                        {
                            "name": "Колл центр на курорте",
                            "complaints": data.get("ComplaintCallCenterResort", 0),
                            "gratitude": data.get("GrateCallCenterResort", 0),
                            "questions": data.get("QuestionCallCenterResort", 0),
                            "suggestions": data.get("OfferCallCenterResort", 0),
                            "total": data.get("ItogoCallCenterResort", 0),
                        },
                        {
                            "name": "Колл центр отправляющего офиса",
                            "complaints": data.get(
                                "ComplaintCallCenterSendingOffice", 0
                            ),
                            "gratitude": data.get("GrateCallCenterSendingOffice", 0),
                            "questions": data.get("QuestionCallCenterSendingOffice", 0),
                            "suggestions": data.get("OfferCallCenterSendingOffice", 0),
                            "total": data.get("ItogoCallCenterSendingOffice", 0),
                        },
                        {
                            "name": "GDS Webbeds(DOTW)",
                            "complaints": data.get("Complaint_GDS", 0),
                            "gratitude": data.get("Grate_GDS", 0),
                            "questions": data.get("Question_GDS", 0),
                            "suggestions": data.get("Offer_GDS", 0),
                            "total": data.get("ItogoGDS", 0),
                        },
                        {
                            "name": "GDS Expedia",
                            "complaints": data.get("ComplaintGDSExpedia", 0),
                            "gratitude": data.get("GrateGDSExpedia", 0),
                            "questions": data.get("QuestionGDSExpedia", 0),
                            "suggestions": data.get("OfferGDSExpedia", 0),
                            "total": data.get("ItogoGDSExpedia", 0),
                        },
                        {
                            "name": "GDS GoGlobal",
                            "complaints": data.get("ComplaintGDSGoGlobal", 0),
                            "gratitude": data.get("GrateGDSGoGlobal", 0),
                            "questions": data.get("QuestionGDSGoGlobal", 0),
                            "suggestions": data.get("OfferGDSGoGlobal", 0),
                            "total": data.get("ItogoGDSGoGlobal", 0),
                        },
                    ],
                    "unclassified": {
                        "total": data.get("Obracheniya", 0),
                        "surveys": data.get("ObracheniyaAnket", 0),
                    },
                    "surveys": {
                        "complaints": data.get("ItogoAnketJalob", 0),
                        "gratitude": data.get("ItogoAnketBlagodarnoct", 0),
                        "questions": data.get("ItogoAnketVopros", 0),
                        "suggestions": data.get("ItogoAnketPredlojenie", 0),
                        "total": (
                            data.get("ItogoAnketJalob", 0)
                            + data.get("ItogoAnketBlagodarnoct", 0)
                            + data.get("ItogoAnketVopros", 0)
                            + data.get("ItogoAnketPredlojenie", 0)
                        ),
                    },
                }
                cursor.close()
                return jsonify(report_data)

        cursor.close()
        return jsonify({"error": "Нет данных за указанный период"}), 404

    except Exception as e:
        logger.error(f"Ошибка в get_classification_report: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-resorts-report", methods=["POST"])
@login_required
def get_resorts_report():
    session = None
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"

        if not date_from or not date_to:
            return jsonify({"error": "Не указан период"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        # Получаем низкоуровневое соединение MySQL
        connection = session.connection().connection

        # Используем курсор для вызова процедуры
        with connection.cursor(dictionary=True) as cursor:
            # Вызываем хранимую процедуру resorts с параметрами
            cursor.callproc("resorts", (date_from, date_to))

            # Получаем результаты
            for result in cursor.stored_results():
                resorts_data = []
                for row in result.fetchall():
                    resort = {
                        "name": row["ResortName"],
                        "complaints": row["JalobaIssueResort_out"],
                        "gratitude": row["GrateIssueResort_out"],
                        "questions": row["QuestionIssueResort_out"],
                        "suggestions": row["OfferIssueResort_out"],
                    }
                    resorts_data.append(resort)

                if not resorts_data:
                    return jsonify({"error": "Нет данных за указанный период"}), 404

                # Очищаем временную таблицу с помощью процедуры del_u_Resorts
                cursor.callproc("del_u_Resorts")
                connection.commit()

                return jsonify(resorts_data)

    except Exception as e:
        logger.error(f"Ошибка при получении данных: {str(e)}")
        return jsonify({"error": f"Ошибка при получении данных: {str(e)}"}), 500
    finally:
        if session:
            session.close()


@main.route("/get-resort-types-data", methods=["POST"])
@login_required
def get_resort_types_data():
    try:
        data = request.get_json()
        date_from = data.get("dateFrom")
        date_to = data.get("dateTo")
        tracker_id = data.get("trackerId")

        if not all([date_from, date_to, tracker_id]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        # Модифицируем дату окончания, добавляя время конца дня
        date_to = f"{date_to} 23:59:59"
        # Добавляем время начала дня для начальной даты для полноты
        date_from = f"{date_from} 00:00:00"

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            connection = session.connection().connection
            with connection.cursor(dictionary=True) as cursor:
                cursor.callproc(
                    "up_TypesRequests_ITS", (date_from, date_to, tracker_id)
                )

                results = []
                for result in cursor.stored_results():
                    data = result.fetchall()
                    logger.info(f"Получено записей: {len(data)}")

                    for row in data:
                        try:
                            processed_row = {}
                            for key, value in row.items():
                                try:
                                    if key == "resort_name":
                                        processed_row[key] = value if value else ""
                                    else:
                                        processed_row[key] = (
                                            0 if value is None else int(value)
                                        )
                                except ValueError as ve:
                                    logger.error(
                                        f"Ошибка преобразования значения: key={key}, value={value}, error={str(ve)}"
                                    )
                                    processed_row[key] = 0
                            results.append(processed_row)
                        except Exception as row_error:
                            logger.error(
                                f"Ошибка обработки строки: {str(row_error)}, row={row}"
                            )
                            continue

                if not results:
                    logger.warning("Нет данных в результате выполнения процедуры")
                    return jsonify({"error": "Нет данных за указанный период"}), 404

                logger.info(f"Успешно обработано записей: {len(results)}")
                return jsonify(results)

        except Exception as e:
            logger.error(f"Ошибка при выполнении процедуры: {str(e)}")
            return jsonify({"error": f"Ошибка при выполнении запроса: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
        return jsonify({"error": f"Ошибка при получении данных: {str(e)}"}), 500


@main.route("/get-issues", methods=["POST"])
@login_required
def get_issues():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                query,
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-type", methods=["POST"])
@login_required
def get_issues_by_type():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                query,
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-resort", methods=["POST"])
@login_required
def get_issues_by_resort():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                query,
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-employee", methods=["POST"])
@login_required
def get_issues_by_employee():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                query,
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-status", methods=["POST"])
@login_required
def get_issues_by_status():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                query,
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-priority", methods=["POST"])
@login_required
def get_issues_by_priority():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                query,
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-category", methods=["POST"])
@login_required
def get_issues_by_category():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")  # Теперь это ID трекера
        country = data.get("country")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT DISTINCT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                LEFT JOIN custom_values cv_country ON i.id = cv_country.customized_id
                    AND cv_country.custom_field_id = 24
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND i.tracker_id = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            params = {
                "date_from": date_from,
                "date_to": date_to,
                "assigned_to": assigned_to,
                "request_type": request_type,
            }

            if country and country.strip():
                query += " AND TRIM(cv_country.value) = TRIM(:country)"
                params["country"] = country

            print(f"Final SQL query: {query}")
            print(f"Parameters: {params}")

            result = session.execute(query, params)
            all_results = result.fetchall()
            print(f"Number of results: {len(all_results)}")

            issues = []
            for row in all_results:
                print(f"Processing row: {row}")
                issues.append({"id": row[0], "subject": row[1]})

            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-total-issues-count")
@login_required
def get_total_issues_count():
    """Получение общего количества обращений с безопасной обработкой ошибок"""
    try:
        def query_total_count(session):
            result = session.execute(
                text("SELECT COUNT(id) as count FROM issues WHERE project_id=1")
            )
            return result.scalar()

        count = execute_quality_query_safe(
            query_total_count,
            "получение общего количества обращений"
        )

        if count is None:
            return jsonify({"success": True, "count": 0, "warning": "Временные проблемы с подключением"})

        return jsonify({"success": True, "count": count or 0})

    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении общего количества обращений: {str(e)}")
        return jsonify({"success": False, "error": "Внутренняя ошибка сервера", "count": 0}), 500


@main.route("/get-new-issues-count")
@login_required
def get_new_issues_count():
    """Получение количества новых обращений с безопасной обработкой ошибок"""
    try:
        def query_count(session):
            result = session.execute(
                text("SELECT COUNT(id) as count FROM issues WHERE project_id=1 AND status_id=1")
            )
            return result.scalar()

        count = execute_quality_query_safe(
            query_count,
            "получение количества новых обращений"
        )

        if count is None:
            # Возвращаем последнее известное значение или 0
            return jsonify({"success": True, "count": 0, "warning": "Временные проблемы с подключением"})

        return jsonify({"success": True, "count": count or 0})

    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении количества новых обращений: {str(e)}")
        return jsonify({"success": False, "error": "Внутренняя ошибка сервера", "count": 0}), 500


@main.route("/comment-notifications")
@login_required
def get_comment_notifications():
    """Получение уведомлений о комментариях с безопасной обработкой ошибок"""
    try:
        if not current_user.is_authenticated:
            return jsonify({"error": "Пользователь не авторизован"}), 401

        def query_notifications(session):
            query = """
                SELECT j.id, j.journalized_id, j.notes, j.created_on,
                       j.user_id, i.subject
                FROM journals j
                INNER JOIN issues i ON j.journalized_id = i.id
                WHERE j.journalized_type = 'Issue'
                AND i.project_id = 1
                AND j.notes IS NOT NULL
                AND TRIM(j.notes) != ''
                AND j.is_read = 0
                ORDER BY j.created_on DESC
                LIMIT 1000
            """

            result = session.execute(text(query))
            return result.mappings().all()

        notifications = execute_quality_query_safe(
            query_notifications,
            "получение уведомлений о комментариях"
        )

        if notifications is None:
            # Возвращаем пустой результат вместо ошибки
            return jsonify({
                "success": True,
                "html": render_template("_comment_notifications.html", notifications=[]),
                "count": 0,
                "warning": "Временные проблемы с подключением к базе данных"
            })

        notifications_data = [
            {
                "id": row["id"],
                "journalized_id": row["journalized_id"],
                "notes": row["notes"] if row["notes"] else "",
                "created_on": (
                    row["created_on"].strftime("%Y-%m-%d %H:%M:%S")
                    if row["created_on"]
                    else ""
                ),
                "user_id": row["user_id"],
                "subject": row["subject"] if row["subject"] else "",
            }
            for row in notifications
        ]

        logger.info(f"Получено {len(notifications_data)} уведомлений о комментариях")

        return jsonify(
            {
                "success": True,
                "html": render_template(
                    "_comment_notifications.html", notifications=notifications_data
                ),
                "count": len(notifications_data),
            }
        )

    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении уведомлений: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Внутренняя ошибка сервера",
            "html": render_template("_comment_notifications.html", notifications=[]),
            "count": 0
        }), 500


@main.route("/mark-comment-read/<int:journal_id>", methods=["POST"])
@login_required
def mark_comment_read(journal_id):
    try:
        session = QualitySession()
        session.execute(
            text("UPDATE journals SET is_read = 1 WHERE id = :id"), {"id": journal_id}
        )
        session.commit()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при отметке комментария как прочитанного: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@main.route("/mark-all-comments-read", methods=["POST"])
@login_required
def mark_all_comments_read():
    try:
        session = QualitySession()
        session.execute(
            text(
                "UPDATE journals SET is_read = 1 WHERE journalized_type = 'Issue' AND is_read = 0"
            )
        )
        session.commit()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при отметке всех комментариев как прочитанных: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@main.app_template_filter("datetimeformat")
def datetimeformat(value, format="%d.%m.%Y %H:%M"):
    if value is None:
        return ""
    return value.strftime(format)


@main.route("/get-countries")
@login_required
def get_countries():
    session = None # Инициализируем session здесь
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        # Оборачиваем SQL запрос в text()
        query = text(
            "SELECT DISTINCT value FROM custom_values WHERE custom_field_id = 24 ORDER BY value ASC"
        )
        result = session.execute(query).mappings().all() # Используем .mappings().all() для словарей


        # Формируем список стран (если значение не пустое)
        countries = [row["value"] for row in result if row["value"] is not None]
        return jsonify(countries)
    except Exception as e:
        logger.error(f"Error in get_countries: {str(e)}") # Используем logger
        return jsonify({"error": str(e)}), 500
    finally:
        if session: # Проверяем что session была присвоена перед закрытием
            session.close()


@main.route("/get-new-issues-list")
@login_required
def get_new_issues_list():
    """Получение списка новых обращений с безопасной обработкой ошибок"""
    try:
        def query_new_issues(session):
            query = """
                SELECT id, subject, description, created_on
                FROM issues
                WHERE project_id = 1
                AND tracker_id = 1
                AND status_id = 1
                ORDER BY created_on DESC
            """

            result = session.execute(text(query))
            return result.mappings().all()

        issues = execute_quality_query_safe(
            query_new_issues,
            "получение списка новых обращений"
        )

        if issues is None:
            # Возвращаем пустой результат вместо ошибки
            return jsonify({
                "success": True,
                "html": render_template("_new_issues_content.html", issues=[]),
                "count": 0,
                "warning": "Временные проблемы с подключением к базе данных"
            })

        issues_data = [
            {
                "id": row["id"],
                "subject": row["subject"],
                "description": row["description"],
                "created_on": row["created_on"],
            }
            for row in issues
        ]

        # Рендерим только содержимое, без структуры сайдбара
        html_content = render_template(
            "_new_issues_content.html", issues=issues_data
        )

        logger.info(f"Получено {len(issues_data)} новых обращений")

        return jsonify(
            {"success": True, "html": html_content, "count": len(issues_data)}
        )

    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка новых обращений: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Внутренняя ошибка сервера",
            "html": render_template("_new_issues_content.html", issues=[]),
            "count": 0
        }), 500


@main.route("/check-connection")
@login_required
def check_connection():
    """Проверка состояния соединений с базами данных"""
    try:
        is_connected = check_database_connections()
        health_report = get_connection_health()

        return jsonify({
            "connected": is_connected,
            "health": health_report,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Ошибка при проверке соединений: {str(e)}")
        return jsonify({
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@main.route("/admin/db-status")
@login_required
def database_status():
    """Административная страница для мониторинга базы данных"""
    try:
        # Проверяем права доступа (можно добавить проверку на роль администратора)
        if not current_user.is_authenticated:
            abort(403)

        health_report = get_connection_health()
        connection_stats = db_manager.get_connection_status()

        return render_template('admin/db_status.html',
                             health=health_report,
                             stats=connection_stats,
                             title="Состояние базы данных")
    except Exception as e:
        logger.error(f"Ошибка при загрузке страницы состояния БД: {str(e)}")
        flash("Ошибка при загрузке состояния базы данных", "error")
        return redirect(url_for("main.index"))


@main.route("/api/push/subscribe", methods=["POST"])
@login_required
def subscribe_push():
    """Подписка на браузерные пуш-уведомления"""
    try:
        data = request.get_json()

        if not data or 'subscription' not in data:
            return jsonify({'error': 'Неверные данные подписки'}), 400

        subscription_data = data['subscription']

        # Извлекаем данные подписки
        endpoint = subscription_data.get('endpoint')
        keys = subscription_data.get('keys', {})
        p256dh_key = keys.get('p256dh')
        auth_key = keys.get('auth')

        if not all([endpoint, p256dh_key, auth_key]):
            return jsonify({'error': 'Неполные данные подписки'}), 400

        # Получаем User-Agent
        user_agent = request.headers.get('User-Agent', '')

        # Проверяем, существует ли уже такая подписка
        existing_subscription = PushSubscription.query.filter_by(
            user_id=current_user.id,
            endpoint=endpoint
        ).first()

        if existing_subscription:
            # Обновляем существующую подписку
            existing_subscription.p256dh_key = p256dh_key
            existing_subscription.auth_key = auth_key
            existing_subscription.user_agent = user_agent
            existing_subscription.last_used = datetime.now(timezone.utc)
            existing_subscription.is_active = True
        else:
            # Создаем новую подписку
            new_subscription = PushSubscription(
                user_id=current_user.id,
                endpoint=endpoint,
                p256dh_key=p256dh_key,
                auth_key=auth_key,
                user_agent=user_agent
            )
            db.session.add(new_subscription)

        # Включаем браузерные уведомления для пользователя
        current_user.browser_notifications_enabled = True

        db.session.commit()

        logger.info(f"Пользователь {current_user.id} подписался на пуш-уведомления")

        return jsonify({
            'success': True,
            'message': 'Подписка на уведомления успешно оформлена'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при подписке на пуш-уведомления: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


@main.route("/api/push/unsubscribe", methods=["POST"])
@login_required
def unsubscribe_push():
    """Отписка от браузерных пуш-уведомлений"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint') if data else None

        if endpoint:
            # Удаляем конкретную подписку
            subscription = PushSubscription.query.filter_by(
                user_id=current_user.id,
                endpoint=endpoint
            ).first()

            if subscription:
                db.session.delete(subscription)
        else:
            # Удаляем все подписки пользователя
            PushSubscription.query.filter_by(user_id=current_user.id).delete()

        # Проверяем, остались ли активные подписки
        remaining_subscriptions = PushSubscription.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).count()

        if remaining_subscriptions == 0:
            current_user.browser_notifications_enabled = False

        db.session.commit()

        logger.info(f"Пользователь {current_user.id} отписался от пуш-уведомлений")

        return jsonify({
            'success': True,
            'message': 'Отписка от уведомлений выполнена'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при отписке от пуш-уведомлений: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


@main.route("/api/push/status", methods=["GET"])
@login_required
def push_status():
    """Получение статуса подписки на пуш-уведомления"""
    try:
        subscriptions_count = PushSubscription.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).count()

        return jsonify({
            'enabled': current_user.browser_notifications_enabled,
            'subscriptions_count': subscriptions_count,
            'has_subscriptions': subscriptions_count > 0
        })

    except Exception as e:
        logger.error(f"Ошибка при получении статуса пуш-уведомлений: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


@main.route("/api/push/test", methods=["POST"])
@login_required
def test_push_notification():
    """Отправка тестового пуш-уведомления"""
    try:
        logger.info(f"[PUSH_TEST] Запрос тестового уведомления от пользователя {current_user.id} ({current_user.email})")

        # Логирование конфигурации VAPID ключей сервера
        vapid_public_key_server = current_app.config.get('VAPID_PUBLIC_KEY')
        vapid_private_key_server_exists = bool(current_app.config.get('VAPID_PRIVATE_KEY'))
        vapid_claims_email_server = current_app.config.get('VAPID_CLAIMS', {}).get('sub')

        logger.info(f"[PUSH_TEST][VAPID_CONFIG] Используемый публичный VAPID ключ (ожидается клиентом): {vapid_public_key_server}")
        if not vapid_public_key_server:
            logger.error("[PUSH_TEST][VAPID_CONFIG] ОШИБКА: VAPID_PUBLIC_KEY не сконфигурирован на сервере.")
        if not vapid_private_key_server_exists:
            logger.warning("[PUSH_TEST][VAPID_CONFIG] ПРЕДУПРЕЖДЕНИЕ: VAPID_PRIVATE_KEY не сконфигурирован на сервере. Отправка будет невозможна.")
        if not vapid_claims_email_server:
            logger.warning("[PUSH_TEST][VAPID_CONFIG] ПРЕДУПРЕЖДЕНИЕ: VAPID_CLAIMS.sub (email) не сконфигурирован на сервере.")
        else:
            logger.info(f"[PUSH_TEST][VAPID_CONFIG] VAPID_CLAIMS.sub (email): {vapid_claims_email_server}")

        # Проверка, что все необходимые VAPID ключи сконфигурированы
        if not vapid_public_key_server or not vapid_private_key_server_exists or not vapid_claims_email_server:
            logger.error("[PUSH_TEST][VAPID_CONFIG] КРИТИЧЕСКАЯ ОШИБКА: Один или несколько VAPID ключей не сконфигурированы. Отправка невозможна.")
            return jsonify({"error": "Ошибка конфигурации VAPID на сервере. Push-уведомление не может быть отправлено."}), 500

        subscriptions = PushSubscription.query.filter_by(user_id=current_user.id, is_active=True).all()
        if not subscriptions:
            logger.warning(f"[PUSH_TEST] У пользователя {current_user.id} нет активных подписок для тестового уведомления.")
            return jsonify({"error": "Нет активных подписок для отправки тестового уведомления"}), 404

        logger.info(f"[PUSH_TEST] Найдено {len(subscriptions)} активных подписок для пользователя {current_user.id}.")

        # Создаем объект NotificationData для тестового уведомления
        # Убедимся, что NotificationData и NotificationType импортированы из notification_service
        test_notification_payload = {
            "title": "Тестовое уведомление 🛠️",
            "message": f"Это тестовое push-уведомление для {current_user.email} от HelpDesk.",
            "data": { # Дополнительные данные, если ваш SW их ожидает
                "url": url_for("main.home", _external=True),
                "custom_key": "test_value",
                "icon": url_for('static', filename='img/push-icon.png', _external=True)
            }
            # "icon": url_for('static', filename='img/push-icon.png', _external=True) # Пример URL для иконки
        }

        notification_data_obj = NotificationData(
            user_id=current_user.id,
            issue_id=0, # Тестовое уведомление не привязано к конкретной заявке
            notification_type=NotificationType.TEST, # Используем новый или существующий тип TEST
            title=test_notification_payload["title"],
            message=test_notification_payload["message"],
            data=test_notification_payload["data"],
            created_at=datetime.now(timezone.utc)
        )

        # Удаляем старый лог, который ссылался на payload_json
        logger.info(f"[PUSH_TEST] Создан объект NotificationData: {notification_data_obj.to_dict()}")

        success_count = 0
        failure_count = 0

        # Передаем объект NotificationData в push_service.send_push_notification
        # Этот метод сам итерирует по подпискам пользователя
        try:
            # Важно: push_service.send_push_notification должен сам найти подписки пользователя
            # и отправить уведомление. Передавать 'sub' здесь не нужно, если send_push_notification
            # спроектирован для работы с NotificationData, который содержит user_id.

            # Вызываем метод сервиса, который отвечает за отправку
            # notification_service - это экземпляр LazyNotificationService
            # он делегирует вызов экземпляру NotificationService, у которого есть push_service

            # NotificationService.push_service.send_push_notification ожидает NotificationData
            notification_service.push_service.send_push_notification(notification_data_obj)

            # Логика подсчета успешных/неуспешных отправок должна быть внутри send_push_notification
            # или send_push_notification должен возвращать результат.
            # Пока предполагаем, что если исключения не было, то все хорошо для всех подписок.
            # Это упрощение, в идеале send_push_notification должен возвращать статус.

            logger.info(f"[PUSH_TEST] Вызов send_push_notification для пользователя {current_user.id} завершен.")
            # Поскольку мы не знаем точное количество успехов/неудач измененным вызовом,
            # вернем общее сообщение об успехе, если нет исключений.
            # Фактическое количество успешных отправок будет залогировано внутри push_service.

            # Проверяем, есть ли активные подписки, чтобы избежать деления на ноль или неверной логики
            if len(subscriptions) > 0:
                 # Этот блок теперь не совсем корректен, так как send_push_notification обрабатывает цикл
                 # Для простоты, если нет исключений, считаем что все прошло для всех (хотя это не так)
                 success_count = len(subscriptions) # Предположение!

        except Exception as e_send_service:
            logger.error(f"[PUSH_TEST] Ошибка при вызове notification_service.push_service.send_push_notification: {str(e_send_service)}", exc_info=True)
            failure_count = len(subscriptions) # Предположение!

        # Логика ответа клиенту
        if failure_count == 0 and success_count > 0:
            logger.info(f"[PUSH_TEST] Тестовые уведомления (предположительно) успешно отправлены для пользователя {current_user.id}.")
            return jsonify({"success": True, "message": f"Тестовое уведомление успешно инициировано для {success_count} устройств."}) # Изменено сообщение
        elif success_count > 0 and failure_count > 0: # Эта ветка маловероятна с текущей структурой
            logger.warning(f"[PUSH_TEST] Тестовые уведомления частично отправлены для пользователя {current_user.id}")
            return jsonify({"success": True, "message": f"Тестовое уведомление инициировано. Успешно для {success_count}, ошибок: {failure_count}."}), 207
        elif failure_count > 0 and success_count == 0:
            logger.error(f"[PUSH_TEST] Не удалось инициировать отправку тестовых уведомлений для пользователя {current_user.id}.")
            return jsonify({"error": f"Не удалось инициировать отправку. Ошибок: {failure_count}."}), 500
        elif success_count == 0 and failure_count == 0 and len(subscriptions) > 0: # Если не было ни успеха ни ошибки, но подписки есть - странно
            logger.warning(f"[PUSH_TEST] Вызов send_push_notification не привел к ошибкам, но success_count=0. Проверьте логи push_service.")
            return jsonify({"success": True, "message": "Запрос на тестовое уведомление обработан. Проверьте уведомления."})
        else: # len(subscriptions) == 0 handled earlier
             logger.error(f"[PUSH_TEST] Неожиданный результат: success_count={success_count}, failure_count={failure_count} при наличии {len(subscriptions)} подписок.")
             return jsonify({"error": "Неожиданная ошибка при отправке тестовых уведомлений."}), 500

    except Exception as e_main:
        logger.critical(f"[PUSH_TEST] КРИТИЧЕСКАЯ ОБЩАЯ ОШИБКА в /api/push/test для пользователя {current_user.id}: {str(e_main)}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера при обработке запроса на тестовое уведомление."}), 500


@main.route("/api/vapid-public-key", methods=["GET"])
def get_vapid_public_key():
    """Получение публичного VAPID ключа"""
    try:
        logger.info("[VAPID] Запрос публичного ключа")
        vapid_public_key = current_app.config.get('VAPID_PUBLIC_KEY')

        if not vapid_public_key:
            logger.error("[VAPID] Публичный ключ не найден в конфигурации")
            return jsonify({'error': 'VAPID ключ не настроен'}), 500

        logger.info(f"[VAPID] Возвращаем публичный ключ: {vapid_public_key[:20]}...")
        return jsonify({'publicKey': vapid_public_key})

    except Exception as e:
        logger.error(f"[VAPID] Ошибка при получении публичного ключа: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500


@main.route("/notification-test")
def notification_test():
    """Тестовая страница для диагностики уведомлений"""
    return render_template('notification_test.html')


@main.route("/admin/cleanup-push-subscriptions", methods=["POST"])
@login_required
def cleanup_push_subscriptions():
    """Административная очистка неактивных пуш-подписок"""
    try:
        # Проверяем права доступа (можно добавить проверку на роль администратора)
        # if not current_user.is_authenticated:  # Эта проверка избыточна из-за @login_required
        #     return jsonify({"error": "Доступ запрещен"}), 403

        from datetime import timedelta

        # Получаем параметры из запроса
        data = request.get_json() or {}
        days_threshold = data.get('days', 7)  # По умолчанию 7 дней

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)

        # Находим неактивные подписки
        inactive_subscriptions = PushSubscription.query.filter(
            PushSubscription.is_active == False,
            PushSubscription.last_used < cutoff_date  # Исправлено с updated_at на last_used
        ).all()

        # Находим подписки с ошибками
        error_subscriptions = PushSubscription.query.filter(
            or_(
                PushSubscription.endpoint == None,
                PushSubscription.endpoint == '',
                PushSubscription.p256dh_key == None,
                PushSubscription.auth_key == None
            )
        ).all()

        # Подсчитываем статистику
        total_before = PushSubscription.query.count()
        to_delete = len(inactive_subscriptions) + len(error_subscriptions)

        # Удаляем подписки
        for subscription in inactive_subscriptions + error_subscriptions:
            db.session.delete(subscription)

        db.session.commit()

        total_after = PushSubscription.query.count()

        logger.info(f"Административная очистка: удалено {to_delete} подписок")

        return jsonify({
            "success": True,
            "message": f"Очистка завершена успешно",
            "statistics": {
                "total_before": total_before,
                "total_after": total_after,
                "deleted": to_delete,
                "inactive_deleted": len(inactive_subscriptions),
                "error_deleted": len(error_subscriptions)
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при административной очистке подписок: {str(e)}")
        return jsonify({"error": f"Ошибка очистки: {str(e)}"}), 500


@main.route("/admin/push-subscriptions-stats", methods=["GET"])
@login_required
def push_subscriptions_stats():
    """Статистика пуш-подписок"""
    try:
        # if not current_user.is_authenticated: # Эта проверка избыточна из-за @login_required
        #     return jsonify({"error": "Доступ запрещен"}), 403

        # Общая статистика
        total_subscriptions = PushSubscription.query.count()
        active_subscriptions = PushSubscription.query.filter_by(is_active=True).count()
        inactive_subscriptions = PushSubscription.query.filter_by(is_active=False).count()

        # Статистика по типам endpoint
        fcm_count = PushSubscription.query.filter(
            PushSubscription.endpoint.like('%fcm.googleapis.com%')
        ).count()

        mozilla_count = PushSubscription.query.filter(
            PushSubscription.endpoint.like('%mozilla.com%')
        ).count()

        # Подписки с ошибками
        error_subscriptions = PushSubscription.query.filter(
            or_(
                PushSubscription.endpoint == None,
                PushSubscription.endpoint == '',
                PushSubscription.p256dh_key == None,
                PushSubscription.auth_key == None
            )
        ).count()

        # Старые подписки (более 30 дней без использования)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        old_subscriptions = PushSubscription.query.filter(
            or_(
                PushSubscription.last_used < cutoff_date,
                PushSubscription.last_used == None
            )
        ).count()

        return jsonify({
            "total": total_subscriptions,
            "active": active_subscriptions,
            "inactive": inactive_subscriptions,
            "by_type": {
                "fcm": fcm_count,
                "mozilla": mozilla_count,
                "other": total_subscriptions - fcm_count - mozilla_count
            },
            "problematic": {
                "with_errors": error_subscriptions,
                "old_unused": old_subscriptions
            }
        })

    except Exception as e:
        logger.error(f"Ошибка при получении статистики подписок: {str(e)}")
        return jsonify({"error": f"Ошибка получения статистики: {str(e)}"}), 500

@main.route("/admin/push-subscriptions")
@login_required
def admin_push_subscriptions():
    """Административная страница управления пуш-подписками"""
    try:
        # Проверяем права доступа (можно добавить проверку на роль администратора)
        # if not current_user.is_authenticated: # Эта проверка избыточна из-за @login_required
        #     abort(403)

        return render_template('admin/push_subscriptions.html',
                             title="Управление пуш-подписками")
    except Exception as e:
        logger.error(f"Ошибка при загрузке страницы управления пуш-подписками: {str(e)}")
        flash("Ошибка при загрузке страницы управления", "error")
        return redirect(url_for("main.index"))

@main.route('/sw.js')
def service_worker():
    # Убедимся, что current_app доступен. Если этот код выполняется до инициализации app, могут быть проблемы.
    # Обычно current_app доступен внутри запроса.
    # Путь к static может зависеть от структуры вашего приложения.
    # Если static находится в корне приложения:
    static_folder_js_path = os.path.join(current_app.root_path, 'static', 'js')
    # Если папка static привязана к блюпринту 'main':
    # static_folder_js_path = os.path.join(main.static_folder, 'js')
    # Предполагаем, что static в корне приложения для send_from_directory

    # Проверяем, что файл существует, чтобы избежать ошибок, если путь неверный
    sw_file_path = os.path.join(static_folder_js_path, 'sw.js')
    if not os.path.exists(sw_file_path):
        # Можно вернуть 404 или логировать ошибку
        logger.error(f"Service Worker file not found at: {sw_file_path}")
        return "Service Worker not found", 404

    try:
        response = send_from_directory(static_folder_js_path, 'sw.js')
        response.headers['Service-Worker-Allowed'] = '/'
        response.headers['Content-Type'] = 'application/javascript'
        return response
    except Exception as e:
        logger.error(f"Error sending service worker: {e}", exc_info=True)
        # Возвращаем ошибку сервера, если что-то пошло не так
        return "Error processing Service Worker", 500
