import os
from configparser import ConfigParser
import logging
from logging.handlers import RotatingFileHandler
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
)
from flask_login import login_required, current_user
from sqlalchemy import or_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from config import get
from blog import db
from blog.models import Post, User, Notifications, NotificationsAddNotes
from blog.user.forms import AddCommentRedmine
from blog.main.forms import IssueForm
from mysql_db import Issue, Status, Session, get_issue_details, get_quality_connection, CustomValue, Tracker, QualitySession
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
    get_notifications,
    get_notifications_add_notes,
    get_count_notifications,
    get_count_notifications_add_notes,
    check_notifications,
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
from sqlalchemy import text
from sqlalchemy.sql.functions import count

main = Blueprint("main", __name__)

# Настройка логгера
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.ERROR)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        get('logging', 'path', 'app.log'),
        maxBytes=1024*1024*5,  # 5 MB
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

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
    return render_template('index.html', title='Главная')


@main.route("/my-issues", methods=["GET"])
@login_required
def my_issues():
    try:
        # Проверяем уведомления только если пользователь аутентифицирован
        if current_user.is_authenticated:
            check_notifications(g.current_user.email, g.current_user.id)
        return render_template("issues.html", title="Мои заявки")
    except Exception as e:
        current_app.logger.error(f"Error in my_issues: {str(e)}")
        flash("Произошла ошибка при загрузке заявок", "error")
        return redirect(url_for('main.index'))


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
    notifications_data = get_notifications(current_user.id)
    notifications_add_notes_data = get_notifications_add_notes(current_user.id)
    combined_notifications = {}

    if notifications_data is not None:
        combined_notifications["notifications_data"] = notifications_data
    if notifications_add_notes_data is not None:
        combined_notifications["notifications_add_notes_data"] = (
            notifications_add_notes_data
        )
    # Перед возвратом шаблона отправляем уведомление
    # send_notification()
    if combined_notifications:
        return render_template(
            "notifications.html", combined_notifications=combined_notifications
        )
    return abort(500, "Failed to fetch notifications data")


@main.route("/clear-notifications", methods=["POST"])
@login_required
def clear_notifications():
    """Удаляем уведомления после нажатия кнопки 'Очистить уведомления'"""
    try:
        # Используем одну транзакцию для всех операций
        notifications = db.session.query(Notifications).filter_by(
            user_id=current_user.id
        ).all()

        notifications_add_notes = db.session.query(NotificationsAddNotes).filter_by(
            user_id=current_user.id
        ).all()

        # Удаляем все уведомления
        for notification in notifications:
            db.session.delete(notification)

        for notification in notifications_add_notes:
            db.session.delete(notification)

        # Коммитим все изменения разом
        db.session.commit()
        flash("Уведомления успешно удалены", "success")

    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Ошибка при удалении уведомлений: {str(e)}", "error")
        logger.error(f"Ошибка при удалении всех уведомлений: {str(e)}")

    return redirect(url_for("main.my_notifications"))


# Маршрут для удаления уведомления об измнении статуса
@main.route("/delete_notification_status/<int:notification_issue_id>", methods=["POST"])
@login_required
def delete_notification_status(notification_issue_id):
    """Удаление уведомления об измнении статуса после нажатия на иконку корзинки"""
    try:
        # Создаем новую сессию для этой операции
        notification = db.session.query(Notifications).filter_by(
            issue_id=notification_issue_id
        ).first()

        if notification:
            db.session.delete(notification)
            db.session.commit()
            flash("Уведомление успешно удалено", "success")
        else:
            flash("Уведомление не найдено", "error")

        return redirect(url_for("main.my_notifications"))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Ошибка при удалении уведомления: {str(e)}", "error")
        return redirect(url_for("main.my_notifications"))


