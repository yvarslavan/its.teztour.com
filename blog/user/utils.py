import os
import random
import secrets
import shutil

from PIL import Image
from flask import current_app
from flask_login import current_user
from functools import wraps
from flask import flash, redirect, url_for


def random_avatar(user):
    full_path = os.path.join(os.getcwd(), 'blog/static', 'profile_pics', user, 'account_img')
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    full_path_avatar = os.path.join(os.getcwd(), 'blog/static/profile_pics/Avatars/')
    list_avatars = os.listdir(full_path_avatar)
    lst = random.choice(list_avatars)
    random_image_file = os.path.join(full_path_avatar, lst)
    print('random_image_file', random_image_file)
    shutil.copy(random_image_file, full_path)
    print('full_path', full_path)
    return lst


def save_picture(form_picture):
    random_hex = secrets.token_hex(10)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    full_path = os.path.join(current_app.root_path, 'static', 'profile_pics/', current_user.username, 'account_img')

    # Создаем директорию с правильными правами
    if not os.path.exists(full_path):
        try:
            os.makedirs(full_path, exist_ok=True)
            # Устанавливаем права 755 для директории (rwxr-xr-x)
            os.chmod(full_path, 0o755)
            current_app.logger.info(f"Создана директория: {full_path}")
        except Exception as e:
            current_app.logger.error(f"Ошибка создания директории {full_path}: {e}")
            raise e

    picture_path = os.path.join(full_path, picture_fn)
    output_size = (600, 600)

    try:
        i = Image.open(form_picture)
        current_app.logger.info(f"Открыто изображение: формат={i.format}, режим={i.mode}, размер={i.size}")

        # Конвертируем изображение в RGB режим для совместимости с JPEG
        if i.mode in ('RGBA', 'LA', 'P'):
            current_app.logger.info(f"Конвертируем изображение из режима {i.mode} в RGB")
            # Создаем белый фон для прозрачных изображений
            background = Image.new('RGB', i.size, 0xFFFFFF)
            if i.mode == 'P':
                i = i.convert('RGBA')
            background.paste(i, mask=i.split()[-1] if i.mode == 'RGBA' else None)
            i = background
        elif i.mode != 'RGB':
            current_app.logger.info(f"Конвертируем изображение из режима {i.mode} в RGB")
            i = i.convert('RGB')

        # Изменяем размер
        i.thumbnail(output_size, Image.Resampling.LANCZOS)

        # Определяем формат для сохранения
        _, file_ext = os.path.splitext(form_picture.filename)
        if file_ext.lower() in ['.jpg', '.jpeg']:
            # Сохраняем как JPEG
            i.save(picture_path, 'JPEG', quality=85, optimize=True)
        elif file_ext.lower() in ['.png']:
            # Сохраняем как PNG
            i.save(picture_path, 'PNG', optimize=True)
        else:
            # По умолчанию сохраняем как JPEG
            i.save(picture_path, 'JPEG', quality=85, optimize=True)

        # Устанавливаем права 644 для файла (rw-r--r--)
        os.chmod(picture_path, 0o644)
        current_app.logger.info(f"Файл сохранен: {picture_path} (формат: {i.mode})")

        # Проверяем, что файл действительно создан
        if os.path.exists(picture_path):
            file_size = os.path.getsize(picture_path)
            current_app.logger.info(f"Файл создан успешно, размер: {file_size} байт")
        else:
            current_app.logger.error(f"Файл не найден после сохранения: {picture_path}")
            raise Exception("Файл не был создан")

    except Exception as e:
        current_app.logger.error(f"Ошибка сохранения файла {picture_path}: {e}")
        # Удаляем частично созданный файл
        if os.path.exists(picture_path):
            try:
                os.remove(picture_path)
            except:
                pass
        raise e

    return picture_fn


def save_picture_post(form_picture):
    if form_picture:  # Проверка на существование form_picture
        random_hex = secrets.token_hex(16)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        full_path = os.path.join(current_app.root_path, 'static', 'profile_pics/', current_user.username,
                                 'post_images')
        if not os.path.exists(full_path):
            os.makedirs(full_path)  # Создать все несуществующие каталоги
        picture_path = os.path.join(full_path, picture_fn)
        output_size = (800, 800)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)
        return picture_fn
    else:
        return None  # Возвращаем None, если form_picture не существует


def quality_control_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_access_quality_control:
            flash('У вас нет доступа к этому разделу', 'warning')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function


def validate_user_image_path(user):
    """
    Проверяет существование файла изображения пользователя и возвращает корректный путь
    """
    if not user.image_file or user.image_file == 'default.jpg':
        return 'default.jpg'

    # Проверяем существование файла
    image_path = os.path.join(
        current_app.root_path,
        'static',
        'profile_pics',
        user.username,
        'account_img',
        user.image_file
    )

    if os.path.exists(image_path):
        return user.image_file
    else:
        # Если файл не существует, возвращаем default.jpg
        return 'default.jpg'


def get_user_image_url(user):
    """
    Возвращает URL изображения пользователя с проверкой существования файла
    """
    from flask import url_for

    valid_image_file = validate_user_image_path(user)

    if valid_image_file == 'default.jpg':
        return url_for('static', filename='profile_pics/default.jpg')
    else:
        return url_for('static', filename=f'profile_pics/{user.username}/account_img/{valid_image_file}')
