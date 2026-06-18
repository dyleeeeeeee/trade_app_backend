from quart import Blueprint, request, jsonify, current_app, g
from quart_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity
from ..middleware import jwt_required_custom
from ..utils.email import email_service
from datetime import timedelta

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
            # Check if user account is blocked
            if user['is_blocked']:
                return jsonify({'message': 'Your account has been blocked. Please contact support.'}), 403
            
            # Create long-lived JWT token (24 hours)
            access_token = create_access_token(identity=str(user['id']), expires_delta=timedelta(hours=24))

            print(f"DEBUG: Created JWT token for user_id = {user['id']} with secret key: {current_app.config.get('JWT_SECRET_KEY', 'NOT SET')}")  # Debug log

            # Send login notification email (don't await to avoid blocking login)
            import asyncio
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr) or 'Unknown'
            ip_address = ip_address.split(',')[0].strip()
            user_agent = request.headers.get('User-Agent', 'Unknown')
            asyncio.create_task(email_service.send_login_notification(user['email'], ip_address, user_agent))

            return jsonify({
                'access_token': access_token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'role': user['role']
                }
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

        # Create long-lived JWT token (24 hours)
        access_token = create_access_token(identity=str(user['id']), expires_delta=timedelta(hours=24))

        print(f"DEBUG: Created JWT token for new user_id = {user['id']} with secret key: {current_app.config.get('JWT_SECRET_KEY', 'NOT SET')}")

        # Send welcome email (don't await to avoid blocking signup)
        import asyncio
        asyncio.create_task(email_service.send_welcome_email(user['email']))

        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'role': user['role']
            }
        }), 201

@auth_bp.route('/logout', methods=['POST'])
async def logout():
    # With JWT, logout is handled client-side by removing tokens
    # No server-side action needed since tokens are stateless
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/user', methods=['GET'])
@jwt_required_custom
async def get_current_user():
    user_id = g.user_id
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

    async with current_app.db_pool.acquire() as conn:
        user = await conn.fetchrow('SELECT id FROM users WHERE email = $1', email)

        if user:
            import secrets
            import asyncio
            from datetime import datetime, timezone, timedelta as _timedelta
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + _timedelta(hours=1)
            try:
                # Persist the token so it can be validated when the user returns.
                await conn.execute('''
                    INSERT INTO password_reset_tokens (user_id, token, expires_at)
                    VALUES ($1, $2, $3)
                ''', user['id'], reset_token, expires_at)
                asyncio.create_task(email_service.send_password_reset_email(email, reset_token))
            except Exception as e:
                # Don't break the request if the table is missing (run the migration).
                print(f"forgot-password: could not persist reset token: {e}")

    # Uniform response regardless of whether the account exists (no enumeration).
    return jsonify({'message': 'If an account exists for that email, a reset link has been sent.'}), 200


@auth_bp.route('/reset-password', methods=['POST'])
async def reset_password():
    data = await request.get_json()
    token = data.get('token')
    new_password = data.get('password')

    if not token or not new_password:
        return jsonify({'message': 'Token and new password are required'}), 400
    if len(new_password) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400

    try:
        async with current_app.db_pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow('''
                    SELECT prt.id, prt.user_id, u.email
                    FROM password_reset_tokens prt
                    JOIN users u ON u.id = prt.user_id
                    WHERE prt.token = $1 AND prt.used = false AND prt.expires_at > now()
                ''', token)

                if not row:
                    return jsonify({'message': 'This reset link is invalid or has expired.'}), 400

                await conn.execute('UPDATE users SET password = $1 WHERE id = $2', new_password, row['user_id'])
                await conn.execute('UPDATE password_reset_tokens SET used = true WHERE id = $1', row['id'])
    except Exception as e:
        print(f"reset-password error: {e}")
        return jsonify({'message': 'This reset link is invalid or has expired.'}), 400

    # Confirm the change after it has committed (fire-and-forget).
    import asyncio
    asyncio.create_task(email_service.send_password_changed_email(row['email']))
    return jsonify({'message': 'Your password has been reset. You can now sign in.'}), 200
