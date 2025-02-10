import logging
import os
import asyncio
from flask import Flask, render_template, request, jsonify
from ollama import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models import Base, Message

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "chatbot_secret_key"

# Create async engine
engine = create_async_engine(
    database_url,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=3600
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Initialize Ollama client
ollama_client = AsyncClient()

async def init_models():
    try:
        logger.info("Initializing database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

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

        async with async_session() as session:
            # Save user message to database
            user_message = Message(role='user', content=message)
            session.add(user_message)
            await session.commit()

            # Call Ollama API asynchronously
            response = await ollama_client.chat(model='llama2', messages=[
                {
                    'role': 'user',
                    'content': message
                }
            ])

            # Save bot response to database
            bot_message = Message(role='bot', content=response['message']['content'])
            session.add(bot_message)
            await session.commit()

            return jsonify({
                'response': bot_message.content
            })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Failed to generate response'}), 500

@app.route('/messages', methods=['GET'])
async def get_messages():
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Message).order_by(Message.created_at.asc())
            )
            messages = result.scalars().all()
            return jsonify([message.to_dict() for message in messages])
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        return jsonify({'error': 'Failed to fetch messages'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html'), 500

def create_app():
    return app