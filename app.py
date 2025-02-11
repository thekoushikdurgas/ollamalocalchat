import logging
import os
from typing import AsyncGenerator, Optional
from flask import Flask, render_template, request, jsonify, session, Response
import json
from ollama import AsyncClient
import hypercorn
from hypercorn.config import Config
import httpx
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class BaseResponse(BaseModel):
    error: Optional[str] = None

class FriendInfo(BaseModel):
    name: str
    age: int
    is_available: bool

class FriendList(BaseModel):
    friends: list[FriendInfo]

class WeatherInfo(BaseModel):
    city: str
    temperature: float
    conditions: str

class RecipeInfo(BaseModel):
    name: str
    ingredients: list[str]
    instructions: list[str]

class ImageAnalysis(BaseModel):
    analysis: str

# Flask App Setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chatbot_secret_key")
ollama_client = AsyncClient()

# Error Handlers
async def handle_ollama_error(error: Exception) -> tuple[dict, int]:
    if isinstance(error, ConnectionError):
        logger.error("Ollama connection error: Failed to connect to service")
        return {"error": "Failed to connect to Ollama. Please ensure Ollama is running."}, 503
    elif "Event loop is closed" in str(error):
        logger.error("Event loop error: Creating new event loop")
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        return {"error": "Please retry your request"}, 503
    logger.error(f"Ollama error: {str(error)}")
    return {"error": str(error)}, 500

# Chat Mode Handlers
async def handle_chat_mode(mode: str, model: str, message: str, stream: bool) -> dict | Response:
    if mode == 'generate':
        return await handle_generate_mode(model, message)
    elif mode == 'tools':
        return await handle_tools_mode(model, message)
    elif mode == 'structured':
        return await handle_structured_mode(model, message)
    else:
        return await handle_regular_chat(model, message, stream)

async def handle_generate_mode(model: str, message: str) -> dict:
    response = await ollama_client.generate(model, prompt=message, stream=False)
    return {'response': response['response']}

async def handle_tools_mode(model: str, message: str) -> dict:
    from tools import TOOL_DEFINITIONS, AVAILABLE_FUNCTIONS
    response = await ollama_client.chat(
        model=model,
        messages=session['messages'],
        tools=TOOL_DEFINITIONS,
        options={'temperature': 0}
    )

    if response.message.tool_calls:
        outputs = await process_tool_calls(response.message.tool_calls)
        final_response = await ollama_client.chat(model=model, messages=session['messages'])
        return {'response': final_response.message.content}
    return {'response': response.message.content}

async def process_tool_calls(tool_calls):
    outputs = []
    for tool in tool_calls:
        if function_to_call := AVAILABLE_FUNCTIONS.get(tool.function.name):
            output = function_to_call(**tool.function.arguments)
            outputs.append(output)
            session['messages'].append({
                'role': 'tool',
                'content': str(output),
                'name': tool.function.name
            })
    return outputs

async def handle_structured_mode(model: str, message: str) -> dict:
    schema_model = detect_schema(message)
    if schema_model:
        schema = schema_model.model_json_schema()
        response = await ollama_client.chat(
            model=model,
            messages=session['messages'],
            format=schema,
            options={'temperature': 0}
        )
        structured_response = schema_model.model_validate_json(response['message']['content'])
        return {'response': structured_response.model_dump_json()}
    return await handle_regular_chat(model, message, False)

async def handle_regular_chat(model: str, message: str, stream: bool) -> dict | Response:
    if stream:
        return Response(generate_stream(message, model), mimetype='text/event-stream')

    response = await ollama_client.chat(model=model, messages=session['messages'])
    return {'response': response['message']['content']}

def detect_schema(message: str) -> Optional[BaseModel]:
    schema_map = {
        'friends': FriendList,
        'weather': WeatherInfo,
        'recipe': RecipeInfo,
        'image': ImageAnalysis
    }
    return next((model for key, model in schema_map.items() 
                 if key in message.lower()), None)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.json
        message = data.get('message')
        model = data.get('model', 'llama2')
        mode = data.get('mode', 'chat')
        stream = data.get('stream', True)

        if not message:
            return jsonify({"error": "Message is required"}), 400

        if 'messages' not in session:
            session['messages'] = []

        session['messages'].append({
            'role': 'user',
            'content': message
        })

        response = await handle_chat_mode(mode, model, message, stream)

        if isinstance(response, Response):
            return response

        session['messages'].append({
            'role': 'assistant',
            'content': response['response']
        })

        return jsonify({
            'response': response['response'],
            'history': session['messages']
        })
    except Exception as e:
        return await handle_ollama_error(e)

