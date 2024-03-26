from flask import Flask, render_template, redirect, url_for, flash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from werkzeug.security import generate_password_hash, check_password_hash
from form import RegisterForm, LoginForm, CreateChatForm, ChatForm
from sqlalchemy.exc import SQLAlchemyError
from flask_socketio import SocketIO, send, emit
import google.generativeai as genai
from openai import OpenAI
import datetime

gemini_api = "AIzaSyD5O_kYEmvbmgtz6b_WJX8_RTw96PqYECk"
gpt_key='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'
# Configure your OpenAI key
client = OpenAI(api_key=gpt_key)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'emiliano2001'
socketio = SocketIO(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boxbox.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(model_class=Base)
db.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="user")
    
class ChatSession(db.Model, Base):
    __tablename__ = "chat_sessions"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    user: Mapped[User] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat_session")

class Message(db.Model, Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    content: Mapped[str] = mapped_column(db.String(1000))
    chat_session_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("chat_sessions.id"))
    sender: Mapped[str] = mapped_column(String(50))
    chat_session: Mapped[ChatSession] = relationship("ChatSession", back_populates="messages")


with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html', current_user=current_user)


# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for('my_chats'))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect                                
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('my_chats'))

    return render_template("login.html", form=form, current_user=current_user)

@app.route('/logout')
def logout():
    logout_user()
    return render_template('index.html')



#3#################################################################################

@app.route('/create_chat', methods=['GET'])
@login_required
def create_chat():
    # Count the number of chats the user has
    chat_count = ChatSession.query.filter_by(user_id=current_user.id).count()
    new_chat_number = chat_count + 1
    default_name = f"Chat {new_chat_number}"
    new_chat = ChatSession(name=default_name, user_id=current_user.id)
    db.session.add(new_chat)
    db.session.commit()

    flash('New chat created successfully!')
    return redirect(url_for('my_chats', chat_id=new_chat.id))



@app.route('/mychats', defaults={'chat_id': None})
@app.route('/mychats/<int:chat_id>')
@login_required
def my_chats(chat_id):
    my_chats = ChatSession.query.filter_by(user_id=current_user.id).all()

    if chat_id:
        # Ensure the chat_id is an integer and exists
        chat_id = int(chat_id)
        # Check if the specified chat belongs to the current user and exists
        chat = next((c for c in my_chats if c.id == chat_id), None)
        if chat is None:
            flash("You do not have permission to view this chat or it does not exist.")
            return redirect(url_for('my_chats'))
        messages = chat.messages

        # Move the active chat to the beginning of the list
        # my_chats.insert(0, my_chats.pop(my_chats.index(chat)))
    else:
        chat = None
        messages = None

    return render_template('chat.html', my_chats=my_chats, current_chat_id=chat_id, chat=chat, messages=messages, name=current_user.name)


def gemini_answer(prompt):
    genai.configure(api_key=gemini_api)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    print(response.text)
    return response.text

def ask_gpt(prompt):
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        print(chat_completion.choices[0].message.content.strip())
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {e}")
        return "I'm sorry, I can't complete that task right now."


@socketio.on('send_message')
def handle_send_message_event(data):
    chat_id = data['chat_id']
    message_content = data['message']
    
    # Save the user message to the database
    user_message = Message(content=message_content, chat_session_id=chat_id, sender='user')
    db.session.add(user_message)
    
    # Get AI response
    gemini_response = gemini_answer(message_content)
    gpt3_5_response = ask_gpt(message_content)
    
    # Save the AI response to the database
    gemini_message = Message(content=gemini_response, chat_session_id=chat_id, sender='gemini')
    gpt3_5_message = Message(content=gpt3_5_response, chat_session_id=chat_id, sender ='gpt3_5')
    db.session.add(gemini_message)
    db.session.add(gpt3_5_message)
    
    db.session.commit()

    # Emit only the AI response back to the client
    emit('gemini_message', {'message': gemini_response, 'sender': 'gemini'})
    emit('gpt3_5_message', {'message': gpt3_5_response, 'sender': 'gpt3_5'})

if __name__ == "__main__":
    socketio.run(app, debug=True)