# Маршрут для удаления уведомления о добавлении комментария
@main.route(
    "/delete_notification_add_notes/<int:notification_add_notes_issue_id>",
    methods=["POST"],
)
@login_required
def delete_notification_add_notes(notification_add_notes_issue_id):
    """Удаление уведомления о добавлении комментария после нажатия на иконку корзинки"""
    try:
        # Создаем новую сессию для этой операции
        notification = db.session.query(NotificationsAddNotes).filter_by(
            issue_id=notification_add_notes_issue_id
        ).first()

        if notification:
            db.session.delete(notification)
            db.session.commit()
            flash("Уведомление успешно удалено", "success")
        else:
            flash("Уведомление не найдено", "error")

        return redirect(url_for("main.my_notifications"))

    except SQLAlchemyError as e:
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

        request_types = [{"id": tracker.id, "name": tracker.name} for tracker in trackers]
        logger.info(f"Successfully fetched {len(request_types)} request types")

        return jsonify({"values": request_types})
    except Exception as e:
        logger.error(f"Error in get_request_types: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'session' in locals():
            session.close()


@main.route('/get-tracker-ids')
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
            'gratitude': next((str(t.id) for t in trackers if t.name == 'Благодарность'), ''),
            'complaint': next((str(t.id) for t in trackers if t.name == 'Жалоба'), ''),
            'question': next((str(t.id) for t in trackers if t.name == 'Вопрос'), ''),
            'suggestion': next((str(t.id) for t in trackers if t.name == 'Предложение'), '')
        }

        return jsonify(tracker_map)
    finally:
        session.close()


@main.route("/get-classification-report", methods=['POST'])
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


@main.route("/get-resorts-report", methods=['POST'])
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
            cursor.callproc('resorts', (date_from, date_to))

            # Получаем результаты
            for result in cursor.stored_results():
                resorts_data = []
                for row in result.fetchall():
                    resort = {
                        'name': row['ResortName'],
                        'complaints': row['JalobaIssueResort_out'],
                        'gratitude': row['GrateIssueResort_out'],
                        'questions': row['QuestionIssueResort_out'],
                        'suggestions': row['OfferIssueResort_out']
                    }
                    resorts_data.append(resort)

                if not resorts_data:
                    return jsonify({"error": "Нет данных за указанный период"}), 404

                # Очищаем временную таблицу с помощью процедуры del_u_Resorts
                cursor.callproc('del_u_Resorts')
                connection.commit()

                return jsonify(resorts_data)

    except Exception as e:
        logger.error(f"Ошибка при получении данных: {str(e)}")
        return jsonify({"error": f"Ошибка при получении данных: {str(e)}"}), 500
    finally:
        if session:
            session.close()


@main.route('/get-resort-types-data', methods=['POST'])
@login_required
def get_resort_types_data():
    try:
        data = request.get_json()
        date_from = data.get('dateFrom')
        date_to = data.get('dateTo')
        tracker_id = data.get('trackerId')

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
                cursor.callproc('up_TypesRequests_ITS', (date_from, date_to, tracker_id))

                results = []
                for result in cursor.stored_results():
                    data = result.fetchall()
                    logger.info(f"Получено записей: {len(data)}")

                    for row in data:
                        try:
                            processed_row = {}
                            for key, value in row.items():
                                try:
                                    if key == 'resort_name':
                                        processed_row[key] = value if value else ''
                                    else:
                                        processed_row[key] = 0 if value is None else int(value)
                                except ValueError as ve:
                                    logger.error(f"Ошибка преобразования значения: key={key}, value={value}, error={str(ve)}")
                                    processed_row[key] = 0
                            results.append(processed_row)
                        except Exception as row_error:
                            logger.error(f"Ошибка обработки строки: {str(row_error)}, row={row}")
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


@main.route('/get-issues', methods=['POST'])
@login_required
def get_issues():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get('assignedTo')
        request_type = data.get('requestType')

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
                    "request_type": request_type
                }
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route('/get-issues-by-type', methods=['POST'])
@login_required
def get_issues_by_type():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get('assignedTo')
        request_type = data.get('requestType')

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
                    "request_type": request_type
                }
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route('/get-issues-by-resort', methods=['POST'])
@login_required
def get_issues_by_resort():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get('assignedTo')
        request_type = data.get('requestType')

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
                    "request_type": request_type
                }
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route('/get-issues-by-employee', methods=['POST'])
@login_required
def get_issues_by_employee():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get('assignedTo')
        request_type = data.get('requestType')

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
                    "request_type": request_type
                }
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route('/get-issues-by-status', methods=['POST'])
@login_required
def get_issues_by_status():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get('assignedTo')
        request_type = data.get('requestType')

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
                    "request_type": request_type
                }
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route('/get-issues-by-priority', methods=['POST'])
@login_required
def get_issues_by_priority():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get('assignedTo')
        request_type = data.get('requestType')

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
                    "request_type": request_type
                }
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route('/get-issues-by-category', methods=['POST'])
@login_required
def get_issues_by_category():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get('assignedTo')
        request_type = data.get('requestType')  # Теперь это ID трекера
        country = data.get('country')


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
                "request_type": request_type
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
    session = None
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({'error': 'Database connection failed', 'count': 0}), 500

        result = session.execute(
            "SELECT COUNT(id) as count FROM issues WHERE project_id=1"
        )

        count = result.scalar()

        return jsonify({'success': True, 'count': count or 0})

    except Exception as e:
        print(f"Error in get_total_issues_count: {str(e)}")
        return jsonify({'error': str(e), 'count': 0}), 500
    finally:
        if session:
            session.close()


