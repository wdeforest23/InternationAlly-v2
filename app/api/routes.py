from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
from app.models.user import db, Chat, Message
from app.utils.agent_manager import process_user_query
import json
from datetime import datetime

# Create blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Process a chat message and return the response"""
    data = request.json
    
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    user_message = data['message']
    chat_id = data.get('chat_id')
    
    # Create a new chat if chat_id is not provided
    if not chat_id:
        new_chat = Chat(user_id=current_user.id, title=user_message[:50])
        db.session.add(new_chat)
        db.session.commit()
        chat_id = new_chat.id
    
    # Save user message
    user_msg = Message(
        chat_id=chat_id,
        content=user_message,
        role='user'
    )
    db.session.add(user_msg)
    db.session.commit()
    
    # Process the message with our agent system
    try:
        response, map_data = process_user_query(user_message)
        
        # Save assistant response
        assistant_msg = Message(
            chat_id=chat_id,
            content=response,
            role='assistant'
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'chat_id': chat_id,
            'map_data': map_data
        })
    
    except Exception as e:
        current_app.logger.error(f"Error processing message: {str(e)}")
        return jsonify({'error': 'An error occurred processing your message'}), 500

@api_bp.route('/chats', methods=['GET'])
@login_required
def get_chats():
    """Get all chats for the current user"""
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.updated_at.desc()).all()
    
    result = []
    for chat in chats:
        # Get the first message as a preview
        first_message = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.asc()).first()
        preview = first_message.content if first_message else ""
        
        result.append({
            'id': chat.id,
            'title': chat.title or preview[:50],
            'created_at': chat.created_at.isoformat(),
            'updated_at': chat.updated_at.isoformat(),
            'preview': preview[:100] + '...' if len(preview) > 100 else preview
        })
    
    return jsonify(result)

@api_bp.route('/chats/<int:chat_id>', methods=['GET'])
@login_required
def get_chat(chat_id):
    """Get a specific chat with all messages"""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.asc()).all()
    
    result = {
        'id': chat.id,
        'title': chat.title,
        'created_at': chat.created_at.isoformat(),
        'updated_at': chat.updated_at.isoformat(),
        'messages': [
            {
                'id': msg.id,
                'content': msg.content,
                'role': msg.role,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages
        ]
    }
    
    return jsonify(result)

@api_bp.route('/chats/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    """Delete a specific chat"""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    db.session.delete(chat)
    db.session.commit()
    
    return jsonify({'success': True})

@api_bp.route('/chats/<int:chat_id>', methods=['PUT'])
@login_required
def update_chat(chat_id):
    """Update chat title"""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    data = request.json
    if 'title' in data:
        chat.title = data['title']
        db.session.commit()
    
    return jsonify({'success': True})
