from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    MultipleFileField,
)
from wtforms.validators import DataRequired, ValidationError


def validate_file_size(field):
    max_size_in_bytes = 10 * 1024 * 1024  # 10 MB, например
    if field.data and len(field.data.read()) > max_size_in_bytes:
        raise ValidationError('Файл слишком большой.')


class IssueForm(FlaskForm):
    subject = StringField("Тема", validators=[DataRequired()])
    description = TextAreaField(
        "Описание",
        validators=[DataRequired()],
        render_kw={"style": "width: 600px; height: 250px;"},
    )
    upload_files = MultipleFileField(
        "Только файлы (png, pdf, jpg, jpeg, pdf, doc, docx, xls, xlsx)",
        validators=[
            FileAllowed(
                ["png", "pdf", "jpg", "jpeg", "pdf", "doc", "docx", "xls", "xlsx"],
                "Неверный формат!",
            ),
        ],
    )
    submit = SubmitField("Создать")