@main.route("/get-new-issues-count")
@login_required
def get_new_issues_count():
    session = None
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({'error': 'Database connection failed', 'count': 0}), 500

        result = session.execute(
            "SELECT COUNT(id) as count FROM issues WHERE project_id=1 AND status_id=1"
        )

        count = result.scalar()

        return jsonify({'success': True, 'count': count or 0})

    except Exception as e:
        print(f"Error in get_new_issues_count: {str(e)}")
        return jsonify({'error': str(e), 'count': 0}), 500
    finally:
        if session:
            session.close()


@main.route("/comment-notifications")
@login_required
def get_comment_notifications():
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Пользователь не авторизован'}), 401

        with QualitySession() as session:
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
            notifications = result.mappings().all()

            notifications_data = [{
                'id': row['id'],
                'journalized_id': row['journalized_id'],
                'notes': row['notes'] if row['notes'] else '',
                'created_on': row['created_on'].strftime('%Y-%m-%d %H:%M:%S') if row['created_on'] else '',
                'user_id': row['user_id'],
                'subject': row['subject'] if row['subject'] else ''
            } for row in notifications]

            logger.info(f"Получено {len(notifications_data)} уведомлений")

            return jsonify({
                'success': True,
                'html': render_template('_comment_notifications.html',
                                     notifications=notifications_data),
                'count': len(notifications_data)
            })

    except Exception as e:
        logger.error(f"Ошибка при получении уведомлений: {str(e)}")
        return jsonify({'error': str(e)}), 500


@main.route("/mark-comment-read/<int:journal_id>", methods=['POST'])
@login_required
def mark_comment_read(journal_id):
    try:
        session = QualitySession()
        session.execute(
            text("UPDATE journals SET is_read = 1 WHERE id = :id"),
            {'id': journal_id}
        )
        session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Ошибка при отметке комментария как прочитанного: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@main.route("/mark-all-comments-read", methods=['POST'])
@login_required
def mark_all_comments_read():
    try:
        session = QualitySession()
        session.execute(
            text("UPDATE journals SET is_read = 1 WHERE journalized_type = 'Issue' AND is_read = 0")
        )
        session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Ошибка при отметке всех комментариев как прочитанных: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@main.app_template_filter('datetimeformat')
def datetimeformat(value, format='%d.%m.%Y %H:%M'):
    if value is None:
        return ''
    return value.strftime(format)


@main.route("/get-countries")
@login_required
def get_countries():
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        query = text("SELECT DISTINCT value FROM custom_values WHERE custom_field_id = 24 ORDER BY value ASC")
        result = session.execute(query).fetchall()
        session.close()

        # Формируем список стран (если значение не пустое)
        countries = [row['value'] for row in result if row['value'] is not None]
        return jsonify(countries)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route("/get-new-issues-list")
@login_required
def get_new_issues_list():
    try:
        with QualitySession() as session:
            query = """
                SELECT id, subject, description, created_on
                FROM issues
                WHERE project_id = 1
                AND tracker_id = 1
                AND status_id = 1
                ORDER BY created_on DESC
            """

            result = session.execute(text(query))
            issues = result.mappings().all()

            issues_data = [{
                'id': row['id'],
                'subject': row['subject'],
                'description': row['description'],
                'created_on': row['created_on']
            } for row in issues]

            # Рендерим только содержимое, без структуры сайдбара
            html_content = render_template('_new_issues_content.html', issues=issues_data)

            return jsonify({
                'success': True,
                'html': html_content,
                'count': len(issues_data)
            })

    except Exception as e:
        logger.error(f"Ошибка при получении списка новых обращений: {str(e)}")
        return jsonify({'error': str(e)}), 500


@main.route("/check-connection")
@login_required
def check_connection():
    from blog.utils.connection_monitor import check_database_connections

    is_connected = check_database_connections()
    return jsonify({"connected": is_connected})
