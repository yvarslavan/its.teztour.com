from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    abort,
    request,
    g,
)
from flask_login import current_user, login_required
from blog import db
from blog.models import Post
from blog.post.forms import PostForm, PostUpdateForm
from blog.user.utils import save_picture_post
from redmine import get_count_notifications, get_count_notifications_add_notes

posts = Blueprint('post', __name__, template_folder='templates')


def get_total_notification_count(user):
    """Подсчет общего количества уведомлений для пользователя"""
    if user is None:
        return 0
    return get_count_notifications(user.id) + get_count_notifications_add_notes(user.id)


# Контекстный процессор для передачи количества уведомлений в каждый шаблон
@posts.context_processor
def inject_notification_count():
    count = get_total_notification_count(
        g.current_user if hasattr(g, "current_user") else None
    )
    return dict(count_notifications=count)


@posts.before_request
def set_current_user():
    g.current_user = current_user if current_user.is_authenticated else None


@posts.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post_new = Post(title=form.title.data, content=form.content.data, image_post=form.picture.data, author=current_user)
        picture_file = save_picture_post(form.picture.data)
        post_new.image_post = picture_file
        db.session.add(post_new)
        db.session.commit()
        flash('Статья была опубликована!', 'success')
        return redirect(url_for('main.blog'))
    path_img_file = url_for('static', filename=f'profile_pics/{current_user.username}/post_images/{current_user.image_file}')
    return render_template('create_post.html', title='Новая статья', form=form, legend='Новая статья', image_file=path_img_file)


@posts.route('/post/<int:post_id>')
@login_required
def post(post_id):
    post_view = Post.query.get_or_404(post_id)
    if post_view.image_post is None:
        path_img_file = False
    else:
        path_img_file = url_for(
            "static",
            filename=f"profile_pics/{post_view.author.username}/post_images/{post_view.image_post}",
        )

    return render_template(
        "post.html", title=post_view.title, post=post_view, img_file_path=path_img_file
    )


@posts.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post_update = Post.query.get_or_404(post_id)

    if post_update.author != current_user:
        abort(403)
    form = PostUpdateForm()
    if request.method == 'GET':
        form.title.data = post_update.title
        form.content.data = post_update.content

    if form.validate_on_submit():
        post_update.title = form.title.data
        post_update.content = form.content.data
        if form.picture.data:
            post_update.image_post = save_picture_post(form.picture.data)
        db.session.commit()
        flash('Данная статья была обновлёна', 'success')

        return redirect(url_for("post.post", post_id=post_update.id))

    image_file = url_for(
        "static",
        filename=f"profile_pics/{current_user.username}/post_images/{post_update.image_post}",
    )

    return render_template(
        "update_post.html",
        title="Обновить статью",
        form=form,
        legend="Обновить статью",
        image_file=image_file,
        post=post_update,
    )


@posts.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post_delete = Post.query.get_or_404(post_id)
    if post_delete.author != current_user:
        abort(403)
    db.session.delete(post_delete)
    db.session.commit()
    flash('Данный пост был удален', 'success')
    return redirect(url_for('users.account'))
