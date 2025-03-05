from flask import Flask
from flask_cors import CORS
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
    
    return app
