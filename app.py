import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from app.utils.chat_manager import ChatManager
import logging

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
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

# Initialize chat manager
chat_manager = ChatManager()

@app.route('/chat', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True)
