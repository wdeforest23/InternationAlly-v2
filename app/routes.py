from flask import Blueprint, render_template, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models.db import db
from .models.user import User
from .utils.chat_manager import ChatManager

main_bp = Blueprint('main', __name__)
chat_manager = ChatManager()

@main_bp.route('/')
def home():
    return render_template('chat.html')

@main_bp.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        response = await chat_manager.process_message(message)
        return jsonify({'success': True, 'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/clear', methods=['POST'])
def clear_history():
    try:
        chat_manager.clear_history()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/signup', methods=['POST'])
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
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        'token': access_token,
        'user': user.to_dict()
    }), 201

@main_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'token': access_token,
            'user': user.to_dict()
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@main_bp.route('/api/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if request.method == 'GET':
        return jsonify(user.to_dict())
    
    data = request.json
    user.first_name = data.get('firstName', user.first_name)
    user.last_name = data.get('lastName', user.last_name)
    user.university = data.get('university', user.university)
    user.student_status = data.get('studentStatus', user.student_status)
    user.visa_type = data.get('visaType', user.visa_type)
    user.housing_preferences = data.get('housingPreferences', user.housing_preferences)
    
    db.session.commit()
    return jsonify(user.to_dict()) 