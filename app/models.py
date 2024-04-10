from flask_login import UserMixin
from . import db  # Import the db instance from your application factory or extensions module
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, String, ForeignKey

# Define the User model class representing the users table in the database
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    chat_sessions = relationship('ChatSession', back_populates='user')

# Define the ChatSession model class representing the chat_sessions table
class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    user = relationship('User', back_populates='chat_sessions')
    messages = relationship('Message', back_populates='chat_session', cascade='all, delete-orphan')

# Define the Message model class representing the messages table
class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000), nullable=False)
    chat_session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False)
    sender = db.Column(db.String(50), nullable=False)
    chat_session = relationship('ChatSession', back_populates='messages')
