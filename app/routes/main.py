from flask import Flask, render_template, Blueprint
import os
from flask import current_app

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return render_template('index.html')

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/contact')
def contact():
    # You might also handle POST requests here if you have a contact form
    return render_template('contact.html')
