from flask import flash
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
        try:
            conn_oracle = connect_oracle(
                db_host, db_port, db_service_name, db_user_name, db_password
            )
            if not conn_oracle:
                flash(
                    "Сервис регистрации временно недоступен. Пожалуйста, попробуйте позже.",
                    "danger",
                )
                raise ValidationError(
                    "Registration service temporarily unavailable"
                )

            check_user_erp = verify_credentials(conn_oracle, login_erp, password.data)
            conn_oracle.close()
            if not check_user_erp:
                flash(
                    "Не удалось завершить регистрацию. Ваши данные не соответствуют аккаунту в TEZ ERP.",
                    "danger",
                )
                raise ValidationError(
                    "Registration could not be completed. Your data does not match your TEZ ERP account"
                )
        except ValidationError:
            raise
        except Exception as e:
            flash(
                "Сервис регистрации временно недоступен. Пожалуйста, попробуйте позже.",
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
