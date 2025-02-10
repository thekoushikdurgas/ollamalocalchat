import logging
import os
from flask import Flask, render_template, request, jsonify, session, Response
import json
from ollama import AsyncClient
import hypercorn
from hypercorn.config import Config
from pydantic import BaseModel

# Define the schema for the response
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

# Placeholder for ImageAnalysis model.  Replace with your actual model.
class ImageAnalysis(BaseModel):
    analysis: str


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

@app.route('/generate-code', methods=['POST'])
async def generate_code():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        suffix = data.get('suffix', '')
        model = data.get('model', 'codellama:7b-code')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        try:
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
            return jsonify({'response': response['response']})
        except Exception as e:
            logger.error(f"Code generation error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/generate', methods=['POST'])
async def generate_response():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        model = data.get('model', 'llama2')
        stream = data.get('stream', True)

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        if stream:
            async def generate_stream():
                async for part in ollama_client.generate(model=model, prompt=prompt, stream=True):
                    yield f"data: {json.dumps({'response': part['response']})}\n\n"
            return Response(generate_stream(), mimetype='text/event-stream')
        else:
            response = await ollama_client.generate(model=model, prompt=prompt)
            return jsonify({'response': response['response']})
    except Exception as e:
        logger.error(f"Generate error: {str(e)}")
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

        messages = [{'role': 'user', 'content': message}]
        if image_data:
            messages[0]['images'] = [image_data]

        try:
            response = await ollama_client.chat(
                model=model,
                messages=messages
            )
            return jsonify({'response': response['message']['content']})
        except Exception as e:
            logger.error(f"Multimodal chat error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.json
        message = data.get('message', '')
        mode = data.get('mode', 'chat')
        model = data.get('model', 'llama2')  # Default to llama2
        stream = data.get('stream', True)  # Enable streaming by default

        if not message:
            return jsonify({'error': 'Message is required'}), 400

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
            elif mode == 'tools':
                try:
                    from tools import TOOL_DEFINITIONS, AVAILABLE_FUNCTIONS
                    response = await ollama_client.chat(
                        model=model,
                        messages=session['messages'],
                        tools=TOOL_DEFINITIONS,
                        options={'temperature': 0}
                    )
                    
                    if response.message.tool_calls:
                        outputs = []
                        for tool in response.message.tool_calls:
                            if function_to_call := AVAILABLE_FUNCTIONS.get(tool.function.name):
                                output = function_to_call(**tool.function.arguments)
                                outputs.append(output)
                                session['messages'].append({
                                    'role': 'tool',
                                    'content': str(output),
                                    'name': tool.function.name
                                })
                        
                        # Get final response with tool outputs
                        final_response = await ollama_client.chat(
                            model=model,
                            messages=session['messages']
                        )
                        bot_response = final_response.message.content
                    else:
                        bot_response = response.message.content
                except Exception as e:
                    logger.error(f"Tools mode error: {str(e)}")
                    raise

            elif mode == 'structured':
                try:
                    # Map keywords to schema models
                    schema_map = {
                        'friends': FriendList,
                        'weather': WeatherInfo,
                        'recipe': RecipeInfo,
                        'image': ImageAnalysis
                    }

                    # Detect which schema to use based on message content
                    schema_model = None
                    for key, model in schema_map.items():
                        if key in message.lower():
                            schema_model = model
                            break

                    if schema_model:
                        # Get schema and format response
                        schema = schema_model.model_json_schema()
                        response = await ollama_client.chat(
                            model=model,
                            messages=session['messages'],
                            format=schema,
                            options={
                                'temperature': 0,
                                'top_p': 0.9,
                                'num_predict': 128
                            }
                        )
                        # Validate and format response
                        structured_response = schema_model.model_validate_json(response['message']['content'])
                        bot_response = structured_response.model_dump_json()
                    else:
                        # Default to regular chat if no structure detected
                        response = await ollama_client.chat(
                            model=model,
                            messages=session['messages']
                        )
                        bot_response = response['message']['content']
                except Exception as e:
                    logger.error(f"Structured output error: {str(e)}")
                    raise
            else:
                # Regular chat mode with streaming
                if stream:
                    async def generate_stream():
                        async for part in ollama_client.generate(model=model, prompt=message, stream=True):
                            yield f"data: {json.dumps({'response': part['response']})}\n\n"

                    return Response(generate_stream(), mimetype='text/event-stream')
                else:
                    response = await ollama_client.chat(
                        model=model,
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

        if not text:
            return jsonify({'error': 'Text is required'}), 400

        response = await ollama_client.embeddings(
            model=model,
            prompt=text
        )
        return jsonify({'embeddings': response['embeddings']})
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/models', methods=['GET'])
async def list_models():
    try:
        response = await ollama_client.list()
        models = []
        for model in response['models']:
            model_info = {
                'name': model['name'],  # Accessing name correctly
                'size': f"{(model['size'] / 1024 / 1024):.2f} MB"
            }
            if 'details' in model:
                model_info.update({
                    'format': model['details'].get('format'),
                    'family': model['details'].get('family'),
                    'parameter_size': model['details'].get('parameter_size'),
                    'quantization_level': model['details'].get('quantization_level')
                })
            models.append(model_info)
        return jsonify(models)
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
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