@app.route('/generate-code', methods=['POST'])
async def generate_code():
    try:
        data = request.json
        prompt = data.get('prompt')
        suffix = data.get('suffix', '')
        model = data.get('model', 'codellama:7b-code')

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        response = await ollama_client.generate(
            model=model,
            prompt=prompt,
            suffix=suffix,
            options={
                'num_predict': 128,
                'temperature': 0,
                'top_p': 0.9,
                'stop': ['< EOT >'],
            }
        )
        return jsonify({"response": response['response']})
    except Exception as e:
        return await handle_ollama_error(e)

@app.route('/generate', methods=['POST'])
async def generate_response():
    try:
        data = request.json
        prompt = data.get('prompt')
        model = data.get('model', 'llama2')
        stream = data.get('stream', True)
        options = data.get('options', {
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
        })

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        if stream:
            return Response(
                generate_stream(prompt, model, options),
                mimetype='text/event-stream'
            )

        response = await ollama_client.generate(
            model=model,
            prompt=prompt,
            options=options
        )
        return jsonify({"response": response['response']})
    except Exception as e:
        return await handle_ollama_error(e)

async def generate_stream(prompt: str, model: str, options: dict) -> AsyncGenerator[str, None]:
    async for part in ollama_client.generate(
        model=model,
        prompt=prompt,
        stream=True,
        options=options
    ):
        yield f"data: {json.dumps({'response': part['response']})}\n\n"

