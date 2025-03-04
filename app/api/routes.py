from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
from app.models.user import User
import json
from datetime import datetime

# Create blueprint
api_bp = Blueprint('api', __name__)

# In-memory storage for chat messages and chats
chat_history = {}
chats = {}

@api_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Get user ID from current user
    user_id = current_user.id
    
    # Initialize chat history for user if not exists
    if user_id not in chat_history:
        chat_history[user_id] = []
    
    # Add user message to history
    chat_history[user_id].append({
        'role': 'user',
        'content': message,
        'timestamp': datetime.now().isoformat()
    })
    
    # TODO: Implement actual AI response generation
    # For now, return a mock response
    response = "I'm your AI assistant. I can help you with housing, local information, and visa-related questions. What would you like to know?"
    
    # Add assistant response to history
    chat_history[user_id].append({
        'role': 'assistant',
        'content': response,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({'response': response})

@api_bp.route('/chats', methods=['GET'])
@login_required
def get_chats():
    """Get all chats for the current user"""
    user_id = current_user.id
    user_chats = chats.get(user_id, [])
    
    result = []
    for chat in user_chats:
        # Get the first message as a preview
        messages = chat.get('messages', [])
        preview = messages[0]['content'] if messages else ""
        
        result.append({
            'id': chat['id'],
            'title': chat.get('title', preview[:50]),
            'created_at': chat['created_at'],
            'updated_at': chat['updated_at'],
            'preview': preview[:100] + '...' if len(preview) > 100 else preview
        })
    
    return jsonify(result)

@api_bp.route('/chats/<int:chat_id>', methods=['GET'])
@login_required
def get_chat(chat_id):
    """Get a specific chat with all messages"""
    user_id = current_user.id
    user_chats = chats.get(user_id, [])
    
    chat = next((c for c in user_chats if c['id'] == chat_id), None)
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    return jsonify(chat)

@api_bp.route('/chats/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    """Delete a specific chat"""
    user_id = current_user.id
    if user_id in chats:
        chats[user_id] = [c for c in chats[user_id] if c['id'] != chat_id]
    
    return jsonify({'success': True})

@api_bp.route('/chats/<int:chat_id>', methods=['PUT'])
@login_required
def update_chat(chat_id):
    """Update chat title"""
    user_id = current_user.id
    user_chats = chats.get(user_id, [])
    
    chat = next((c for c in user_chats if c['id'] == chat_id), None)
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    data = request.json
    if 'title' in data:
        chat['title'] = data['title']
        chat['updated_at'] = datetime.now().isoformat()
    
    return jsonify({'success': True})
