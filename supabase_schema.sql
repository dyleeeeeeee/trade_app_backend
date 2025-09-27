-- Supabase Database Schema for Cookie Cash Trading Platform
-- Run this in your Supabase SQL Editor

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Wallet transactions table (updated with profit support)
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('deposit', 'withdraw', 'transfer_in', 'transfer_out', 'trade_buy', 'trade_sell', 'admin_adjustment_positive', 'admin_adjustment_negative', 'strategy_investment', 'strategy_unsubscription', 'profit_adjustment_positive', 'profit_adjustment_negative')),
    amount DECIMAL(20, 8) NOT NULL CHECK (amount > 0),
    balance_before DECIMAL(20, 8) NOT NULL,
    balance_after DECIMAL(20, 8) NOT NULL,
    profit_before DECIMAL(20, 8) DEFAULT 0,
    profit_after DECIMAL(20, 8) DEFAULT 0,
    reference_id VARCHAR(100), -- for trade_id or withdrawal_id
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    asset VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    size DECIMAL(20, 8) NOT NULL CHECK (size > 0),
    price DECIMAL(20, 8) NOT NULL CHECK (price > 0),
    total DECIMAL(20, 8) NOT NULL CHECK (total > 0),
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Withdrawals table
CREATE TABLE IF NOT EXISTS withdrawals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(20, 8) NOT NULL CHECK (amount > 0),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    admin_id INTEGER REFERENCES users(id), -- who approved/rejected
    notes TEXT
);

-- Copy trading subscriptions table
CREATE TABLE IF NOT EXISTS copy_trading_subscriptions (
    id SERIAL PRIMARY KEY,
    follower_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    trader_id VARCHAR(100) NOT NULL,
    allocation DECIMAL(5, 2) NOT NULL CHECK (allocation > 0 AND allocation <= 100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(follower_id, trader_id)
);

-- Profit tracking tables for complex P&L calculations
CREATE TABLE IF NOT EXISTS profit_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    total_profit DECIMAL(20, 8) DEFAULT 0,
    strategy_profits DECIMAL(20, 8) DEFAULT 0,
    trading_profits DECIMAL(20, 8) DEFAULT 0,
    subscription_profits DECIMAL(20, 8) DEFAULT 0,
    realized_pnl DECIMAL(20, 8) DEFAULT 0,
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0,
    daily_roi DECIMAL(10, 6) DEFAULT 0,
    sharpe_ratio DECIMAL(10, 6) DEFAULT 0,
    max_drawdown DECIMAL(10, 6) DEFAULT 0,
    volatility DECIMAL(10, 6) DEFAULT 0,
    snapshot_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(user_id, snapshot_date)
);

-- Advanced trade profit calculations
CREATE TABLE IF NOT EXISTS trade_profits (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trades(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8),
    position_size DECIMAL(20, 8) NOT NULL,
    realized_pnl DECIMAL(20, 8) DEFAULT 0,
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0,
    holding_period_hours INTEGER DEFAULT 0,
    volatility_at_entry DECIMAL(10, 6) DEFAULT 0,
    market_regime VARCHAR(20) DEFAULT 'neutral', -- bull, bear, neutral, volatile
    risk_adjusted_return DECIMAL(10, 6) DEFAULT 0,
    alpha_contribution DECIMAL(20, 8) DEFAULT 0,
    beta_exposure DECIMAL(10, 6) DEFAULT 1,
    momentum_score DECIMAL(10, 6) DEFAULT 0,
    technical_score DECIMAL(10, 6) DEFAULT 0,
    fundamental_score DECIMAL(10, 6) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Strategy performance tracking with Newton-inspired calculations
CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_subscription_id INTEGER REFERENCES strategy_subscriptions(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    invested_amount DECIMAL(20, 8) NOT NULL,
    current_value DECIMAL(20, 8) NOT NULL,
    realized_profits DECIMAL(20, 8) DEFAULT 0,
    unrealized_profits DECIMAL(20, 8) DEFAULT 0,
    total_return DECIMAL(10, 6) DEFAULT 0,
    annualized_return DECIMAL(10, 6) DEFAULT 0,
    volatility DECIMAL(10, 6) DEFAULT 0,
    sharpe_ratio DECIMAL(10, 6) DEFAULT 0,
    sortino_ratio DECIMAL(10, 6) DEFAULT 0,
    max_drawdown DECIMAL(10, 6) DEFAULT 0,
    calmar_ratio DECIMAL(10, 6) DEFAULT 0,
    omega_ratio DECIMAL(10, 6) DEFAULT 0,
    win_rate DECIMAL(5, 2) DEFAULT 0,
    profit_factor DECIMAL(10, 6) DEFAULT 1,
    expectancy DECIMAL(20, 8) DEFAULT 0,
    recovery_factor DECIMAL(10, 6) DEFAULT 0,
    ulcer_index DECIMAL(10, 6) DEFAULT 0,
    tail_ratio DECIMAL(10, 6) DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_user_id ON wallet_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_created_at ON wallet_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);
CREATE INDEX IF NOT EXISTS idx_withdrawals_user_id ON withdrawals(user_id);
CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON withdrawals(status);
CREATE INDEX IF NOT EXISTS idx_copy_trading_follower_id ON copy_trading_subscriptions(follower_id);
CREATE INDEX IF NOT EXISTS idx_copy_trading_trader_id ON copy_trading_subscriptions(trader_id);
CREATE INDEX IF NOT EXISTS idx_profit_snapshots_user_id ON profit_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_profit_snapshots_date ON profit_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_trade_profits_trade_id ON trade_profits(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_profits_user_id ON trade_profits(user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_subscription_id ON strategy_performance(strategy_subscription_id);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_user_id ON strategy_performance(user_id);

-- Insert admin user (change password in production!)
INSERT INTO users (email, password, role)
VALUES ('admin@example.com', 'admin123', 'admin')
ON CONFLICT (email) DO NOTHING;

-- Enable Row Level Security (RLS) - optional but recommended for Supabase
-- Uncomment and modify these policies based on your security requirements

-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE wallet_transactions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE withdrawals ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE copy_trading_subscriptions ENABLE ROW LEVEL SECURITY;

-- Example RLS policies (users can only access their own data)
-- CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid()::text = id::text);
-- CREATE POLICY "Users can view own transactions" ON wallet_transactions FOR SELECT USING (auth.uid() = user_id);
-- (Add more policies as needed for your security model)
