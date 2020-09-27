from flask import render_template, current_app, request,  url_for, redirect
from flask_login import current_user

from . import main
from app.main.forms import PostForm
from .. import db
from ..models import Permissions, Post


@main.route('/index', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    per_page = int(current_app.config['SOCIAL_BLOG_PER_PAGE'])
    pagination = Post.query.order_by(Post.time.desc()).paginate(
        page, per_page=per_page, error_out=False
    )
    posts = pagination.items
    form = PostForm()
    if current_user.can(Permissions.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        db.session.commit()
        return redirect(url_for('.index'))

    return render_template('main/index.html', form=form, pagination=pagination, posts=posts)

