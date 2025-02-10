import logging
import os
from flask import Flask, render_template, request, jsonify
import ollama
from models import db, Message
import asyncio
from ollama import AsyncClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "chatbot_secret_key"

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Initialize Ollama async client
ollama_client = AsyncClient()

@app.route('/')
def index():
    return render_template('index.html')

async def get_ollama_response(message):
    """Async function to get response from Ollama"""
    try:
        messages = [{'role': 'user', 'content': message}]
        response = await ollama_client.chat('llama2', messages=messages)
        return response['message']['content']
    except Exception as e:
        logger.error(f"Error getting Ollama response: {str(e)}")
        raise

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.json
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Save user message to database
        user_message = Message(role='user', content=message)
        db.session.add(user_message)
        db.session.commit()

        # Get response from Ollama asynchronously
        bot_response = await get_ollama_response(message)

        # Save bot response to database
        bot_message = Message(role='bot', content=bot_response)
        db.session.add(bot_message)
        db.session.commit()

        return jsonify({
            'response': bot_message.content
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Failed to generate response'}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    messages = Message.query.order_by(Message.created_at.asc()).all()
    return jsonify([message.to_dict() for message in messages])

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html'), 500