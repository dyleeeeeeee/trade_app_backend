-- Database migration to add missing profit_after column
-- Run this in your database to fix the schema

-- Add profit_before and profit_after columns to wallet_transactions table if they don't exist
ALTER TABLE wallet_transactions
ADD COLUMN IF NOT EXISTS profit_before DECIMAL(20, 8) DEFAULT 0,
ADD COLUMN IF NOT EXISTS profit_after DECIMAL(20, 8) DEFAULT 0;

-- Update existing records to have proper profit values (set to 0 if null)
UPDATE wallet_transactions
SET profit_before = COALESCE(profit_before, 0),
    profit_after = COALESCE(profit_after, 0)
WHERE profit_before IS NULL OR profit_after IS NULL;
