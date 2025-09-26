from quart import Quart, request, jsonify, session, g
from quart_cors import cors
from functools import wraps
import asyncpg

def setup_middleware(app: Quart):
    # Enable CORS
    app = cors(app, allow_origin="http://localhost:8080", allow_credentials=True)

    @app.before_request
    async def load_user():
        user_id = session.get('user_id')
        if user_id:
            async with app.db_pool.acquire() as conn:
                user = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
                g.user = user
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
