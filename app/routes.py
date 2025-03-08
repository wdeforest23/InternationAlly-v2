from flask import Blueprint, render_template, jsonify
from .utils.chat_manager import ChatManager

main_bp = Blueprint('main', __name__)
chat_manager = ChatManager()

@main_bp.route('/')
def home():
    return render_template('chat.html')

@main_bp.route('/clear', methods=['POST'])
def clear_history():
    try:
        chat_manager.clear_history()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 