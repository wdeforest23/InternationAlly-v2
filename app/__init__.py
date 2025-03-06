from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from .models.db import init_db, db
import os

# Initialize extensions here so they can be imported by other parts of the app
from flask_login import LoginManager
login_manager = LoginManager()

def create_app():
    # Get the absolute path to the app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__)
    
    # Set template and static folders using absolute paths
    app.template_folder = os.path.join(app_dir, 'templates')
    app.static_folder = os.path.join(app_dir, 'static')
    
    CORS(app)  # Enable CORS for all routes
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Configure database and secrets
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
    
    # Initialize extensions
    init_db(app)
    jwt = JWTManager(app)

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
