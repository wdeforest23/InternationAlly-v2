from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os

login_manager = LoginManager()

def create_app():
    load_dotenv()

    # Get the absolute path to the app directory
    app_dir = os.path.abspath(os.path.dirname(__file__))
    
    app = Flask(__name__,
                static_folder=os.path.join(app_dir, 'static'),
                template_folder=os.path.join(app_dir, 'pages'))

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
    app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions in filesystem

    login_manager.init_app(app)
    login_manager.login_view = 'login'

    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
