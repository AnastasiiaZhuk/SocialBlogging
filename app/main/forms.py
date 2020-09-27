from wtforms import TextAreaField, validators, SubmitField
from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField


class PostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[validators.DataRequired()])
    submit = SubmitField('Post')