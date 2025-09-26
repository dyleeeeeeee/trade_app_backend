from quart import Quart, session, g
import asyncpg
from .config import Config
from .routes import register_routes
from .middleware import setup_middleware
import os
from quart_cors import cors # 👈 1. Import the cors function


async def create_app():
    app = Quart(__name__)
    
    # 💡 2. Apply CORS to your app.
    # This allows all origins for simplicity. For production, you should
    # restrict this to your frontend's domain, e.g., allow_origin="https://your-domain.com"
    app = cors(app, allow_origin="*") 

    # Load config
    config = Config()
    app.config.from_object(config)

    # Setup middleware
    setup_middleware(app)

    # Create database connection pool
    # Supabase requires SSL connections and has specific connection limits
    app.db_pool = await asyncpg.create_pool(
        config.DATABASE_URL,
        min_size=1,
        max_size=5,  # Supabase has connection limits, keep this low
        max_queries=50000,
        max_inactive_connection_lifetime=300.0,
        command_timeout=60,
        ssl='require'  # Force SSL for Supabase
    )

    # Register routes
    register_routes(app)

    # Setup session
    app.secret_key = config.SECRET_KEY

    # Cleanup on app shutdown
    @app.before_serving
    async def create_tables():
        async with app.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'user',
                    is_blocked BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS wallet_transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    transaction_type VARCHAR(50) NOT NULL,
                    amount DECIMAL(20, 8) NOT NULL,
                    balance_before DECIMAL(20, 8) NOT NULL,
                    balance_after DECIMAL(20, 8) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    asset VARCHAR(50) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    size DECIMAL(20, 8) NOT NULL,
                    price DECIMAL(20, 8) NOT NULL,
                    total DECIMAL(20, 8) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS withdrawals (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    amount DECIMAL(20, 8) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS copy_trading_subscriptions (
                    id SERIAL PRIMARY KEY,
                    follower_id INTEGER REFERENCES users(id),
                    trader_id VARCHAR(100) NOT NULL,
                    allocation DECIMAL(5, 2) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

    @app.after_serving
    async def cleanup():
        await app.db_pool.close()

    return app
