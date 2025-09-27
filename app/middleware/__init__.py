from quart import Quart, request, jsonify, g, current_app
from quart_cors import cors
from functools import wraps
from quart_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

def setup_middleware(app: Quart):
    # Enable CORS for multiple origins (development and production)
    app = cors(app, allow_origin=[
        "http://localhost:8080",  # Development frontend
        "https://protective-optimism-production-d4a3.up.railway.app",  # Railway backend (for deployed frontend)
        "https://astridgloballtd.pro",  # Cloudflare Pages production frontend
        "http://localhost:3000",  # Alternative development port
        "http://127.0.0.1:8080",  # Alternative localhost
        "http://127.0.0.1:3000"   # Alternative localhost
    ])

def jwt_required_custom(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        try:
            await verify_jwt_in_request()
            user_id = get_jwt_identity()

            # Check if user account is blocked
            async with current_app.db_pool.acquire() as conn:
                user = await conn.fetchrow('SELECT is_blocked FROM users WHERE id = $1', int(user_id))
                if user and user['is_blocked']:
                    return jsonify({'message': 'Your account has been blocked. Please contact support.'}), 403

            # Store user_id in g for access in route handlers
            g.user_id = int(user_id)
            return await f(*args, **kwargs)
        except Exception as e:
            print(f"JWT verification failed: {e}")
            import traceback
            print(f"JWT error traceback: {traceback.format_exc()}")
            return jsonify({'message': 'Invalid or missing JWT token'}), 401
    return decorated_function

def admin_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        try:
            await verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # Check if user is admin
            async with current_app.db_pool.acquire() as conn:
                user = await conn.fetchrow('SELECT role FROM users WHERE id = $1', int(user_id))
                if not user or user['role'] != 'admin':
                    return jsonify({'message': 'Admin access required'}), 403

            # Store user_id in g for access in route handlers
            g.user_id = int(user_id)
            return await f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Invalid or missing JWT token'}), 401
    return decorated_function
