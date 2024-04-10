from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()



def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'emiliano2001'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boxbox.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Flask-Login configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, manage_session=False, cors_allowed_origins="*")

    # Register blueprints
    from app.routes.main import main
    app.register_blueprint(main)
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User  # Import here to avoid circular imports
        return User.query.get(int(user_id))
    
    from app.routes.auth import auth
    app.register_blueprint(auth, url_prefix='/auth')

    from app.routes.chat import chat
    app.register_blueprint(chat, url_prefix='/chat')

    # Shell context processor
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Message  # Assuming models are defined here
        return {'db': db, 'User': User, 'Message': Message}
    

    with app.app_context():
        db.create_all()

    return app