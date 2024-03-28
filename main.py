from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from werkzeug.security import generate_password_hash, check_password_hash
from form import RegisterForm, LoginForm, CreateChatForm
from sqlalchemy.exc import SQLAlchemyError
from flask_socketio import SocketIO, send, emit
import google.generativeai as genai
from openai import OpenAI
import datetime
import re

gemini_api = "AIzaSyCzQC_uvxEEDbFRhYDcdpURTQtcpFU2NGY"
gpt_key='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'
# Configure your OpenAI key
client = OpenAI(api_key=gpt_key)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'emiliano2001'
socketio = SocketIO(app,  manage_session=False)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


# Define a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass
# Configure the database URI and track modifications
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boxbox.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Define a user loader function for Flask-Login to load users by ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define the User model class representing the users table in the database
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="user")

# Define the ChatSession model class representing the chat_sessions table
class ChatSession(db.Model, Base):
    __tablename__ = "chat_sessions"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    user: Mapped[User] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat_session", cascade='all, delete-orphan')

# Define the Message model class representing the messages table
class Message(db.Model, Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    content: Mapped[str] = mapped_column(db.String(1000))
    chat_session_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("chat_sessions.id", ondelete='CASCADE'))
    sender: Mapped[str] = mapped_column(String(50))
    chat_session: Mapped[ChatSession] = relationship("ChatSession", back_populates="messages")

# Create all database tables within the application context
with app.app_context():
    db.create_all()


# HomePage of the website
@app.route('/')
def home():
    return render_template('index.html')


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

# User login
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


# Edit user name################################################# 
@app.route('/change-name', methods=['POST'])
@login_required
def change_name():
    new_name = request.form.get('new_name')
    if new_name:
        # Assuming you're using Flask-Login to get the current user
        user_id = current_user.get_id()
        user = User.query.get(user_id)
        if user:
            user.name = new_name
            db.session.commit()
            flash('Your name has been changed successfully.', 'success')
        else:
            flash('User not found.', 'error')
    else:
        flash('Please enter a new name.', 'error')

    return redirect(url_for('my_chats')) 


# Loggout the user
@app.route('/logout')
def logout():
    logout_user()
    return render_template('index.html')



#3###########################################################################################################################
# Creates new chats for the usr
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


# After login Page and chat Page
@app.route('/mychats', defaults={'chat_id': None})
@app.route('/mychats/<int:chat_id>')
@login_required
def my_chats(chat_id):
    my_chats = ChatSession.query.filter_by(user_id=current_user.id).all()

    chat = None
    messages = None

    if chat_id:
        chat = ChatSession.query.filter_by(id=chat_id, user_id=current_user.id).first()
        if chat:
            messages = chat.messages
            # Optionally move the active chat to the top
            # my_chats.sort(key=lambda x: x.id == chat_id, reverse=True)
        else:
            flash("You do not have permission to view this chat or it does not exist.", "error")
            return redirect(url_for('my_chats'))

    return render_template('chat.html', my_chats=my_chats, current_chat_id=chat_id, chat=chat, messages=messages, name=current_user.name)

#Chat renaming function
@app.route('/rename_chat/<int:chat_id>', methods=['POST'])
@login_required
def rename_chat(chat_id):
    # Extract the new chat name from the request
    new_name = request.json.get('newName', '')
    if not new_name:
        return jsonify({'success': False, 'message': 'New name is required.'}), 400

    # Fetch the chat by ID and ensure it belongs to the current user
    chat = ChatSession.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if chat is None:
        return jsonify({'success': False, 'message': 'Chat not found or access denied.'}), 404

    # Update the chat name and commit changes
    chat.name = new_name
    db.session.commit()

    return jsonify({'success': True, 'message': 'Chat renamed successfully.'})

@socketio.on('delete_chat')
def handle_delete_chat(data):
    chat_id = data.get('chat_id')
    if chat_id:
        chat_to_delete = ChatSession.query.get(chat_id)
        if chat_to_delete:
            db.session.delete(chat_to_delete)
            db.session.commit()
            print(f"Chat {chat_id} deleted")
            # Notify the client(s) about the deletion
            emit('chat_deleted', {'chat_id': chat_id}, broadcast=True)
        else:
            print(f"Chat {chat_id} not found for deletion")
            # Optionally, notify the client the chat was not found
            emit('chat_delete_failed', {'error': 'Chat not found', 'chat_id': chat_id}, room=request.sid)

# Gemini api call
def gemini_answer(prompt):
    genai.configure(api_key=gemini_api)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    print(response.text)
    return response.text

# GPT 3.5-Turbo api call
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



# Removes unnecessary symbols from the ai response
def remove_bold_tags(text):
    # Remove <b> tags and their contents
    cleaned_text = re.sub(r'<b>(.*?)</b>', '', text)
    return cleaned_text



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

    # Remove <b> tags from AI responses
    gemini_response_cleaned = remove_bold_tags(gemini_response)
    gpt3_5_response_cleaned = remove_bold_tags(gpt3_5_response)

    # Save the AI response to the database
    gemini_message = Message(content=gemini_response_cleaned, chat_session_id=chat_id, sender='gemini')
    gpt3_5_message = Message(content=gpt3_5_response_cleaned, chat_session_id=chat_id, sender='gpt3_5')

    db.session.add(gemini_message)
    db.session.add(gpt3_5_message)
    
    db.session.commit()

    # Emit only the AI response back to the client
    emit('gemini_message', {'message': gemini_response, 'sender': 'gemini'})
    emit('gpt3_5_message', {'message': gpt3_5_response, 'sender': 'gpt3_5'})

if __name__ == "__main__":
    socketio.run(app, debug=True)