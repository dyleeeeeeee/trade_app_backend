from quart import Quart
from quart_cors import cors

def setup_middleware(app: Quart):
    # Enable CORS for multiple origins (development and production)
    app = cors(app, allow_origin=[
        "http://localhost:8080",  # Development frontend
        "https://protective-optimism-production-d4a3.up.railway.app",  # Railway backend (for deployed frontend)
        "https://astridgloballtd.pro",  # Cloudflare Pages production frontend
        "http://localhost:3000",  # Alternative development port
        "http://127.0.0.1:8080",  # Alternative localhost
        "http://127.0.0.1:3000"   # Alternative localhost
    ], allow_credentials=True)
