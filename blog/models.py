from datetime import datetime, timezone
from flask import current_app
from flask_login import UserMixin
from sqlalchemy import text
from mysql_db import QualityBase
from blog.db_config import db # Импортируем db из нового файла
from blog import db
# Создаем алиас внутри модуля
db_call = db

def load_user(user_id):
    with current_app.app_context():
        return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    office = db.Column(db.String(120), unique=False, nullable=True)
    image_file = db.Column(db.String(20), nullable=False, default="default.jpg")
    password = db.Column(db.String(60), nullable=False)
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    full_name = db.Column(db.String(255), unique=False, nullable=True)
    department = db.Column(db.String(120), unique=False, nullable=True)
    position = db.Column(db.String(120), unique=False, nullable=True)
    phone = db.Column(db.String(30), unique=False, nullable=True)
    vpn = db.Column(db.Integer, unique=False, nullable=True)
    vpn_end_date = db.Column(
        db.String(30), unique=False, nullable=True, default="<Дата не определена>"
    )
    vacuum_im_notifications = db.Column(db.Integer, default=0)
    online = db.Column(db.Boolean, default=False)
    is_redmine_user = db.Column(db.Boolean, default=False, nullable=False)
    id_redmine_user = db.Column(db.Integer, default=4)
    can_access_quality_control = db.Column(db.Boolean, default=False, nullable=False)
    can_access_contact_center_moscow = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    browser_notifications_enabled = db.Column(db.Boolean, default=False)
    # notifications_widget_enabled = db.Column(db.Boolean, default=True, nullable=False)  # ВРЕМЕННО ОТКЛЮЧЕНО
    last_notification_check = db.Column(db.DateTime, nullable=True)
    posts = db.relationship("Post", backref="author", lazy=True)
    push_subscriptions = db.relationship("PushSubscription", backref="user", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return (f"User({self.id}, {self.username}, {self.email}, {self.image_file}, {self.last_seen}, "
                f"is_admin={self.is_admin}, full_name={self.full_name}, department={self.department}, "
                f"position={self.position}, internal_phone={self.internal_phone}, mobile_phone={self.mobile_phone}, "
                f"is_redmine_user={self.is_redmine_user}, id_redmine_user={self.id_redmine_user}, "
                f"can_access_quality_control={self.can_access_quality_control}, "
                f"can_access_contact_center_moscow={self.can_access_contact_center_moscow}, "
                f"browser_notifications_enabled={self.browser_notifications_enabled})")

    def get_active_tasks(self):
        pass

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text(60), nullable=False)
    image_post = db.Column(db.String(30), nullable=True)  # , default='default.jpg'
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"Post({self.title}, {self.date_posted}, {self.image_post})"

class Notifications(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    issue_id = db.Column(db.Integer)
    old_status = db.Column(db.Text)
    new_status = db.Column(db.Text)
    old_subj = db.Column(db.Text)
    date_created = db.Column(db.DateTime)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(
        self, user_id, issue_id, old_status, new_status, old_subj, date_created
    ):
        self.user_id = user_id
        self.issue_id = issue_id
        self.old_status = old_status
        self.new_status = new_status
        self.old_subj = old_subj
        self.date_created = date_created
        self.is_read = False

class NotificationsAddNotes(db.Model):
    __tablename__ = "notifications_add_notes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    issue_id = db.Column(db.Integer)
    author = db.Column(db.Text)
    notes = db.Column(db.Text)
    date_created = db.Column(db.DateTime)
    source_id = db.Column(db.Integer)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, user_id, issue_id, author, notes, date_created, source_id):
        self.user_id = user_id
        self.issue_id = issue_id
        self.author = author
        self.notes = notes
        self.date_created = date_created
        self.source_id = source_id
        self.is_read = False


class RedmineNotification(db.Model):
    """Модель для хранения уведомлений из Redmine"""
    __tablename__ = "redmine_notifications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    redmine_issue_id = db.Column(db.Integer, nullable=False)
    issue_subject = db.Column(db.Text, nullable=False)
    issue_url = db.Column(db.Text, nullable=False)
    is_group_notification = db.Column(db.Boolean, nullable=False, default=False)
    group_name = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    source_notification_id = db.Column(db.Integer, nullable=False)

    # Связь с пользователем
    user = db.relationship("User", backref="redmine_notifications")

    # Ограничение уникальности для предотвращения дубликатов
    __table_args__ = (
        db.UniqueConstraint('user_id', 'source_notification_id', name='_user_source_uc'),
    )

    def __repr__(self):
        return f"<RedmineNotification id={self.id} user_id={self.user_id} issue_id={self.redmine_issue_id}>"


