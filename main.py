import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from app import app, init_models

async def main():
    # Initialize database first
    await init_models()

    # Configure Hypercorn
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    config.use_reloader = True

    # Serve the application
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())