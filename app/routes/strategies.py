from quart import Blueprint, request, jsonify, g, current_app
from ..middleware import login_required
from ..utils.email import email_service

strategy_bp = Blueprint('strategy', __name__)

# Strategy data for seeding
DEFAULT_STRATEGIES = [
    {
        'name': 'BTC Momentum',
        'description': 'Rides Bitcoin trends using technical indicators and market sentiment analysis',
        'category': 'crypto',
        'risk_level': 'high',
        'expected_roi': 0.85,  # 0.85% daily
        'min_investment': 1000.00,
        'max_investment': 100000.00
    },
    {
        'name': 'ETH Long-term Hold',
        'description': 'Strategic accumulation of Ethereum during market dips for long-term growth',
        'category': 'crypto',
        'risk_level': 'medium',
        'expected_roi': 0.65,  # 0.65% daily
        'min_investment': 500.00,
        'max_investment': 50000.00
    },
    {
        'name': 'Stablecoin Yield',
        'description': 'Earn consistent returns through stablecoin lending and liquidity provision',
        'category': 'crypto',
        'risk_level': 'low',
        'expected_roi': 0.25,  # 0.25% daily
        'min_investment': 100.00,
        'max_investment': 10000.00
    },
    {
        'name': 'Altcoin Gems',
        'description': 'High-risk, high-reward strategy focusing on emerging cryptocurrencies',
        'category': 'crypto',
        'risk_level': 'high',
        'expected_roi': 3.25,  # 3.25% daily
        'min_investment': 2000.00,
        'max_investment': 50000.00
    },
    {
        'name': 'Mean Reversion',
        'description': 'Exploits price deviations from historical averages across multiple assets',
        'category': 'quant',
        'risk_level': 'medium',
        'expected_roi': 0.75,  # 0.75% daily
        'min_investment': 1500.00,
        'max_investment': 75000.00
    },
    {
        'name': 'Momentum Trading',
        'description': 'Follows strong price trends using algorithmic signals and volume analysis',
        'category': 'quant',
        'risk_level': 'medium',
        'expected_roi': 1.05,  # 1.05% daily
        'min_investment': 1000.00,
        'max_investment': 100000.00
    },
    {
        'name': 'Arbitrage Simulation',
        'description': 'Simulates cross-exchange arbitrage opportunities in real-time',
        'category': 'quant',
        'risk_level': 'low',
        'expected_roi': 0.35,  # 0.35% daily
        'min_investment': 5000.00,
        'max_investment': 250000.00
    },
    {
        'name': 'AI Predictor',
        'description': 'Machine learning model predicting short-term price movements',
        'category': 'quant',
        'risk_level': 'high',
        'expected_roi': 2.25,  # 2.25% daily
        'min_investment': 3000.00,
        'max_investment': 150000.00
    }
]

