from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session, Blueprint
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column, mapper
from sqlalchemy import Integer, String, Text
from werkzeug.security import generate_password_hash, check_password_hash
from app.form import RegisterForm, LoginForm, CreateChatForm
from sqlalchemy.exc import SQLAlchemyError
from flask_socketio import SocketIO, send, emit
import datetime
from app import db
from app import socketio
from app.models import User, ChatSession, Message
from app.utils.ai_handlers import gemini_answer, ask_gpt
from concurrent.futures import ThreadPoolExecutor
import asyncio

chat = Blueprint('chat', __name__)

# Creates new chats for the usr
@chat.route('/create_chat', methods=['GET'])
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
    return redirect(url_for('chat.my_chats', chat_id=new_chat.id))


# After login Page and chat Page
@chat.route('/mychats', defaults={'chat_id': None})
@chat.route('/mychats/<int:chat_id>')
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
@chat.route('/rename_chat/<int:chat_id>', methods=['POST'])
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



# Removes unnecessary symbols from the ai response
@socketio.on('send_message')
def handle_send_message_event(data):
    chat_id = data['chat_id']
    message_content = data['message']
    
    # Prepare user message
    user_message = {'content': message_content, 'chat_session_id': chat_id, 'sender': 'user'}

    # Use ThreadPoolExecutor to call gemini_answer and ask_gpt concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_gemini = executor.submit(gemini_answer, message_content)
        future_gpt3_5 = executor.submit(ask_gpt, message_content)

        gemini_response = future_gemini.result()
        gpt3_5_response = future_gpt3_5.result()

    # Clean AI responses from <b> tags
    gemini_response_cleaned = gemini_response
    gpt3_5_response_cleaned = gpt3_5_response

    # Prepare AI messages
    gemini_message = {'content': gemini_response_cleaned, 'chat_session_id': chat_id, 'sender': 'gemini'}
    gpt3_5_message = {'content': gpt3_5_response_cleaned, 'chat_session_id': chat_id, 'sender': 'gpt3_5'}

    # Collect all messages to insert
    messages_data = [user_message, gemini_message, gpt3_5_message]

    # Bulk insert messages
    db.session.bulk_insert_mappings(Message, messages_data)
    db.session.commit()

    # Emit the AI responses back to the client
    emit('gemini_message', {'message': gemini_response, 'sender': 'gemini'})
    emit('gpt3_5_message', {'message': gpt3_5_response, 'sender': 'gpt3_5'})