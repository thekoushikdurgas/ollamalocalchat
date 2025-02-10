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

async def get_embedding(text: str, model: str = 'llama2') -> list:
    """Get embeddings for text using specified model."""
    try:
        response = await ollama_client.embeddings(
            model=model,
            prompt=text
        )
        return response['embeddings']
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        return []

def cosine_similarity(v1: list, v2: list) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm1 = sum(x * x for x in v1) ** 0.5
    norm2 = sum(x * x for x in v2) ** 0.5
    return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0

@app.route('/embed', methods=['POST'])
async def embed_text():
    try:
        data = request.json
        text = data.get('text', '')
        model = data.get('model', 'llama2')

        if not text:
            return jsonify({'error': 'Text is required'}), 400

        embeddings = await get_embedding(text, model)
        return jsonify({'embeddings': embeddings})
    except Exception as e:
        logger.error(f"Embedding request error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.json
        message = data.get('message', '')
        mode = data.get('mode', 'chat')
        model = data.get('model', 'llama2')  # Default to llama2

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Initialize messages list for the session if it doesn't exist
        if 'messages' not in session:
            session['messages'] = []

        # Initialize messages list for the session if it doesn't exist
        if 'messages' not in session:
            session['messages'] = []

        # Add user message to history
        session['messages'].append({
            'role': 'user',
            'content': message
        })

        try:
            if mode == 'generate':
                try:
                    response = await ollama_client.generate(
                        'llama2',
                        prompt=message,
                        stream=False
                    )
                    bot_response = response['response']
                except Exception as e:
                    logger.error(f"Generate mode error: {str(e)}")
                    raise
            elif mode == 'structured':
                # Handle structured output requests
                try:
                    # Detect the type of structured output needed
                    if 'friends' in message.lower():
                        schema = FriendList.model_json_schema()
                        response = await ollama_client.chat(
                            model='llama2',
                            messages=session['messages'],
                            format=schema,
                            options={'temperature': 0}
                        )
                        # Validate response with Pydantic
                        structured_response = FriendList.model_validate_json(response['message']['content'])
                        bot_response = structured_response.model_dump_json()
                    elif 'weather' in message.lower():
                        schema = WeatherInfo.model_json_schema()
                        response = await ollama_client.chat(
                            model='llama2',
                            messages=session['messages'],
                            format=schema,
                            options={'temperature': 0}
                        )
                        structured_response = WeatherInfo.model_validate_json(response['message']['content'])
                        bot_response = structured_response.model_dump_json()
                    else:
                        # Default to regular chat if no structure detected
                        response = await ollama_client.chat(
                            model='llama2',
                            messages=session['messages']
                        )
                        bot_response = response['message']['content']
                except Exception as e:
                    logger.error(f"Structured output error: {str(e)}")
                    raise
            else:
                # Regular chat mode
                response = await ollama_client.chat(
                    model='llama2',
                    messages=session['messages']
                )
                bot_response = response['message']['content']

            # Add bot response to history
            session['messages'].append({
                'role': 'assistant',
                'content': bot_response
            })

            return jsonify({
                'response': bot_response,
                'history': session['messages']
            })

        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            return jsonify({'error': 'Model response failed'}), 500

    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/create-model', methods=['POST'])
async def create_model():
    try:
        data = request.json
        model_name = data.get('model_name')
        base_model = data.get('base_model', 'llama2')
        system_prompt = data.get('system_prompt', '')

        if not model_name:
            return jsonify({'error': 'Model name is required'}), 400

        client = AsyncClient()
        response = await client.create(
            model=model_name,
            from_=base_model,
            system=system_prompt,
            stream=False
        )
        
        return jsonify({'status': response['status']})
    except Exception as e:
        logger.error(f"Model creation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear', methods=['POST'])
async def clear_history():
    session['messages'] = []
    return jsonify({'status': 'success'})

@app.route('/messages', methods=['GET'])
async def get_messages():
    # For now, return an empty list since we're not storing messages
    return jsonify([])

@app.route('/similar-messages', methods=['POST'])
async def find_similar_messages():
    try:
        data = request.json
        query = data.get('query', '')
        model = data.get('model', 'llama2')
        threshold = data.get('threshold', 0.8)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        query_embedding = await get_embedding(query, model)
        
        # In a real application, you would store and retrieve embeddings from a database
        # For now, we'll just compare with recent messages
        similar_messages = []
        
        if 'messages' in session:
            for msg in session['messages']:
                if msg['role'] == 'user':
                    msg_embedding = await get_embedding(msg['content'], model)
                    similarity = cosine_similarity(query_embedding, msg_embedding)
                    if similarity >= threshold:
                        similar_messages.append({
                            'content': msg['content'],
                            'similarity': similarity
                        })

        return jsonify({'similar_messages': similar_messages})
    except Exception as e:
        logger.error(f"Similar messages error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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