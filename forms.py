from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from flask_wtf.file import FileField, FileRequired, FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField(
        'Username', 
        validators=[DataRequired(), Length(min=2, max=20)],
        render_kw={"placeholder": "Enter your username"}
    )
    email = StringField(
        'Email', 
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter your email"}
    )
    password = PasswordField(
        'Password', 
        validators=[DataRequired(), Length(min=6, max=35)],
        render_kw={"placeholder": "Create a password"}
    )
    confirm_password = PasswordField(
        'Confirm Password', 
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
        render_kw={"placeholder": "Confirm your password"}
    )
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField(
        'Email', 
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter your email"}
    )
    password = PasswordField(
        'Password', 
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter your password"}
    )
    submit = SubmitField('Login')


class ProductForm(FlaskForm):
    name = StringField(
        'Name:',
        validators=[
            DataRequired(message="Product name is required."),
            Length(min=2, max=100, message="Product name must be between 2 and 100 characters.")
        ],
        render_kw={"placeholder": "Enter product name"}
    )
    price = IntegerField(
        'Price:',
        validators=[
            DataRequired(message="Price is required."),
            NumberRange(min=1, message="Price must be greater than 0.")
        ],
        render_kw={"placeholder": "Enter price"}
    )
    category = StringField(
        'Category:',
        validators=[
            DataRequired(message="Category is required.")
        ],
        render_kw={"placeholder": "Enter category"}
    )
    stock = IntegerField(
        'Stock:',
        validators=[
            DataRequired(message="Stock quantity is required."),
            NumberRange(min=0, message="Stock quantity must be non-negative.")
        ],
        render_kw={"placeholder": "Enter stock quantity"}
    )
    image = FileField(
        'Image:',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only! Supported formats: jpg, jpeg, png, gif.'),
            FileRequired('File was not provided!')
        ],
        render_kw={"accept": "image/*"}
    )
    submit = SubmitField('Add Products', render_kw={"class": "btn btn-primary"})