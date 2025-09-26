import asyncio
from hypercorn.asyncio import serve
from hypercorn.config import Config
import os

# IMPORTANT: Adjust this import to match your project's structure.
# If the file containing create_app() is named 'main.py', this will be:
# from main import create_app
# If it's inside a package 'my_app/__init__.py', it will be:
# from my_app import create_app
from app import create_app # Assuming your app code is in 'main.py'

async def main():
    """
    Main entry point to create and run the Quart application.
    """
    # Create the application instance using your factory
    app = await create_app()

    # Configure Hypercorn
    config = Config()
    
    # Bind to host and port. "0.0.0.0" makes it accessible on your network.
    # Use environment variables for flexibility, defaulting to 8000.
    port = int(os.environ.get("PORT", 8000))
    config.bind = [f"0.0.0.0:{port}"]

    # Enable auto-reloader for development. The server will restart on code changes.
    config.use_reloader = True
    
    print(f"🚀 Starting server on http://0.0.0.0:{port}")
    
    # Run the server
    await serve(app, config)

if __name__ == "__main__":
    try:
        # Run the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("Server stopped by user.")