from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from .config import Config
from app.models import User  # Import User model to access it in the user_loader function
from app.extensions import db, bcrypt, login_manager
from app.auth.routes import AdminUser
# Initialize extensions
migrate = Migrate()

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)

    # Initialize the app with extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.auth import auth as auth_blueprint
    from app.admin import admin as admin_blueprint
    from app.main import main as main_blueprint

    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(main_blueprint)

    login_manager.login_view = 'auth.login'

    # User loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        if user_id == "1":
        # Return the static admin user if the user_id is "1"
            return AdminUser()
        return User.query.get(int(user_id))  # Assuming user_id is an integer

    return app
