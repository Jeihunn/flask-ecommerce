from extensions import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, EmailField
from wtforms.validators import Email, DataRequired, EqualTo, Length, ValidationError
from models import User, Subscriber
from werkzeug.security import check_password_hash


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()], render_kw={
                       "data-validation-required-message": "Please enter your email"})
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=30)], render_kw={
                             "data-validation-required-message": "Please enter your password"})
    submit = SubmitField("Login")

    def validate(self):
        if not super().validate():
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if not user or not check_password_hash(user.password, self.password.data):
            self.email.errors.append("Invalid email or password.")
            return False
        return True


class RegisterForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(
        min=8, max=30), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError(
                'Email already exists. Please choose a different email.')


class CommentForm(FlaskForm):
    review = TextAreaField('Review', validators=[DataRequired()])
    submit = SubmitField("Submit")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    subject = StringField("Subject", validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField("Submit")


class SubscribeForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Subscribe Now")

    def validate_email(self, email):
        if Subscriber.query.filter_by(email=email.data).first():
            raise ValidationError(
                'This email address is already subscribed.')