class PushSubscription(db.Model):
    """Модель для хранения подписок на браузерные пуш-уведомления"""
    __tablename__ = "push_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh_key = db.Column(db.Text, nullable=False)
    auth_key = db.Column(db.Text, nullable=False)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Уникальный индекс для предотвращения дублирования подписок
    __table_args__ = (
        db.UniqueConstraint('user_id', 'endpoint', name='unique_user_endpoint'),
    )

    def __init__(self, user_id, endpoint, p256dh_key, auth_key, user_agent=None):
        self.user_id = user_id
        self.endpoint = endpoint
        self.p256dh_key = p256dh_key
        self.auth_key = auth_key
        self.user_agent = user_agent

    def to_dict(self):
        """Преобразование в словарь для использования с pywebpush"""
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh_key,
                'auth': self.auth_key
            }
        }

    def __repr__(self):
        return f"PushSubscription(user_id={self.user_id}, endpoint={self.endpoint[:50]}..., active={self.is_active})"


# УДАЛЕНО: Oracle-модели AgencyPhone и CallInfo
# Эти таблицы существуют только в Oracle базе данных,
# к ним обращаемся напрямую через SQL запросы


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.String, unique=True, nullable=False)
    from_jid = db.Column(db.String, nullable=False)
    to_jid = db.Column(db.String, nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    type = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default='unread')
    contact_name = db.Column(db.String)
    contact_status = db.Column(db.String)
    is_archived = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<ChatMessage {self.message_id}>"

class AgencyPhone(db.Model):
    """Модель для хранения информации о телефонах агентств"""
    __tablename__ = "T_AGENCY_PHONE"
    __table_args__ = {'extend_existing': True}

    # Объявляем все колонки явно вместо autoload
    agency_id = db.Column("AGENCY_ID", db.Numeric(8, 0), primary_key=True)
    agency_phone = db.Column("AGENCY_PHONE", db.String(1000), nullable=True)
    oc_rowid = db.Column("OC_ROWID", db.String(18), nullable=True)
    o_rowid = db.Column("O_ROWID", db.String(18), nullable=True)


class CallInfo(db.Model):
    __tablename__ = "T_CALL_INFO"
    __table_args__ = {'extend_existing': True}

    id = db.Column("CALL_INFO_ID", db.Integer, primary_key=True, autoincrement=True)
    time_begin = db.Column("TIME_BEGIN", db.DateTime, index=True)
    time_end = db.Column("TIME_END", db.DateTime, index=True)
    agency_id = db.Column("AGENCY_ID", db.String(255), index=True)
    tel_number = db.Column("PHONE_NUMBER", db.String(15), index=True)
    currator = db.Column("CURRATOR", db.String(128), index=True)
    theme = db.Column("THEME", db.String(128), index=True)
    region = db.Column("REGION", db.String(3), index=True)
    agency_manager = db.Column("AGENCY_MANAGER", db.String(50), index=True)
    agency_name = db.Column("AGENCY_NAME", db.String(255), index=True)

class Journal(QualityBase):
    __tablename__ = "journals"
    __bind_key__ = 'quality'

    __table_args__ = (
        db.Index("index_journals_on_created_on", "created_on"),
        db.Index("index_journals_on_easy_type", "easy_type", mysql_length=191),
        db.Index("index_journals_on_journalized_id", "journalized_id"),
        db.Index("index_journals_on_user_id", "user_id"),
        db.Index("journals_journalized_id", "journalized_id", "journalized_type"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8",
            "mysql_collate": "utf8_general_ci",
            "schema": "redmine"
        },
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    journalized_id = db.Column(
        db.Integer,
        nullable=False,
        server_default=text("0")
    )
    journalized_type = db.Column(
        db.String(30),
        nullable=False,
        server_default=text("''")
    )
    user_id = db.Column(
        db.Integer,
        nullable=False,
        server_default=text("0")
    )
    notes = db.Column(db.Text, nullable=True)
    created_on = db.Column(db.DateTime, nullable=False)
    private_notes = db.Column(
        db.Boolean,
        nullable=False,
        server_default=text("0")
    )
    easy_type = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Journal {self.id} (Issue {self.journalized_id})>"