@strategy_bp.route('', methods=['GET'])
@login_required
async def get_strategies():
    """Get all available strategies"""
    try:
        async with current_app.db_pool.acquire() as conn:
            # Seed strategies if they don't exist
            existing_count = await conn.fetchval('SELECT COUNT(*) FROM strategies')
            if existing_count == 0:
                for strategy_data in DEFAULT_STRATEGIES:
                    await conn.execute('''
                        INSERT INTO strategies (name, description, category, risk_level, expected_roi, min_investment, max_investment)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ''', strategy_data['name'], strategy_data['description'], strategy_data['category'],
                         strategy_data['risk_level'], strategy_data['expected_roi'], strategy_data['min_investment'], strategy_data['max_investment'])

            # Get all strategies with subscriber counts
            rows = await conn.fetch('''
                SELECT s.*,
                       COUNT(ss.id) as subscriber_count,
                       COALESCE(SUM(ss.invested_amount), 0) as total_invested
                FROM strategies s
                LEFT JOIN strategy_subscriptions ss ON s.id = ss.strategy_id AND ss.is_active = true
                WHERE s.is_active = true
                GROUP BY s.id
                ORDER BY s.category, s.expected_roi DESC
            ''')

            strategies = []
            for row in rows:
                strategies.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'category': row['category'],
                    'risk_level': row['risk_level'],
                    'expected_roi': float(row['expected_roi']),
                    'min_investment': float(row['min_investment']),
                    'max_investment': float(row['max_investment']) if row['max_investment'] else None,
                    'subscriber_count': row['subscriber_count'],
                    'total_invested': float(row['total_invested'])
                })

            return jsonify({'strategies': strategies}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting strategies: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@strategy_bp.route('/my-strategies', methods=['GET'])
@login_required
async def get_my_strategies():
    """Get user's active strategy subscriptions with calculated earnings based on time elapsed"""
    try:
        user_id = g.user['id']
        async with current_app.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT ss.id, ss.strategy_id, ss.invested_amount, ss.subscribed_at,
                       s.name, s.description, s.category, s.risk_level, s.expected_roi
                FROM strategy_subscriptions ss
                JOIN strategies s ON ss.strategy_id = s.id
                WHERE ss.user_id = $1 AND ss.is_active = true
                ORDER BY ss.subscribed_at DESC
            ''', user_id)

            my_strategies = []
            from datetime import datetime, timezone

            for row in rows:
                invested_amount = float(row['invested_amount'])
                daily_roi_rate = float(row['expected_roi']) / 100  # Convert percentage to decimal
                subscribed_at = row['subscribed_at']

                # Calculate days elapsed since subscription
                if isinstance(subscribed_at, datetime):
                    # Ensure we're working with timezone-aware datetime
                    if subscribed_at.tzinfo is None:
                        subscribed_at = subscribed_at.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    days_elapsed = (now - subscribed_at).total_seconds() / (24 * 60 * 60)
                else:
                    days_elapsed = 1  # Fallback

                # Calculate total earnings: daily_roi_rate * invested_amount * days_elapsed
                # Add some randomization for realism (±20%)
                import random
                variance_factor = 0.8 + (random.random() * 0.4)  # Between 0.8 and 1.2
                base_daily_earnings = daily_roi_rate * invested_amount
                actual_daily_earnings = base_daily_earnings * variance_factor

                # Ensure minimum earnings
                actual_daily_earnings = max(actual_daily_earnings, invested_amount * 0.0001)

                total_earnings = actual_daily_earnings * days_elapsed

                # Only count full days for display
                full_days_active = int(days_elapsed)

                my_strategies.append({
                    'subscription_id': row['id'],
                    'strategy_id': row['strategy_id'],
                    'strategy_name': row['name'],
                    'description': row['description'],
                    'category': row['category'],
                    'risk_level': row['risk_level'],
                    'expected_roi': float(row['expected_roi']),
                    'invested_amount': invested_amount,
                    'total_earnings': total_earnings,
                    'days_active': full_days_active,
                    'subscribed_at': row['subscribed_at'].isoformat() if row['subscribed_at'] else None
                })

            return jsonify({'strategies': my_strategies}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting user strategies: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@strategy_bp.route('/<int:strategy_id>/subscribe', methods=['POST'])
@login_required
async def subscribe_to_strategy(strategy_id):
    """Subscribe to a strategy with investment amount"""
    try:
        data = await request.get_json()
        invested_amount = data.get('invested_amount', 0)

        if not invested_amount or invested_amount <= 0:
            return jsonify({'error': 'Valid investment amount required'}), 400

        user_id = g.user['id']

        async with current_app.db_pool.acquire() as conn:
            # Check if strategy exists and is active
            strategy = await conn.fetchrow('SELECT * FROM strategies WHERE id = $1 AND is_active = true', strategy_id)
            if not strategy:
                return jsonify({'error': 'Strategy not found'}), 404

            # Check investment limits
            if invested_amount < float(strategy['min_investment']):
                return jsonify({'error': f'Minimum investment is ${strategy["min_investment"]}'}), 400

            if strategy['max_investment'] and invested_amount > float(strategy['max_investment']):
                return jsonify({'error': f'Maximum investment is ${strategy["max_investment"]}'}), 400

            # Check user's wallet balance
            balance_row = await conn.fetchrow('''
                SELECT balance_after FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC LIMIT 1
            ''', user_id)

            current_balance = float(balance_row['balance_after']) if balance_row else 0

            if current_balance < invested_amount:
                return jsonify({'error': 'Insufficient balance'}), 400

            # Check if user is already subscribed
            existing = await conn.fetchrow('SELECT id FROM strategy_subscriptions WHERE user_id = $1 AND strategy_id = $2 AND is_active = true', user_id, strategy_id)
            if existing:
                return jsonify({'error': 'Already subscribed to this strategy'}), 400

            # Create subscription
            subscription_id = await conn.fetchval('''
                INSERT INTO strategy_subscriptions (user_id, strategy_id, invested_amount)
                VALUES ($1, $2, $3)
                RETURNING id
            ''', user_id, strategy_id, invested_amount)

            # Deduct from wallet
            await conn.execute('''
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after)
                VALUES ($1, 'strategy_investment', $2, $3, $4)
            ''', user_id, -invested_amount, current_balance, current_balance - invested_amount)

            # Send subscription confirmation email (don't await to avoid blocking)
            import asyncio
            asyncio.create_task(email_service.send_strategy_subscription_email(
                g.user['email'], strategy['name'], float(invested_amount), 
                float(strategy['expected_roi']), strategy['risk_level']
            ))

            return jsonify({
                'message': f'Successfully subscribed to {strategy["name"]}',
                'subscription_id': subscription_id
            }), 201

    except Exception as e:
        current_app.logger.error(f"Error subscribing to strategy: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@strategy_bp.route('/<int:strategy_id>/unsubscribe', methods=['POST'])
@login_required
async def unsubscribe_from_strategy(strategy_id):
    """Unsubscribe from a strategy"""
    try:
        user_id = g.user['id']

        async with current_app.db_pool.acquire() as conn:
            # Find active subscription
            subscription = await conn.fetchrow('''
                SELECT ss.*, s.name, s.expected_roi FROM strategy_subscriptions ss
                JOIN strategies s ON ss.strategy_id = s.id
                WHERE ss.user_id = $1 AND ss.strategy_id = $2 AND ss.is_active = true
            ''', user_id, strategy_id)

            if not subscription:
                return jsonify({'error': 'No active subscription found'}), 404

            # Calculate total earnings based on time elapsed
            invested_amount = float(subscription['invested_amount'])
            daily_roi_rate = float(subscription['expected_roi']) / 100  # Convert percentage to decimal
            subscribed_at = subscription['subscribed_at']

            from datetime import datetime, timezone
            if isinstance(subscribed_at, datetime):
                if subscribed_at.tzinfo is None:
                    subscribed_at = subscribed_at.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_elapsed = (now - subscribed_at).total_seconds() / (24 * 60 * 60)
            else:
                days_elapsed = 1  # Fallback

            # Calculate total earnings with randomization
            import random
            variance_factor = 0.8 + (random.random() * 0.4)  # Between 0.8 and 1.2
            base_daily_earnings = daily_roi_rate * invested_amount
            actual_daily_earnings = base_daily_earnings * variance_factor
            actual_daily_earnings = max(actual_daily_earnings, invested_amount * 0.0001)
            total_earnings = actual_daily_earnings * days_elapsed

            return_amount = invested_amount + total_earnings

            # Get current balance
            balance_row = await conn.fetchrow('''
                SELECT balance_after FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC LIMIT 1
            ''', user_id)
            current_balance = float(balance_row['balance_after']) if balance_row else 0

            # Update subscription as inactive
            await conn.execute('''
                UPDATE strategy_subscriptions
                SET is_active = false, unsubscribed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            ''', subscription['id'])

            # Return invested amount + earnings to wallet
            await conn.execute('''
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after)
                VALUES ($1, 'strategy_unsubscription', $2, $3, $4)
            ''', user_id, return_amount, current_balance, current_balance + return_amount)

            return jsonify({
                'message': f'Successfully unsubscribed from {subscription["name"]}',
                'returned_amount': return_amount,
                'invested_amount': invested_amount,
                'earnings': total_earnings
            }), 200

    except Exception as e:
        current_app.logger.error(f"Error unsubscribing from strategy: {e}")
        return jsonify({'error': 'Internal server error'}), 500
