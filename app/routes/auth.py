from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.form import LoginForm, RegisterForm

auth = Blueprint('auth', __name__)

# Register new users into the User database
@auth.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('auth.login'))

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
        return redirect(url_for('chat.my_chats'))
    return render_template("register.html", form=form, current_user=current_user)

# User login
@auth.route('/login', methods=["GET", "POST"])
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
            return redirect(url_for('auth.login'))
        # Password incorrect                                
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('auth.login'))
        else:
            login_user(user)
            return redirect(url_for('chat.my_chats'))

    return render_template("login.html", form=form, current_user=current_user)


# Edit user name################################################# 
@auth.route('/change-name', methods=['POST'])
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

    return redirect(url_for('chat.my_chats')) 


# Loggout the user
@auth.route('/logout')
def logout():
    logout_user()
    return render_template('index.html')
