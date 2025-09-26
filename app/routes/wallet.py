from quart import Blueprint, request, jsonify, current_app, g
from ..middleware import jwt_required_custom
from ..utils.email import email_service

wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/wallet', methods=['GET'])
@jwt_required_custom
async def get_balance():
    user_id = g.user_id

    async with current_app.db_pool.acquire() as conn:
        # Get the most recent balance_after
        result = await conn.fetchrow('''
            SELECT balance_after
            FROM wallet_transactions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        ''', user_id)

        balance = float(result['balance_after']) if result else 0.0

        return jsonify({'balance': balance}), 200

@wallet_bp.route('/deposit', methods=['POST'])
@jwt_required_custom
async def deposit():
    data = await request.get_json()
    amount = data.get('amount', 0)

    if amount <= 0:
        return jsonify({'message': 'Invalid amount'}), 400

    user_id = g.user_id

    async with current_app.db_pool.acquire() as conn:
        async with conn.transaction():
            # Get current balance
            balance_result = await conn.fetchrow('''
                SELECT balance_after
                FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            ''', user_id)

            balance_before = float(balance_result['balance_after']) if balance_result else 0.0
            balance_after = balance_before + amount

            # Insert transaction
            await conn.execute('''
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after)
                VALUES ($1, 'deposit', $2, $3, $4)
            ''', user_id, amount, balance_before, balance_after)

            return jsonify({'message': 'Deposit successful', 'balance': balance_after}), 200

@wallet_bp.route('/withdraw', methods=['POST'])
@jwt_required_custom
async def withdraw():
    data = await request.get_json()
    amount = data.get('amount', 0)

    if amount <= 0:
        return jsonify({'message': 'Invalid amount'}), 400

    user_id = g.user_id

    async with current_app.db_pool.acquire() as conn:
        async with conn.transaction():
            # Check balance
            balance_result = await conn.fetchrow('''
                SELECT balance_after
                FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            ''', user_id)

            balance = float(balance_result['balance_after']) if balance_result else 0.0

            if balance < amount:
                return jsonify({'message': 'Insufficient balance'}), 400

            # Create withdrawal request
            withdrawal = await conn.fetchrow('''
                INSERT INTO withdrawals (user_id, amount)
                VALUES ($1, $2)
                RETURNING id, amount, status, requested_at
            ''', user_id, amount)

            # Send withdrawal request email (don't await to avoid blocking)
            import asyncio
            asyncio.create_task(email_service.send_withdrawal_request_email(g.user['email'], float(amount), withdrawal['id']))

            return jsonify({
                'message': 'Withdrawal request submitted',
                'withdrawal': {
                    'id': withdrawal['id'],
                    'amount': float(withdrawal['amount']),
                    'status': withdrawal['status'],
                    'requested_at': withdrawal['requested_at'].isoformat()
                }
            }), 200

@wallet_bp.route('/transfer', methods=['POST'])
@jwt_required_custom
async def transfer():
    data = await request.get_json()
    recipient_email = data.get('recipient')
    amount = data.get('amount', 0)

    if not recipient_email or amount <= 0:
        return jsonify({'message': 'Recipient email and valid amount required'}), 400

    user_id = g.user_id

    async with current_app.db_pool.acquire() as conn:
        async with conn.transaction():
            # Get recipient
            recipient = await conn.fetchrow('SELECT id FROM users WHERE email = $1', recipient_email)
            if not recipient:
                return jsonify({'message': 'Recipient not found'}), 404

            if recipient['id'] == user_id:
                return jsonify({'message': 'Cannot transfer to yourself'}), 400

            # Check sender balance
            balance_result = await conn.fetchrow('''
                SELECT balance_after
                FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            ''', user_id)

            sender_balance = float(balance_result['balance_after']) if balance_result else 0.0

            if sender_balance < amount:
                return jsonify({'message': 'Insufficient balance'}), 400

            # Record transactions
            await conn.execute('''
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after)
                VALUES ($1, 'transfer_out', $2, $3, $4)
            ''', user_id, -amount, sender_balance, sender_balance - amount)

            # Get recipient's current balance
            recipient_balance_result = await conn.fetchrow('''
                SELECT balance_after
                FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            ''', recipient['id'])

            recipient_balance_before = float(recipient_balance_result['balance_after']) if recipient_balance_result else 0.0
            recipient_balance_after = recipient_balance_before + amount

            await conn.execute('''
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after)
                VALUES ($1, 'transfer_in', $2, $3, $4)
            ''', recipient['id'], amount, recipient_balance_before, recipient_balance_after)

            return jsonify({'message': 'Transfer successful'}), 200

@wallet_bp.route('/withdrawals', methods=['GET'])
@jwt_required_custom
async def get_withdrawals():
    user_id = g.user_id

    async with current_app.db_pool.acquire() as conn:
        withdrawals = await conn.fetch('''
            SELECT id, amount, status, requested_at
            FROM withdrawals
            WHERE user_id = $1
            ORDER BY requested_at DESC
        ''', user_id)

        withdrawal_list = [{
            'id': w['id'],
            'amount': float(w['amount']),
            'status': w['status'],
            'created_at': w['requested_at'].isoformat()
        } for w in withdrawals]

        return jsonify({'withdrawals': withdrawal_list}), 200

@wallet_bp.route('/deposits', methods=['GET'])
@jwt_required_custom
async def get_deposits():
    user_id = g.user_id

    async with current_app.db_pool.acquire() as conn:
        deposits = await conn.fetch('''
            SELECT id, transaction_type, amount, balance_before, balance_after, created_at
            FROM wallet_transactions
            WHERE user_id = $1 AND transaction_type = 'deposit'
            ORDER BY created_at DESC
        ''', user_id)

        deposit_list = [{
            'id': d['id'],
            'amount': float(d['amount']),
            'balance_before': float(d['balance_before']),
            'balance_after': float(d['balance_after']),
            'created_at': d['created_at'].isoformat(),
            'type': d['transaction_type']
        } for d in deposits]

        return jsonify({'deposits': deposit_list}), 200
