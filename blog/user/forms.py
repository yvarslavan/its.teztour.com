from flask import flash
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
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
        conn_oracle = connect_oracle(
            db_host, db_port, db_service_name, db_user_name, db_password
        )
        if not conn_oracle:
            flash(
                "Не удалось проверить ваш аккаунт TEZ ERP, возможно нет соединения VPN.",
                "danger",
            )
            raise ValidationError(
                "Your TEZ ERP account could not be verified, there may be no TEZ TOUR VPN connection"
            )

        check_user_erp = verify_credentials(conn_oracle, login_erp, password.data)
        if not check_user_erp:
            flash(
                "Не удалось завершить регистрацию. Ваши данные не соответствуют аккаунту в TEZ ERP.",
                "danger",
            )
            raise ValidationError(
                "Registration could not be completed. Your data does not match your TEZ ERP account"
            )


class LoginForm(FlaskForm):
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
        "Изображение (png, jpg)", validators=[FileAllowed(["jpg", "png"])]
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
