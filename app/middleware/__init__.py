from quart import Quart, request, jsonify, g
from quart_cors import cors
from functools import wraps
import asyncpg

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

    @app.before_request
    async def load_user():
        user_id = request.cookies.get('user_session')
        if user_id:
            try:
                user_id = int(user_id)  # Convert string to int
                async with app.db_pool.acquire() as conn:
                    user = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
                    g.user = user
            except Exception as e:
                g.user = None
        else:
            g.user = None

def login_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if g.user is None:
            return jsonify({'message': 'Authentication required'}), 401
        return await f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if g.user is None:
            return jsonify({'message': 'Authentication required'}), 401
        if g.user['role'] != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return await f(*args, **kwargs)
    return decorated_function
