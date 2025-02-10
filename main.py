
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from app import app

async def main():
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    config.use_reloader = True
    
    try:
        await serve(app, config)
    except OSError as e:
        if "Address already in use" in str(e):
            config.bind = ["0.0.0.0:8080"]
            print("Port 5000 not available, using port 8080 instead")
            await serve(app, config)
        else:
            raise

if __name__ == "__main__":
    asyncio.run(main())
