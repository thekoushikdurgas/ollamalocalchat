import logging
from flask import Flask, render_template, request, jsonify
import ollama

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "chatbot_secret_key"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Call Ollama API
        response = ollama.chat(model='llama2', messages=[
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

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html'), 500
