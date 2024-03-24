from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
import datetime

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()], render_kw={"autocomplete": "name"})
    submit = SubmitField("Sign Me Up!")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")
    
class CreateChatForm(FlaskForm):
    name = StringField("Chat Name", validators=[DataRequired()], default=lambda: f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    submit = SubmitField("Create")
    
class ChatForm(FlaskForm):
    message = StringField("Message")
    submit = SubmitField("Send")