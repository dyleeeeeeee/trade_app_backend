from quart import Blueprint, request, jsonify, current_app, g
from ..utils.email import email_service

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users', methods=['GET'])
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
async def update_user_balance(user_id):
    data = await request.get_json()
    new_balance = data.get('balance', 0)

    if new_balance < 0:
        return jsonify({'message': 'Balance cannot be negative'}), 400

    async with current_app.db_pool.acquire() as conn:
        async with conn.transaction():
            # Get current balance and profit
            current_balance_result = await conn.fetchrow('''
                SELECT balance_after
                FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            ''', user_id)

            current_profit_result = await conn.fetchrow('''
                SELECT profit_after
                FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            ''', user_id)

            current_balance = float(current_balance_result['balance_after']) if current_balance_result else 0.0
            current_profit = float(current_profit_result['profit_after']) if current_profit_result else 0.0

            # Calculate adjustment amount
            adjustment = new_balance - current_balance

            if adjustment != 0:
                # Add adjustment transaction
                transaction_type = 'admin_adjustment_positive' if adjustment > 0 else 'admin_adjustment_negative'

                await conn.execute('''
                    INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after, profit_before, profit_after)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', user_id, transaction_type, abs(adjustment), current_balance, new_balance, current_profit, current_profit)

            return jsonify({
                'message': 'User balance updated successfully',
                'previous_balance': current_balance,
                'new_balance': new_balance,
                'adjustment': adjustment
            }), 200

@admin_bp.route('/admin/users/<int:user_id>/balance-info', methods=['GET'])
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

@admin_bp.route('/admin/users/<int:user_id>/profit', methods=['POST'])
async def update_user_profit(user_id):
    data = await request.get_json()
    new_profit = data.get('profit', 0)

    if new_profit < 0:
        return jsonify({'message': 'Profit cannot be negative'}), 400

    async with current_app.db_pool.acquire() as conn:
        async with conn.transaction():
            # Get current profit - use the most recent profit_after
            current_profit_result = await conn.fetchrow('''
                SELECT profit_after
                FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            ''', user_id)

            current_profit = float(current_profit_result['profit_after']) if current_profit_result else 0.0

            # Get current balance for reference
            current_balance_result = await conn.fetchrow('''
                SELECT balance_after
                FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            ''', user_id)

            current_balance = float(current_balance_result['balance_after']) if current_balance_result else 0.0

            # Calculate adjustment amount
            adjustment = new_profit - current_profit

            if adjustment != 0:
                # Add adjustment transaction
                transaction_type = 'profit_adjustment_positive' if adjustment > 0 else 'profit_adjustment_negative'

                await conn.execute('''
                    INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after, profit_before, profit_after)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', user_id, transaction_type, abs(adjustment), current_balance, current_balance, current_profit, new_profit)

                # Update profit snapshots for advanced tracking
                await conn.execute('''
                    INSERT INTO profit_snapshots (user_id, total_profit, strategy_profits, trading_profits, subscription_profits)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id, snapshot_date)
                    DO UPDATE SET
                        total_profit = EXCLUDED.total_profit,
                        strategy_profits = EXCLUDED.strategy_profits,
                        trading_profits = EXCLUDED.trading_profits,
                        subscription_profits = EXCLUDED.subscription_profits
                ''', user_id, new_profit, 0, 0, 0)

            return jsonify({
                'message': 'User profit updated successfully',
                'previous_profit': current_profit,
                'new_profit': new_profit,
                'adjustment': adjustment
            }), 200

@admin_bp.route('/admin/users/<int:user_id>/profit-info', methods=['GET'])
async def get_user_profit(user_id):
    async with current_app.db_pool.acquire() as conn:
        # Get the most recent profit_after
        result = await conn.fetchrow('''
            SELECT profit_after
            FROM wallet_transactions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        ''', user_id)

        profit = float(result['profit_after']) if result else 0.0

        return jsonify({'profit': profit}), 200
