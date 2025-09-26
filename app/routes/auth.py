from quart import Blueprint, request, jsonify, current_app
from quart_auth import AuthUser, login_user, logout_user, current_user, login_required
from ..utils.email import email_service

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
async def login():
    data = await request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password required'}), 400

    async with current_app.db_pool.acquire() as conn:
        user = await conn.fetchrow('SELECT * FROM users WHERE email = $1', email)

        if user and user['password'] == password:  # Simple password check (no hashing as requested)
            # Login the user using quart-auth
            login_user(AuthUser(user['id']))

            print(f"DEBUG: Logged in user_id = {user['id']}")  # Debug log

            # Send login notification email (don't await to avoid blocking login)
            import asyncio
            asyncio.create_task(email_service.send_login_notification(user['email']))

            return jsonify({
                'id': user['id'],
                'email': user['email'],
                'role': user['role']
            }), 200

    return jsonify({'message': 'Invalid credentials'}), 401

@auth_bp.route('/signup', methods=['POST'])
async def signup():
    data = await request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password required'}), 400

    async with current_app.db_pool.acquire() as conn:
        # Check if user exists
        existing = await conn.fetchrow('SELECT id FROM users WHERE email = $1', email)
        if existing:
            return jsonify({'message': 'User already exists'}), 400

        # Create user
        user = await conn.fetchrow('''
            INSERT INTO users (email, password, role)
            VALUES ($1, $2, 'user')
            RETURNING id, email, role
        ''', email, password)

        # Login the user using quart-auth
        login_user(AuthUser(user['id']))

        # Send welcome email (don't await to avoid blocking signup)
        import asyncio
        asyncio.create_task(email_service.send_welcome_email(user['email']))

        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'role': user['role']
        }), 201

@auth_bp.route('/logout', methods=['POST'])
async def logout():
    logout_user()
    return jsonify({'message': 'Logged out'}), 200

@auth_bp.route('/user', methods=['GET'])
@login_required
async def get_current_user():
    user_id = int(current_user.auth_id)
    async with current_app.db_pool.acquire() as conn:
        user = await conn.fetchrow('SELECT id, email, role FROM users WHERE id = $1', user_id)
        if user:
            return jsonify({
                'id': user['id'],
                'email': user['email'],
                'role': user['role']
            }), 200
        else:
            return jsonify({'message': 'User not found'}), 404

@auth_bp.route('/forgot-password', methods=['POST'])
async def forgot_password():
    data = await request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email required'}), 400

    # In a real app, you'd send an email here
    # For now, just return success
    return jsonify({'message': 'Password reset email sent'}), 200
