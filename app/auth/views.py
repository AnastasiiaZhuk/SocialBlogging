from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user

from app.decorators import admin_required
from app import auth
from app.auth.forms import (
    LoginForm, RegisterForm, ChangePasswordForm,
    ResetPasswordForm, ChangeEmailForm, EditProfileForm,
    EditProfileAdminForm,
)
from app.models import User, Role, Post
from .. import db
from ..email import send_email


@auth.auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect('main.index')
    return render_template('auth/unconfirmed.html')


@auth.auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))


@auth.auth.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid credentials')
    return render_template('auth/login.html', form=form)


@auth.auth.route('/logout', methods=["GET", "POST"])
def logout():
    logout_user()
    flash('You have benn logged out!')
    return redirect(url_for('main.index'))


@auth.auth.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)

        flash('Now you registered!')
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account!')
    else:
        flash('The confirmation link is invalid or expired')
    return redirect(url_for('main.index'))


@auth.auth.route('/password/change', methods=["POST", "GET"])
@login_required
def change_password():
    form = ChangePasswordForm
    if form.validate_on_submit():
        if current_user.verify_password(form.password_old):
            current_user.password = form.password_new
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated!')
            return redirect(url_for('main.index'))
        else:
            flash('Enter valid old password')
    return render_template('auth/password_change.html', form=form)


@auth.auth.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_confirmation_token()
            send_email(user.email, 'Reset your password',
                       'auth/email/reset_password',
                       user=user, token=token)


@auth.auth.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()

    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.time.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@auth.auth.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@auth.auth.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_admin_profile(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('User has updated!')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)