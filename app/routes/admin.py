from quart import Blueprint, request, jsonify, g, current_app
from ..middleware import admin_required
from ..utils.email import email_service

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users', methods=['GET'])
@admin_required
async def get_users():
    async with current_app.db_pool.acquire() as conn:
        users = await conn.fetch('''
            SELECT id, email, role, is_blocked, created_at
            FROM users
            ORDER BY created_at DESC
        ''')

        user_list = [{
            'id': u['id'],
            'email': u['email'],
            'role': u['role'],
            'blocked': u['is_blocked']
        } for u in users]

        return jsonify({'users': user_list}), 200

@admin_bp.route('/admin/users/<int:user_id>/block', methods=['POST'])
@admin_required
async def block_user(user_id):
    data = await request.get_json()
    block = data.get('block', False)

    async with current_app.db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE users
            SET is_blocked = $1
            WHERE id = $2
        ''', block, user_id)

        return jsonify({'message': f'User {"blocked" if block else "unblocked"} successfully'}), 200

@admin_bp.route('/admin/withdrawals', methods=['GET'])
@admin_required
async def get_withdrawals():
    async with current_app.db_pool.acquire() as conn:
        withdrawals = await conn.fetch('''
            SELECT w.id, w.amount, w.status, w.requested_at, u.email as user_email
            FROM withdrawals w
            JOIN users u ON w.user_id = u.id
            ORDER BY w.requested_at DESC
        ''')

        withdrawal_list = [{
            'id': w['id'],
            'amount': float(w['amount']),
            'status': w['status'],
            'user_email': w['user_email'],
            'requested_at': w['requested_at'].isoformat()
        } for w in withdrawals]

        return jsonify({'withdrawals': withdrawal_list}), 200

@admin_bp.route('/admin/withdrawals/<int:withdrawal_id>/approve', methods=['POST'])
@admin_required
async def approve_withdrawal(withdrawal_id):
    async with current_app.db_pool.acquire() as conn:
        async with conn.transaction():
            # Get withdrawal details
            withdrawal = await conn.fetchrow('''
                SELECT * FROM withdrawals WHERE id = $1 AND status = 'pending'
            ''', withdrawal_id)

            if not withdrawal:
                return jsonify({'message': 'Withdrawal not found or already processed'}), 404

            # Update withdrawal status
            await conn.execute('''
                UPDATE withdrawals
                SET status = 'approved', processed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            ''', withdrawal_id)

            # Deduct from user balance
            await conn.execute('''
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after)
                SELECT $1, 'withdraw', $2,
                       COALESCE(SUM(CASE WHEN transaction_type IN ('deposit', 'transfer_in', 'trade_sell') THEN amount
                                         WHEN transaction_type IN ('withdraw', 'transfer_out', 'trade_buy') THEN -amount END), 0),
                       COALESCE(SUM(CASE WHEN transaction_type IN ('deposit', 'transfer_in', 'trade_sell') THEN amount
                                         WHEN transaction_type IN ('withdraw', 'transfer_out', 'trade_buy') THEN -amount END), 0) - $2
                FROM wallet_transactions WHERE user_id = $1
            ''', withdrawal['user_id'], float(withdrawal['amount']))

            # Get user email for notification
            user = await conn.fetchrow('SELECT email FROM users WHERE id = $1', withdrawal['user_id'])

            # Send approval email (don't await to avoid blocking)
            import asyncio
            asyncio.create_task(email_service.send_withdrawal_approved_email(user['email'], float(withdrawal['amount']), withdrawal_id))

            return jsonify({'message': 'Withdrawal approved successfully'}), 200

@admin_bp.route('/admin/users/<int:user_id>/balance', methods=['POST'])
@admin_required
async def update_user_balance(user_id):
    data = await request.get_json()
    new_balance = data.get('balance', 0)

    if new_balance < 0:
        return jsonify({'message': 'Balance cannot be negative'}), 400

    async with current_app.db_pool.acquire() as conn:
        async with conn.transaction():
            # Get current balance - use the most recent balance_after
            current_balance_result = await conn.fetchrow('''
                SELECT balance_after
                FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            ''', user_id)

            current_balance = float(current_balance_result['balance_after']) if current_balance_result else 0.0

            # Calculate adjustment amount
            adjustment = new_balance - current_balance

            if adjustment != 0:
                # Add adjustment transaction
                transaction_type = 'admin_adjustment_positive' if adjustment > 0 else 'admin_adjustment_negative'

                await conn.execute('''
                    INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, transaction_type, abs(adjustment), current_balance, new_balance)

            return jsonify({
                'message': 'User balance updated successfully',
                'previous_balance': current_balance,
                'new_balance': new_balance,
                'adjustment': adjustment
            }), 200

@admin_bp.route('/admin/users/<int:user_id>/balance-info', methods=['GET'])
@admin_required
async def get_user_balance(user_id):
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
