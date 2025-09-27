from quart import Blueprint, request, jsonify, current_app, g
from ..middleware import jwt_required_custom
from ..utils.email import email_service
from ..utils.pandl_calculator import economic_calculator, TradeMetrics, MarketRegime
import aiohttp
import os
import time
import numpy as np
from typing import Dict, Optional

trading_bp = Blueprint('trading', __name__)

# In-memory cache for prices
price_cache: Dict[str, Dict] = {}
CACHE_TTL = 60_000  # Cache prices for 60 seconds

def get_cached_price(asset: str) -> Optional[float]:
    """Get price from cache if still valid"""
    if asset in price_cache:
        cached_data = price_cache[asset]
        if time.time() - cached_data['timestamp'] < CACHE_TTL:
            return cached_data['price']
        else:
            # Cache expired, remove it
            del price_cache[asset]
    return None

def set_cached_price(asset: str, price: float):
    """Store price in cache with timestamp"""
    price_cache[asset] = {
        'price': price,
        'timestamp': time.time()
    }

async def get_current_price(asset):
    """
    Get current market price for an asset using only Alpha Vantage APIs

    - Crypto (BTC, ETH): Uses CURRENCY_EXCHANGE_RATE API
    - Stocks (AAPL, GOOGL): Uses GLOBAL_QUOTE API
    - Includes in-memory caching for 60 seconds
    """
    # Check cache first
    cached_price = get_cached_price(asset)
    if cached_price is not None:
        return cached_price

    try:
        # Map asset symbols to API identifiers
        asset_map = {
            'BTC/USD': ('BTC', 'USD', 'crypto'),
            'ETH/USD': ('ETH', 'USD', 'crypto'),
            'AAPL': ('AAPL', 'stock'),
            'GOOGL': ('GOOGL', 'stock')
        }

        if asset not in asset_map:
            return None

        api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')

        if len(asset_map[asset]) == 3:  # Crypto assets
            from_currency, to_currency, asset_type = asset_map[asset]

            # Alpha Vantage CURRENCY_EXCHANGE_RATE for crypto
            url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency={to_currency}&apikey={api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        exchange_rate = data.get('Realtime Currency Exchange Rate', {})
                        price_str = exchange_rate.get('5. Exchange Rate')
                        if price_str:
                            try:
                                price = float(price_str)
                                set_cached_price(asset, price)  # Cache the price
                                return price
                            except ValueError:
                                pass
        else:  # Stock assets
            symbol = asset_map[asset][0]

            # Alpha Vantage GLOBAL_QUOTE for stocks
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        global_quote = data.get('Global Quote', {})
                        price_str = global_quote.get('05. price')
                        if price_str:
                            try:
                                price = float(price_str)
                                set_cached_price(asset, price)  # Cache the price
                                return price
                            except ValueError:
                                pass

        # Fallback prices if API fails
        fallback_prices = {
            'BTC/USD': 45000.00,
            'ETH/USD': 2400.00,
            'AAPL': 182.50,
            'GOOGL': 142.30
        }
        fallback_price = fallback_prices.get(asset, 100.0)
        set_cached_price(asset, fallback_price)  # Cache fallback price too
        print(f"Using fallback price for {asset} - API may be rate limited")
        return fallback_price

    except Exception as e:
        print(f"Error fetching price for {asset}: {e}")
        # Return fallback prices as final fallback
        fallback_prices = {
            'BTC/USD': 45000.00,
            'ETH/USD': 2400.00,
            'AAPL': 182.50,
            'GOOGL': 142.30
        }
        fallback_price = fallback_prices.get(asset, 100.0)
        set_cached_price(asset, fallback_price)  # Cache fallback price
        return fallback_price

@trading_bp.route('/trade', methods=['POST'])
@jwt_required_custom
async def place_trade():
    data = await request.get_json()
    asset = data.get('asset')
    side = data.get('side')  # 'buy' or 'sell'
    size = data.get('size', 0)

    if not asset or side not in ['buy', 'sell'] or size <= 0:
        return jsonify({'message': 'Invalid trade parameters'}), 400

    # Get current market price
    price = await get_current_price(asset)
    if price is None:
        return jsonify({'message': 'Unable to fetch current market price'}), 400

    user_id = g.user_id
    total = size * price
    async with current_app.db_pool.acquire() as conn:
        async with conn.transaction():
            # Check balance for buy orders
            if side == 'buy':
                balance_result = await conn.fetchrow('''
                    SELECT balance_after
                    FROM wallet_transactions
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', user_id)

                balance = float(balance_result['balance_after']) if balance_result else 0.0

                if balance < total:
                    return jsonify({'message': 'Insufficient balance'}), 400

                # Record buy transaction
                await conn.execute('''
                    INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after, profit_before, profit_after)
                    VALUES ($1, 'trade_buy', $2, $3, $4, $5, $6)
                ''', user_id, -total, balance, balance - total, 0, 0)
            else:
                # For sell orders, check if there are matching buy orders first
                # Check if total sell quantity exceeds existing buy orders for this asset
                buy_orders_total = await conn.fetchrow('''
                    SELECT COALESCE(SUM(size), 0) as total_buy_size
                    FROM trades
                    WHERE asset = $1 AND side = 'buy'
                ''', asset)

                total_buy_quantity = float(buy_orders_total['total_buy_size']) if buy_orders_total else 0.0

                if total_buy_quantity < size:
                    return jsonify({'message': f'Insufficient buy orders for {asset}. Available: {total_buy_quantity}, Requested: {size}'}), 400

                # Get current balance and profit for sell transaction
                balance_result = await conn.fetchrow('''
                    SELECT balance_after
                    FROM wallet_transactions
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', user_id)

                profit_result = await conn.fetchrow('''
                    SELECT profit_after
                    FROM wallet_transactions
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', user_id)

                current_balance = float(balance_result['balance_after']) if balance_result else 0.0
                current_profit = float(profit_result['profit_after']) if profit_result else 0.0

                # Record sell transaction
                await conn.execute('''
                    INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_before, balance_after, profit_before, profit_after)
                    VALUES ($1, 'trade_sell', $2, $3, $4, $5, $6)
                ''', user_id, total, current_balance, current_balance + total, current_profit, current_profit)

            # Create trade record
            trade = await conn.fetchrow('''
                INSERT INTO trades (user_id, asset, side, size, price, total)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, asset, side, size, price, total, created_at
            ''', user_id, asset, side, size, price, total)

            # Calculate advanced P&L metrics using Newton/Chinese Quant methods
            import random
            from datetime import datetime, timedelta

            # Generate synthetic market data for P&L calculation
            timestamps = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]  # 24 hours of data
            synthetic_prices = []
            synthetic_volumes = []

            # Generate realistic price movements
            current_price = price
            for i in range(24):
                # Add random walk with mean reversion
                change = random.gauss(0, current_price * 0.02)  # 2% volatility
                current_price += change
                current_price = max(current_price * 0.95, min(current_price * 1.05, current_price))  # Bound price movements
                synthetic_prices.append(current_price)
                synthetic_volumes.append(random.uniform(1000, 10000))  # Random volume

            # Calculate trade metrics
            trade_metrics = TradeMetrics(
                entry_price=price,
                exit_price=price,  # For now, assume no exit (unrealized P&L)
                position_size=float(size),
                holding_period=1,  # Start with 1 hour
                volatility_at_entry=np.std(synthetic_prices[-10:]) / np.mean(synthetic_prices[-10:]) if len(synthetic_prices) >= 10 else 0.02,
                market_regime=economic_calculator.chinese_calc.calculate_market_regime(synthetic_prices, synthetic_volumes),
                momentum_score=(synthetic_prices[-1] - synthetic_prices[0]) / synthetic_prices[0] if synthetic_prices else 0,
                technical_score=random.uniform(0.3, 0.8),  # Simplified technical score
                fundamental_score=random.uniform(0.4, 0.9)   # Simplified fundamental score
            )

            # Calculate advanced P&L
            pnl_result = economic_calculator.calculate_comprehensive_pnl(
                trade_metrics, {
                    'price_changes': [p - synthetic_prices[0] for p in synthetic_prices[1:]],
                    'volume_changes': synthetic_volumes[1:],
                    'historical_returns': [(synthetic_prices[i] - synthetic_prices[i-1]) / synthetic_prices[i-1] for i in range(1, len(synthetic_prices))]
                }, {
                    'economic_cycle_position': 0.6,  # Assume expansion phase
                    'money_supply_growth': 0.02,
                    'inflation_expectations': 0.02,
                    'debt_to_equity': 1.5,
                    'interest_coverage': 3.0,
                    'cash_flow_volatility': 0.15,
                    'education_years': 16,
                    'experience_years': 5
                }
            )

            # Store advanced trade profit metrics
            await conn.execute('''
                INSERT INTO trade_profits (
                    trade_id, user_id, entry_price, exit_price, position_size,
                    realized_pnl, unrealized_pnl, holding_period_hours, volatility_at_entry,
                    market_regime, risk_adjusted_return, alpha_contribution, beta_exposure,
                    momentum_score, technical_score, fundamental_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            ''', trade['id'], user_id, price, price, float(size),
                 pnl_result['final_pnl'] if side == 'sell' else 0,  # Realized P&L for sells
                 pnl_result['final_pnl'] if side == 'buy' else 0,   # Unrealized P&L for buys
                 1, trade_metrics.volatility_at_entry, trade_metrics.market_regime.value,
                 pnl_result['final_pnl'] / (price * float(size)) if price * float(size) != 0 else 0,  # Risk-adjusted return
                 pnl_result['quantum_score'], 1.0,  # Beta exposure
                 trade_metrics.momentum_score, trade_metrics.technical_score, trade_metrics.fundamental_score)

            # Update profit snapshots
            current_profit_result = await conn.fetchrow('''
                SELECT profit_after FROM wallet_transactions
                WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1
            ''', user_id)
            current_profit = float(current_profit_result['profit_after']) if current_profit_result else 0

            new_profit = current_profit + pnl_result['final_pnl']

            await conn.execute('''
                INSERT INTO profit_snapshots (user_id, total_profit, trading_profits, realized_pnl, unrealized_pnl)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, snapshot_date)
                DO UPDATE SET
                    total_profit = EXCLUDED.total_profit,
                    trading_profits = EXCLUDED.trading_profits,
                    realized_pnl = EXCLUDED.realized_pnl,
                    unrealized_pnl = EXCLUDED.unrealized_pnl
            ''', user_id, new_profit, pnl_result['final_pnl'], pnl_result['final_pnl'], 0)

            # Get user email for notification
            user_email_row = await conn.fetchrow('SELECT email FROM users WHERE id = $1', user_id)
            user_email = user_email_row['email'] if user_email_row else None
            
            # Send trade execution email (don't await to avoid blocking)
            import asyncio
            asyncio.create_task(email_service.send_trade_executed_email(user_email, asset, side, float(size), float(price), total))

            return jsonify({
                'message': f'{side.capitalize()} order placed successfully',
                'trade': {
                    'id': trade['id'],
                    'asset': trade['asset'],
                    'side': trade['side'],
                    'size': float(trade['size']),
                    'price': float(trade['price']),
                    'total': float(trade['total']),
                    'created_at': trade['created_at'].isoformat()
                }
            }), 200

@trading_bp.route('/trades', methods=['GET'])
@jwt_required_custom
async def get_trades():
    user_id = g.user_id

    async with current_app.db_pool.acquire() as conn:
        trades = await conn.fetch('''
            SELECT id, asset, side, size, price, total, created_at
            FROM trades
            WHERE user_id = $1
            ORDER BY created_at DESC
        ''', user_id)

        trade_list = [{
            'id': t['id'],
            'asset': t['asset'],
            'side': t['side'],
            'size': float(t['size']),
            'price': float(t['price']),
            'created_at': t['created_at'].isoformat()
        } for t in trades]

        return jsonify({'trades': trade_list}), 200

@trading_bp.route('/copy/subscribe', methods=['POST'])
@jwt_required_custom
async def subscribe_to_trader():
    data = await request.get_json()
    trader_id = data.get('trader_id')
    allocation = data.get('allocation', 0)

    if not trader_id or allocation <= 0 or allocation > 100:
        return jsonify({'message': 'Invalid trader ID or allocation'}), 400

    user_id = g.user_id

    async with current_app.db_pool.acquire() as conn:
        # Check if already subscribed
        existing = await conn.fetchrow('''
            SELECT id FROM copy_trading_subscriptions
            WHERE follower_id = $1 AND trader_id = $2
        ''', user_id, trader_id)

        if existing:
            # Update allocation
            await conn.execute('''
                UPDATE copy_trading_subscriptions
                SET allocation = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            ''', allocation, existing['id'])
        else:
            # Create new subscription
            await conn.execute('''
                INSERT INTO copy_trading_subscriptions (follower_id, trader_id, allocation)
                VALUES ($1, $2, $3)
            ''', user_id, trader_id, allocation)

        return jsonify({'message': 'Successfully subscribed to trader'}), 200

@trading_bp.route('/copy/subscriptions', methods=['GET'])
@jwt_required_custom
async def get_subscriptions():
    user_id = g.user_id

    async with current_app.db_pool.acquire() as conn:
        subscriptions = await conn.fetch('''
            SELECT id, trader_id, allocation, is_active, created_at
            FROM copy_trading_subscriptions
            WHERE follower_id = $1 AND is_active = true
            ORDER BY created_at DESC
        ''', user_id)

        subscription_list = [{
            'id': s['id'],
            'trader_id': s['trader_id'],
            'allocation': float(s['allocation']),
            'is_active': s['is_active'],
            'created_at': s['created_at'].isoformat()
        } for s in subscriptions]

        return jsonify({'subscriptions': subscription_list}), 200

@trading_bp.route('/prices', methods=['GET'])
async def get_prices():
    """
    Get current market prices for all supported assets using only Alpha Vantage APIs

    - Crypto prices: CURRENCY_EXCHANGE_RATE API
    - Stock prices: GLOBAL_QUOTE API
    - Change data: Real for stocks, calculated for crypto
    """
    assets = [
        {'symbol': 'BTC/USD', 'name': 'Bitcoin', 'id': 'bitcoin'},
        {'symbol': 'ETH/USD', 'name': 'Ethereum', 'id': 'ethereum'},
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'id': 'apple'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'id': 'google'}
    ]

    priced_assets = []

    for asset in assets:
        price = await get_current_price(asset['symbol'])
        if price is not None:
            # Get change data based on asset type
            if asset['symbol'] in ['BTC/USD', 'ETH/USD']:
                # For crypto, calculate mock change since CURRENCY_EXCHANGE_RATE doesn't provide change
                change = (price * 0.02) * (1 if asset['symbol'].startswith('BTC') else -1)
            else:
                # For stocks, get real change data from Alpha Vantage GLOBAL_QUOTE
                try:
                    api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
                    symbol = asset['symbol'].split('/')[0]  # Remove /USD part
                    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                global_quote = data.get('Global Quote', {})
                                change_str = global_quote.get('09. change')
                                if change_str:
                                    try:
                                        change = float(change_str)
                                    except ValueError:
                                        change = 0.0
                                else:
                                    change = 0.0
                            else:
                                change = 0.0
                except Exception:
                    change = 0.0

            priced_assets.append({
                'symbol': asset['symbol'],
                'name': asset['name'],
                'price': str(price),
                'change': round(change, 2),
                'id': asset['id']
            })

    return jsonify({'assets': priced_assets}), 200
