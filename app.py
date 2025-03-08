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
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
logging.basicConfig(
    handlers=[
        RotatingFileHandler(
            'logs/app.log', 
            maxBytes=10000000, 
            backupCount=5
        ),
        logging.StreamHandler()  # This will also print to console
    ],
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app():
    app = Flask(__name__, static_url_path='/flask_static')
    
    # Add this after creating the app instance
    app.logger.setLevel(logging.DEBUG)
    
    # Update CORS configuration
    CORS(app, 
         resources={r"/api/*": {
             "origins": ["http://localhost:5173"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Accept"],
             "supports_credentials": True,
             "expose_headers": ["Content-Type", "Authorization"],
             "max_age": 120  # Cache preflight requests
         }},
         supports_credentials=True)  # Enable credentials globally

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///internationAlly.db')
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

    @app.route('/api/chat', methods=['POST'])
    @jwt_required()
    def chat():
        try:
            data = request.get_json()
            if not data or 'message' not in data:
                return jsonify({'error': 'No message provided'}), 400

            current_user_id = get_jwt_identity()
            message = data['message']
            
            logging.info(f"Processing message for user {current_user_id}")
            
            # Create a new conversation or get existing one
            conversation = Conversation.query.filter_by(
                user_id=current_user_id,
                is_active=True
            ).order_by(Conversation.created_at.desc()).first()
            
            if not conversation:
                conversation = Conversation(user_id=current_user_id)
                db.session.add(conversation)
                db.session.commit()
            
            # Add the user's message
            user_message = Message(
                conversation_id=conversation.id,
                role='user',
                content=message
            )
            db.session.add(user_message)
            db.session.commit()
            
            # Process the message synchronously
            response = chat_manager.process_message(message, current_user_id)
            
            if response.get('success'):
                # Add the assistant's response
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role='assistant',
                    content=response.get('response', 'Sorry, I could not process your message.')
                )
                db.session.add(assistant_message)
                db.session.commit()
                
                return jsonify(response)
            else:
                return jsonify({
                    'success': False,
                    'error': response.get('error', 'Failed to process message')
                }), 500

        except Exception as e:
            logging.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint"""
        return jsonify({'status': 'healthy'})

    # Authentication routes
    @app.route('/api/login', methods=['POST'])
    def login():
        # Add debug logging
        app.logger.debug(f"Received login request: {request.headers}")
        app.logger.debug(f"Request data: {request.get_data()}")
        
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Add more debug logging
        app.logger.debug(f"Processing login for email: {email}")
        
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

    @app.route('/api/debug/conversation/<int:conversation_id>', methods=['GET'])
    @jwt_required()
    def debug_conversation(conversation_id):
        """Debug endpoint to verify conversation storage"""
        try:
            current_user_id = get_jwt_identity()
            conversation = Conversation.query.get(conversation_id)
            
            if not conversation or conversation.user_id != int(current_user_id):
                return jsonify({"error": "Conversation not found"}), 404
            
            messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
            
            return jsonify({
                "conversation_id": conversation_id,
                "created_at": conversation.created_at.isoformat(),
                "is_active": conversation.is_active,
                "messages": [{
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.message_metadata
                } for msg in messages]
            })
            
        except Exception as e:
            logging.error(f"Error in debug endpoint: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/debug/latest', methods=['GET'])
    @jwt_required()
    def debug_latest():
        """Debug endpoint to check latest messages"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get latest conversation
            conversation = Conversation.query.filter_by(
                user_id=current_user_id,
                is_active=True
            ).first()
            
            if not conversation:
                return jsonify({"error": "No active conversation"}), 404
            
            # Get messages
            messages = Message.query.filter_by(
                conversation_id=conversation.id
            ).order_by(Message.timestamp.desc()).limit(5).all()
            
            return jsonify({
                "conversation_id": conversation.id,
                "messages": [{
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "metadata": msg.message_metadata
                } for msg in messages]
            })
            
        except Exception as e:
            logging.error(f"Debug endpoint error: {str(e)}")
            return jsonify({"error": str(e)}), 500

    # Create database tables within app context
    with app.app_context():
        # Import models here to ensure they're registered with SQLAlchemy
        from app.models.conversation import Conversation, Message
        
        # Create all tables
        db.create_all()
        
        # Register blueprints
        from app.routes import main_bp
        app.register_blueprint(main_bp)

    return app

# Instead of creating the app instance at module level,
# let's make it available through a function that flask cli can discover
def get_app():
    return create_app()

# For direct python execution
if __name__ == '__main__':
    app = get_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
