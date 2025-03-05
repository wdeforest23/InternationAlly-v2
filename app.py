import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from app.utils.chat_manager import ChatManager
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for testing
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create Flask app
app = Flask(__name__)

# Initialize chat manager
chat_manager = ChatManager()

@app.route('/test', methods=['POST'])
async def test_apis():
    try:
        message = request.json.get('message', '')
        logging.info(f"Testing APIs with message: {message}")
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Process message and get response
        response = await chat_manager.process_message(message)
        
        return jsonify({
            'success': True,
            'response': response.get('response'),
            'api_data': {
                'housing_results': len(response['api_data']['housing']) if response['api_data']['housing'] else 0,
                'places_results': len(response['api_data']['places']) if response['api_data']['places'] else 0
            },
            'analysis': response.get('analysis')
        })
        
    except Exception as e:
        logging.error(f"Error in test endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
