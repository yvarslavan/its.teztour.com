from flask import flash
import logging
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileSize
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError, Optional, Email
from blog.models import User
from erp_oracle import (
    verify_credentials,
    connect_oracle,
    db_host,
    db_port,
    db_service_name,
    db_user_name,
    db_password,
)


class RegistrationForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[
            DataRequired(),
            Length(
                min=3,
                max=20,
                message="Имя пользователя должно быть в интервале между %(min) и %(max)символами",
            ),
        ],
    )
    # email = StringField('Еmail', validators=[DataRequired(), Email('Некорректный email')])
    password = PasswordField("Пароль", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Подтвердите пароль",
        validators=[
            DataRequired(),
            EqualTo("password", message="Пароли должны совпадать"),
        ],
    )
    submit = SubmitField("Регистрация")

    def validate_username(self, username):
        global login_erp

        user = User.query.filter_by(username=username.data).first()
        login_erp = username.data
        if user:
            flash("Это имя уже занято. Пожалуйста, выберите другое", "danger")
            raise ValidationError(
                "That username is taken. Please choose a different one"
            )

    def validate_password(self, password):
        logger = logging.getLogger(__name__)
        logger.info(f"[REGISTRATION DEBUG] Starting password validation for user: {login_erp}")
        logger.info(f"[REGISTRATION DEBUG] Oracle connection params - host: {db_host}, port: {db_port}, service: {db_service_name}")
        try:
            logger.info("[REGISTRATION DEBUG] Attempting Oracle connection...")
            conn_oracle = connect_oracle(
                db_host, db_port, db_service_name, db_user_name, db_password
            )
            logger.info(f"[REGISTRATION DEBUG] Oracle connection result: {conn_oracle is not None}")
            if not conn_oracle:
                logger.error("[REGISTRATION DEBUG] Oracle connection is None - cannot connect to ERP")
                flash(
                    "Не удалось подключиться к TEZ ERP. "
                    "Проверьте: 1) Включен ли VPN (Cisco Secure Client), "
                    "2) Стабильность интернет-соединения. "
                    "Если проблема persists, попробуйте позже.",
                    "danger",
                )
                raise ValidationError(
                    "Registration service temporarily unavailable"
                )

            logger.info(f"[REGISTRATION DEBUG] Oracle connected, verifying credentials for: {login_erp}")
            check_user_erp = verify_credentials(conn_oracle, login_erp, password.data)
            logger.info(f"[REGISTRATION DEBUG] verify_credentials result: {check_user_erp}")
            conn_oracle.close()
            if not check_user_erp:
                logger.warning(f"[REGISTRATION DEBUG] Credentials verification failed for user: {login_erp}")
                flash(
                    "Не удалось проверить учетные данные в TEZ ERP. "
                    "Возможные причины: неверный логин/пароль, истек срок действия VPN, "
                    "или временные проблемы соединения. Попробуйте снова.",
                    "danger",
                )
                raise ValidationError(
                    "Registration could not be completed. Your data does not match your TEZ ERP account"
                )
            logger.info(f"[REGISTRATION DEBUG] Password validation successful for user: {login_erp}")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"[REGISTRATION DEBUG] Exception during password validation: {str(e)}")
            import traceback
            logger.error(f"[REGISTRATION DEBUG] Traceback: {traceback.format_exc()}")
            flash(
                "Ошибка подключения к TEZ ERP. "
                "Убедитесь, что VPN включен и интернет-соединение стабильно. "
                "Если проблема повторяется, обратитесь в IT поддержку.",
                "danger",
            )
            raise ValidationError(
                "Registration service temporarily unavailable"
            )


class LoginForm(FlaskForm):
    # Убираем Meta класс, чтобы использовать стандартную обработку CSRF
    # CSRF будет управляться глобально через конфигурацию приложения
    # email = StringField('Email', validators=[DataRequired(), Email('Некорректный email')])
    username = StringField(
        "Имя пользователя",
        validators=[
            DataRequired(),
            Length(
                min=3,
                max=20,
                message="Имя пользователя должно быть в интервале между %(min) и %(max)символами.",
            ),
        ],
    )
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")

    def validate_password(self, password):
        # Проверка наличия значения в полях username и password
        if not self.username.data or not password.data:
            flash("Введите имя пользователя и пароль", "danger")
            raise ValidationError("Enter a username and password")


class UpdateAccountForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[DataRequired(), Length(min=4, max=20)],
        render_kw={"readonly": True},
    )
    picture = FileField(
        "Изображение (png, jpg, jpeg)",
        validators=[
            FileAllowed(["jpg", "jpeg", "png"], "Разрешены только изображения в форматах JPG, JPEG и PNG"),
            FileSize(max_size=5 * 1024 * 1024, message="Размер файла не должен превышать 5MB")
        ]
    )
    submit = SubmitField("Обновить", render_kw={"class": "btn-left-align"})

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                flash("Это имя уже занято. Пожалуйста, выберите другое", "danger")
                raise ValidationError(
                    "That username is taken. Please choose a different one"
                )


class AddCommentRedmine(FlaskForm):
    comment = TextAreaField(
        label="Заметка по задаче (переписка с исполнителем):",
        validators=[DataRequired()],
    )


class SendEmailForm(FlaskForm):
    """Форма для отправки email из деталей задачи"""
    sender = StringField(
        label="От кого:",
        validators=[DataRequired()],
        render_kw={"readonly": True, "placeholder": "Email отправителя"}
    )
    recipient = StringField(
        label="Кому:",
        validators=[DataRequired()],
        render_kw={"placeholder": "Введите email получателя"}
    )
    subject = StringField(
        label="Тема:",
        validators=[DataRequired()],
        render_kw={"placeholder": "Введите тему письма"}
    )
    cc = StringField(
        label="Копия (CC):",
        validators=[Optional()],
        render_kw={"placeholder": "Дополнительные получатели"}
    )
    message = TextAreaField(
        label="Сообщение:",
        validators=[DataRequired()],
        render_kw={"rows": 8, "placeholder": "Введите текст сообщения...", "id": "emailMessageField"}
    )
    attachments = FileField(
        label="Вложения:",
        validators=[Optional()],
        render_kw={"multiple": True}
    )
    send_email = BooleanField(
        label="Отправить email",
        default=True
    )
