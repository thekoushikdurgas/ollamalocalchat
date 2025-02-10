import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from app import app

async def main():
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    config.use_reloader = True

    # Serve the application
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())