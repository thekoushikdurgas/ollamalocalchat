import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from app import app

async def main():
    config = Config()
    try:
        # Try port 5000 first
        port = 5000
        config.bind = [f"0.0.0.0:{port}"]
        config.use_reloader = True
        await serve(app, config)
    except OSError:
        # If port 5000 fails, try port 8080
        port = 8080
        config.bind = [f"0.0.0.0:{port}"]
        print(f"Port 5000 not available, using port {port} instead")
        await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())