@app.route('/analyze-comic', methods=['POST'])
async def analyze_comic():
    try:
        data = request.json
        comic_num = data.get('comic_num')

        async with httpx.AsyncClient() as client:
            latest = await client.get('https://xkcd.com/info.0.json')
            latest.raise_for_status()

            if not comic_num:
                import random
                comic_num = random.randint(1, latest.json().get('num'))

            comic = await client.get(f'https://xkcd.com/{comic_num}/info.0.json')
            comic.raise_for_status()
            comic_data = comic.json()

            raw = await client.get(comic_data.get('img'))
            raw.raise_for_status()

            response = await ollama_client.generate(
                model='llava',
                prompt='explain this comic:',
                images=[raw.content],
                stream=False
            )

            return jsonify({
                'comic_num': comic_data.get('num'),
                'title': comic_data.get('title'),
                'alt': comic_data.get('alt'),
                'link': f'https://xkcd.com/{comic_num}',
                'image_url': comic_data.get('img'),
                'explanation': response['response']
            })

    except Exception as e:
        logger.error(f"Comic analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/multimodal-chat', methods=['POST'])
async def multimodal_chat():
    try:
        data = request.json
        message = data.get('message', '')
        image_data = data.get('image', '')  # Base64 encoded image
        model = data.get('model', 'llama2-vision')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        messages = [{
            'role': 'user',
            'content': message,
            'images': [image_data] if image_data else []
        }]

        try:
            response = await ollama_client.chat(
                model=model,
                messages=messages,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                }
            )

            # Add image thumbnail to response if image was analyzed
            response_data = {
                'response': response['message']['content'],
                'has_image': bool(image_data)
            }

            return jsonify(response_data)
        except Exception as e:
            logger.error(f"Multimodal chat error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/pull-progress', methods=['GET'])
async def get_pull_progress():
    if 'pull_progress' not in session:
        session['pull_progress'] = {}
    return jsonify(session['pull_progress'])

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
        session['pull_progress'] = {'status': 'Initializing model creation...'}

        # Validate base model exists
        try:
            models = await client.list()
            if not any(model.model == base_model for model in models.models):
                # Pull the base model if it doesn't exist
                session['pull_progress']['status'] = f'Pulling base model {base_model}...'
                async for progress in client.pull(base_model, stream=True):
                    if 'status' in progress:
                        session['pull_progress']['status'] = progress['status']
                    elif 'completed' in progress and 'total' in progress:
                        session['pull_progress']['progress'] = f"{(progress['completed']/progress['total'])*100:.1f}%"
        except Exception as e:
            logger.error(f"Error checking model existence: {str(e)}")
            return jsonify({'error': f"Error checking model: {str(e)}"}), 500

        try:
            async for progress in client.pull(base_model, stream=True):
                digest = progress.get('digest', '')
                status = progress.get('status', '')

                if status:
                    session['pull_progress']['status'] = status
                    continue

                if digest:
                    if 'total' in progress:
                        if digest not in session['pull_progress']:
                            session['pull_progress'][digest] = {
                                'total': progress['total'],
                                'completed': 0,
                                'digest_short': digest[7:19]
                            }
                    if 'completed' in progress:
                        session['pull_progress'][digest]['completed'] = progress['completed']

                current_digest = digest

        except Exception as e:
            logger.error(f"Error pulling model: {str(e)}")
            return jsonify({'error': f"Error pulling model: {str(e)}"}), 500

        # Then create the custom model
        # Create the model with streaming based on user preference
        stream = data.get('stream', True)
        if stream:
            async for progress in client.create(
                model=model_name,
                from_=base_model,
                system=system_prompt,
                stream=True
            ):
                session['pull_progress']['status'] = f"Creating model: {progress.status}"
        else:
            response = await client.create(
                model=model_name,
                from_=base_model,
                system=system_prompt,
                stream=False
            )
            session['pull_progress']['status'] = f"Model created: {response.status}"

        return jsonify({'status': response['status']})
    except Exception as e:
        logger.error(f"Model creation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/create-chat', methods=['POST'])
async def create_chat():
    try:
        data = request.json
        name = data.get('name')
        base_model = data.get('base_model', 'llama2')
        system_prompt = data.get('system_prompt', '')

        if not name:
            return jsonify({'error': 'Chat name is required'}), 400

        try:
            response = await ollama_client.create(
                model=f'chat-{name.lower().replace(" ", "-")}',
                from_=base_model,
                system=system_prompt,
                stream=False
            )

            # Clear session messages for new chat
            session['messages'] = []
            session['current_chat'] = name

            return jsonify({'status': 'success', 'name': name})
        except Exception as e:
            logger.error(f"Chat creation error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/clear', methods=['POST'])
async def clear_history():
    session['messages'] = []
    return jsonify({'status': 'success'})

@app.route('/messages', methods=['GET'])
async def get_messages():
    # For now, return an empty list since we're not storing messages
    return jsonify([])

@app.route('/embed', methods=['POST'])
async def generate_embedding():
    try:
        data = request.json
        text = data.get('text', '')
        model = data.get('model', 'llama2')
        batch = data.get('batch', False)
        texts = data.get('texts', [])

        if batch:
            if not texts:
                return jsonify({'error': 'Texts array is required for batch embedding'}), 400
            responses = []
            for t in texts:
                response = await ollama_client.embeddings(
                    model=model,
                    prompt=t
                )
                responses.append(response['embeddings'])
            return jsonify({'embeddings': responses})
        else:
            if not text:
                return jsonify({'error': 'Text is required'}), 400
            response = await ollama_client.embeddings(
                model=model,
                prompt=text
            )
            return jsonify({
                'embeddings': response['embeddings'],
                'metadata': {
                    'model': model,
                    'dimensions': len(response['embeddings'])
                }
            })
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process-status', methods=['GET'])
async def get_process_status():
    try:
        response = await ollama_client.ps()
        models_status = []
        for model in response.models:
            model_info = {
                'model': model.model,
                'digest': model.digest,
                'size': f"{(model.size / 1024 / 1024):.2f} MB",
                'size_vram': f"{(model.size_vram / 1024 / 1024):.2f} MB",
                'details': model.details
            }
            if model.expires_at:
                model_info['expires_at'] = model.expires_at
            models_status.append(model_info)
        return jsonify(models_status)
    except Exception as e:
        logger.error(f"Error getting process status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/models', methods=['GET'])
async def list_models():
    try:
        response = await ollama_client.list()
        models_info = []
        for model in response.models:
            model_info = {
                'name': model.model,
                'size': f"{(model.size / 1024 / 1024):.2f} MB",
            }
            if model.details:
                model_info.update({
                    'format': model.details.format,
                    'family': model.details.family,
                    'parameter_size': model.details.parameter_size,
                    'quantization_level': model.details.quantization_level
                })
            models_info.append(model_info)
        return jsonify(models_info)
    except Exception as e:
        return await handle_ollama_error(e)

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