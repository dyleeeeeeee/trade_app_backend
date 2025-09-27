from quart import Blueprint, request, jsonify, current_app, g
from ..middleware import jwt_required_custom, admin_required
from ..utils.email import email_service
from ..utils.pandl_calculator import economic_calculator, TradeMetrics, MarketRegime
import random

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
@jwt_required_custom
async def get_my_strategies():
    """Get user's active strategy subscriptions with calculated earnings based on time elapsed"""
    try:
        user_id = g.user_id
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
                    if subscribed_at.tzinfo is None:
                        subscribed_at = subscribed_at.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    days_elapsed = (now - subscribed_at).total_seconds() / (24 * 60 * 60)
                else:
                    days_elapsed = 1  # Fallback

                # Only count full days for display
                full_days_active = int(days_elapsed)

                # Calculate total earnings using advanced P&L calculator
                # Generate synthetic market data for demonstration
                days_active = full_days_active
                if days_active == 0:
                    days_active = 1

                # Create synthetic daily returns based on strategy performance
                daily_returns = []
                base_daily_return = daily_roi_rate

                # Add volatility and market regime effects
                for day in range(days_active):
                    # Simulate market volatility
                    volatility_factor = 0.8 + (random.random() * 0.4)  # 0.8 to 1.2
                    regime_factor = 1.0

                    # Simulate different market regimes
                    regime_roll = random.random()
                    if regime_roll < 0.1:  # 10% chance of bear market
                        regime_factor = 0.7
                    elif regime_roll < 0.25:  # 15% chance of volatile market
                        regime_factor = 1.3
                    elif regime_roll < 0.6:  # 35% chance of bull market
                        regime_factor = 1.1

                    daily_return = base_daily_return * volatility_factor * regime_factor
                    daily_returns.append(daily_return)

                # Use advanced calculator for strategy performance
                performance = economic_calculator.calculate_strategy_performance_economics(
                    daily_returns, invested_amount, {
                        'time_period_days': days_active,
                        'risk_free_rate': 0.02,
                        'benchmark_return': 0.05,  # Market benchmark
                        'market_beta': 1.2,  # Strategy beta
                        'market_return': 0.06
                    }
                )

                # Calculate total earnings with advanced metrics
                total_earnings = invested_amount * performance.total_return

                # Ensure minimum earnings (guarantee)
                total_earnings = max(total_earnings, invested_amount * 0.0001 * days_active)

                # Store advanced performance metrics in database
                # First check if record exists, then update or insert accordingly
                existing_record = await conn.fetchrow('''
                    SELECT id FROM strategy_performance 
                    WHERE strategy_subscription_id = $1
                ''', row['id'])

                if existing_record:
                    # Update existing record
                    await conn.execute('''
                        UPDATE strategy_performance SET
                            user_id = $2, invested_amount = $3, current_value = $4,
                            realized_profits = $5, unrealized_profits = $6, total_return = $7, 
                            annualized_return = $8, volatility = $9, sharpe_ratio = $10,
                            sortino_ratio = $11, max_drawdown = $12, calmar_ratio = $13,
                            omega_ratio = $14, win_rate = $15, profit_factor = $16, 
                            expectancy = $17, recovery_factor = $18, ulcer_index = $19,
                            tail_ratio = $20, last_updated = CURRENT_TIMESTAMP
                        WHERE strategy_subscription_id = $1
                    ''', row['id'], user_id, invested_amount, invested_amount + total_earnings,
                         total_earnings, 0, performance.total_return, performance.annualized_return,
                         performance.volatility, performance.sharpe_ratio, performance.sortino_ratio,
                         performance.max_drawdown, performance.calmar_ratio, performance.omega_ratio,
                         performance.win_rate, performance.profit_factor, performance.expectancy,
                         performance.recovery_factor, performance.ulcer_index, performance.tail_ratio)
                else:
                    # Insert new record
                    await conn.execute('''
                        INSERT INTO strategy_performance (
                            strategy_subscription_id, user_id, invested_amount, current_value,
                            realized_profits, unrealized_profits, total_return, annualized_return,
                            volatility, sharpe_ratio, sortino_ratio, max_drawdown, calmar_ratio,
                            omega_ratio, win_rate, profit_factor, expectancy, recovery_factor,
                            ulcer_index, tail_ratio
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    ''', row['id'], user_id, invested_amount, invested_amount + total_earnings,
                         total_earnings, 0, performance.total_return, performance.annualized_return,
                         performance.volatility, performance.sharpe_ratio, performance.sortino_ratio,
                         performance.max_drawdown, performance.calmar_ratio, performance.omega_ratio,
                         performance.win_rate, performance.profit_factor, performance.expectancy,
                         performance.recovery_factor, performance.ulcer_index, performance.tail_ratio)

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
@jwt_required_custom
async def subscribe_to_strategy(strategy_id):
    """Subscribe to a strategy with investment amount"""
    try:
        data = await request.get_json()
        invested_amount = data.get('invested_amount', 0)

        if not invested_amount or invested_amount <= 0:
            return jsonify({'error': 'Valid investment amount required'}), 400

        user_id = g.user_id

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

            # Check user's wallet balance and profit
            balance_row = await conn.fetchrow('''
                SELECT balance_after FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC LIMIT 1
            ''', user_id)

            profit_row = await conn.fetchrow('''
                SELECT profit_after FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC LIMIT 1
            ''', user_id)

            current_balance = float(balance_row['balance_after']) if balance_row else 0
            current_profit = float(profit_row['profit_after']) if profit_row else 0

            if current_balance < invested_amount:
                return jsonify({'error': 'Insufficient balance'}), 400

            # Create subscription
            subscription_id = await conn.fetchval('''
                INSERT INTO strategy_subscriptions (user_id, strategy_id, invested_amount)
                VALUES ($1, $2, $3)
                RETURNING id
            ''', user_id, strategy_id, invested_amount)

            # Deduct from wallet
            await conn.execute('''
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after, profit_before, profit_after)
                VALUES ($1, 'strategy_investment', $2, $3, $4, $5, $6)
            ''', user_id, -invested_amount, current_balance, current_balance - invested_amount, current_profit, current_profit)

            # Get user email for notification
            user_email_row = await conn.fetchrow('SELECT email FROM users WHERE id = $1', user_id)
            user_email = user_email_row['email'] if user_email_row else None
            import asyncio
            asyncio.create_task(email_service.send_strategy_subscription_email(
                user_email, strategy['name'], float(invested_amount), 
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
@jwt_required_custom
async def unsubscribe_from_strategy(strategy_id):
    """Unsubscribe from a strategy"""
    try:
        user_id = g.user_id

        async with current_app.db_pool.acquire() as conn:
            # Find active subscription
            subscription = await conn.fetchrow('''
                SELECT ss.*, s.name, s.expected_roi FROM strategy_subscriptions ss
                JOIN strategies s ON ss.strategy_id = s.id
                WHERE ss.user_id = $1 AND ss.strategy_id = $2 AND ss.is_active = true
            ''', user_id, strategy_id)

            if not subscription:
                return jsonify({'error': 'No active subscription found'}), 404

            # Calculate total earnings based on time elapsed using advanced calculator
            invested_amount = float(subscription['invested_amount'])
            subscribed_at = subscription['subscribed_at']

            from datetime import datetime, timezone
            if isinstance(subscribed_at, datetime):
                if subscribed_at.tzinfo is None:
                    subscribed_at = subscribed_at.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_elapsed = (now - subscribed_at).total_seconds() / (24 * 60 * 60)
            else:
                days_elapsed = 1  # Fallback

            # Generate synthetic returns for advanced calculation
            days_active = max(1, int(days_elapsed))
            daily_returns = []
            daily_roi_rate = float(subscription['expected_roi']) / 100

            import random
            for day in range(days_active):
                volatility_factor = 0.8 + (random.random() * 0.4)
                regime_factor = 1.0

                regime_roll = random.random()
                if regime_roll < 0.1:
                    regime_factor = 0.7
                elif regime_roll < 0.25:
                    regime_factor = 1.3
                elif regime_roll < 0.6:
                    regime_factor = 1.1

                daily_return = daily_roi_rate * volatility_factor * regime_factor
                daily_returns.append(daily_return)

            # Use advanced calculator
            performance = economic_calculator.calculate_strategy_performance_economics(
                daily_returns, invested_amount, {
                    'time_period_days': days_active,
                    'risk_free_rate': 0.02,
                    'benchmark_return': 0.05,
                    'market_beta': 1.2,
                    'market_return': 0.06
                }
            )

            total_earnings = invested_amount * performance.total_return
            total_earnings = max(total_earnings, invested_amount * 0.0001 * days_active)

            return_amount = invested_amount + total_earnings

            # Get current balance and profit
            balance_row = await conn.fetchrow('''
                SELECT balance_after FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC LIMIT 1
            ''', user_id)

            profit_row = await conn.fetchrow('''
                SELECT profit_after FROM wallet_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC LIMIT 1
            ''', user_id)

            current_balance = float(balance_row['balance_after']) if balance_row else 0
            current_profit = float(profit_row['profit_after']) if profit_row else 0

            # Update subscription as inactive
            await conn.execute('''
                UPDATE strategy_subscriptions
                SET is_active = false, unsubscribed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            ''', subscription['id'])

            # Return invested amount + earnings to wallet
            await conn.execute('''
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after, profit_before, profit_after)
                VALUES ($1, 'strategy_unsubscription', $2, $3, $4, $5, $6)
            ''', user_id, return_amount, current_balance, current_balance + return_amount, current_profit, current_profit)

            return jsonify({
                'message': f'Successfully unsubscribed from {subscription["name"]}',
                'returned_amount': return_amount,
                'invested_amount': invested_amount,
                'earnings': total_earnings
            }), 200

    except Exception as e:
        current_app.logger.error(f"Error unsubscribing from strategy: {e}")
        return jsonify({'error': 'Internal server error'}), 500
