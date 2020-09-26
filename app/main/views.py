from flask import render_template, url_for, redirect
from flask_login import current_user

from . import main
from app.main.forms import PostForm
from .. import db
from ..models import Permissions, Post


@main.route('/index', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permissions.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        db.session.commit()
        return redirect(url_for('.index'))
    posts = Post.query.order_by(Post.time.desc()).all()

    return render_template('main/index.html', form=form, posts=posts)

