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
    if not os.path.exists(full_path):
        os.mkdir(full_path)
    picture_path = os.path.join(full_path, picture_fn)
    output_size = (600, 600)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

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
