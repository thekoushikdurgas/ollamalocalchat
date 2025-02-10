
# Ollama Chatbot UI

A Flask-based web application that provides a chat interface for interacting with Ollama's local language models.

## Features

- Real-time chat interface with streaming responses
- Multiple chat modes:
  - Standard chat with history
  - Structured output generation
  - Stream mode for real-time responses
- Message history management
- Tool integration for mathematical operations
- Responsive UI design

## Prerequisites

- Python 3.11 or higher
- Ollama installed and running locally
- Required Python packages (installed automatically via requirements.txt)

## Setup

1. Clone this project in Replit
2. Click the "Run" button to start the server
3. The application will be available at the provided URL

## Project Structure

```
├── app.py           # Main Flask application
├── main.py          # Server startup configuration
├── models.py        # Database and Pydantic models
├── static/          # Static assets
│   ├── css/        # Stylesheets
│   └── js/         # JavaScript files
└── templates/       # HTML templates
```

## Available Chat Modes

1. **Standard Chat**: Regular conversation with the model
2. **Generate**: For text generation tasks
3. **Structured**: Outputs formatted data (weather, friends list, etc.)

## API Endpoints

- `GET /`: Main chat interface
- `POST /chat`: Send messages to the chatbot
- `POST /clear`: Clear chat history
- `GET /messages`: Retrieve message history
- `GET /history`: Get chat history
- `PUT /history/<id>`: Edit history entry
- `DELETE /history/<id>`: Delete history entry

## Features

- Persistent chat history
- Message streaming
- Tool integration
- Structured data output
- Responsive design
- Dark/light mode support

## Development

The project uses:
- Flask for the web framework
- Hypercorn for ASGI server
- SQLAlchemy for database operations
- Ollama for LLM integration

Made with ❤️ on Replit
