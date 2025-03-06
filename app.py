import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from app.utils.chat_manager import ChatManager
import logging
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from app.models.db import db, init_db
from app.models.user import User

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Initialize extensions
init_db(app)  # Initialize database first
jwt = JWTManager(app)

# Initialize chat manager
chat_manager = ChatManager()

@app.route('/chat', methods=['POST'])
@jwt_required()
async def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        message = data['message']
        logging.info(f"Received message: {message}")

        # Process the message
        response = await chat_manager.process_message(message)
        
        # Log the type of response we got
        if response['success']:
            logging.info("Message processed successfully")
            if response['api_data']['rag']:
                logging.info("RAG system was used in response")
            if response['api_data']['housing']:
                logging.info("Housing data was included")
            if response['api_data']['places']:
                logging.info("Places data was included")
        else:
            logging.error(f"Error processing message: {response.get('error')}")

        return jsonify(response)

    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy'})

# Authentication routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'token': access_token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    user = User(
        email=data['email'],
        first_name=data['firstName'],
        last_name=data['lastName']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'token': access_token,
        'user': user.to_dict()
    }), 201

# Protected routes
@app.route('/api/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if request.method == 'GET':
            return jsonify(user.to_dict())
        
        elif request.method == 'PUT':
            data = request.json
            user.first_name = data.get('firstName', user.first_name)
            user.last_name = data.get('lastName', user.last_name)
            user.university = data.get('university', user.university)
            user.student_status = data.get('studentStatus', user.student_status)
            user.visa_type = data.get('visaType', user.visa_type)
            user.housing_preferences = data.get('housingPreferences', user.housing_preferences)
            
            db.session.commit()
            return jsonify(user.to_dict())
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Register blueprints
from app.routes import main_bp
app.register_blueprint(main_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables within app context
    app.run(debug=True)
