import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_database():
    """
    Setup database tables and initial data for Supabase.

    Note: For Supabase, you may need to create tables through the SQL Editor
    in the Supabase dashboard instead of programmatically due to RLS policies.
    """

    # Connect to database
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Try to construct from individual components
        db_host = os.getenv('SUPABASE_DB_HOST')
        db_port = os.getenv('SUPABASE_DB_PORT', '6543')
        db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
        db_user = os.getenv('SUPABASE_DB_USER')
        db_password = os.getenv('SUPABASE_DB_PASSWORD')

        if db_host and db_user and db_password:
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"

    if not database_url:
        print("❌ No DATABASE_URL found. Please set up your Supabase database connection in .env")
        return

    try:
        conn = await asyncpg.connect(database_url)

        print("✅ Connected to Supabase database")

        # Try to create tables (this may fail due to Supabase RLS/policies)
        try:
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
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"⚠️  Table creation may have failed: {str(e)}")
            print("💡 You may need to create tables manually in Supabase SQL Editor")
            print("   Run the SQL commands from supabase_schema.sql in your Supabase dashboard")

        # Try to create admin user
        try:
            admin_exists = await conn.fetchval('SELECT id FROM users WHERE email = $1', 'admin@example.com')
            if not admin_exists:
                await conn.execute('''
                    INSERT INTO users (email, password, role)
                    VALUES ($1, $2, $3)
                ''', 'admin@example.com', 'admin123', 'admin')
                print("✅ Admin user created: admin@example.com / admin123")
            else:
                print("✅ Admin user already exists")
        except Exception as e:
            print(f"⚠️  Admin user creation may have failed: {str(e)}")
            print("💡 You may need to create the admin user manually in Supabase")

        print("\n🎉 Database setup complete!")
        print("\n📋 Next steps:")
        print("1. If tables weren't created, run the SQL in supabase_schema.sql manually")
        print("2. Configure Row Level Security (RLS) policies in Supabase dashboard if needed")
        print("3. Test the connection by running: python run.py")

    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        print("💡 Check your Supabase connection settings and try again")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == '__main__':
    asyncio.run(setup_database())
