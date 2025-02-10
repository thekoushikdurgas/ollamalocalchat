import logging
import os
from flask import Flask, render_template, request, jsonify
from ollama import AsyncClient
import hypercorn
from hypercorn.config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "chatbot_secret_key"

# Initialize Ollama client
ollama_client = AsyncClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.json
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Call Ollama API asynchronously
        response = await ollama_client.chat(model='llama2', messages=[
            {
                'role': 'user',
                'content': message
            }
        ])

        return jsonify({
            'response': response['message']['content']
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Failed to generate response'}), 500

@app.route('/messages', methods=['GET'])
async def get_messages():
    # For now, return an empty list since we're not storing messages
    return jsonify([])

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html'), 500

if __name__ == '__main__':
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    hypercorn.run(app, config)