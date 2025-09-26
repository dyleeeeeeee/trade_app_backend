# Cookie Cash Trading Platform Backend

A simple Python backend for a trading platform using Quart and asyncpg.

## Features

- User authentication with httpOnly cookies (no JWT)
- Wallet management (deposit, withdraw, transfer)
- Trading functionality (buy/sell assets)
- Copy trading subscriptions
- Admin panel for user management and withdrawal approvals
- PostgreSQL database with asyncpg
- **Email notifications** for important events

## Email Notifications

The backend automatically sends email notifications for:

- **Welcome Email**: Sent after successful account registration
- **Login Notifications**: Sent after each successful login
- **Withdrawal Requests**: Sent when user requests a withdrawal
- **Withdrawal Approvals**: Sent when admin approves a withdrawal
- **Trade Executions**: Sent when a trade order is executed
- **Password Reset**: Sent when user requests password reset (if implemented)

### Email Configuration

To enable email notifications:

1. Configure SMTP settings in `.env` file
2. For Gmail, use an "App Password" instead of your regular password
3. Enable "Less secure app access" or use OAuth2 for production

Example Gmail setup:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
```

## Supabase Setup (Recommended)

This backend is optimized for Supabase PostgreSQL. Follow these steps:

### 1. Create a Supabase Project
1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the database to be set up

### 2. Get Your Connection Details
In your Supabase dashboard:
1. Go to Settings → Database
2. Copy the connection details (host, port, user, password, database name)
3. Use the **Pooled connection** for better performance

### 3. Configure Environment Variables
Update your `.env` file with Supabase connection details:

```bash
# Option 1: Use full DATABASE_URL (recommended)
DATABASE_URL=postgresql://postgres.[your-project-ref]:[your-password]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require

# Option 2: Use individual components
SUPABASE_DB_HOST=aws-0-[region].pooler.supabase.com
SUPABASE_DB_PORT=6543
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.[your-project-ref]
SUPABASE_DB_PASSWORD=your-password
```

### 4. Create Database Tables
Run the SQL schema in your Supabase dashboard:

1. Go to **SQL Editor** in your Supabase dashboard
2. Copy and paste the contents of `supabase_schema.sql`
3. Click **Run** to create all tables and initial data

### 5. Run Setup Script
```bash
python setup_db.py
```

This will verify the connection and create any missing data.

## Traditional PostgreSQL Setup

If you prefer to use a traditional PostgreSQL instance instead of Supabase:

### 1. Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS with Homebrew
brew install postgresql

# Or use Docker
docker run --name postgres -e POSTGRES_PASSWORD=mypassword -d -p 5432:5432 postgres
```

### 2. Configure Environment
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/trading_platform
```

### 3. Run Setup
```bash
python setup_db.py
```

## Running the Application

After setup is complete:

```bash
python run.py
```

The application will start on `http://localhost:5000`.

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /signup` - User registration
- `POST /logout` - User logout
- `GET /user` - Get current user info
- `POST /forgot-password` - Password reset request

### Wallet
- `GET /wallet` - Get wallet balance
- `POST /deposit` - Deposit funds
- `POST /withdraw` - Request withdrawal
- `POST /transfer` - Transfer funds to another user
- `GET /withdrawals` - Get user's withdrawal history

### Trading
- `POST /trade` - Place a trade order
- `GET /trades` - Get user's trade history
- `POST /copy/subscribe` - Subscribe to copy trader
- `GET /copy/subscriptions` - Get user's subscriptions

### Admin
- `GET /admin/users` - Get all users
- `POST /admin/users/{user_id}/block` - Block/unblock user
- `GET /admin/withdrawals` - Get all withdrawals
- `POST /admin/withdrawals/{id}/approve` - Approve withdrawal

## Database Schema

### For Supabase
Use the `supabase_schema.sql` file in your Supabase SQL Editor to create tables.

### For Traditional PostgreSQL
The application automatically creates the following tables on startup:

- `users` - User accounts
- `wallet_transactions` - Wallet transaction history
- `trades` - Trade records
- `withdrawals` - Withdrawal requests
- `copy_trading_subscriptions` - Copy trading subscriptions

## Notes

- Passwords are stored in plain text (as requested - not recommended for production)
- Uses httpOnly cookies for session management
- All wallet operations are tracked in transaction history
- Balance is calculated from transaction history
- Admin role is required for admin endpoints
