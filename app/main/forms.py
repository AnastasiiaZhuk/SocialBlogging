from wtforms import TextAreaField, validators, SubmitField
from flask_wtf import FlaskForm


class PostForm(FlaskForm):
    body = TextAreaField("What's on your mind?", validators=[validators.DataRequired()])
    submit = SubmitField('Post')