-- Migration: Add 2FA fields to users table
-- Date: 2026-01-10
-- Description: Adds TOTP secret, enabled flag, and backup codes for two-factor authentication
-- Compatible with SQLite

-- Add totp_secret column (Base32 encoded secret)
ALTER TABLE users ADD COLUMN totp_secret VARCHAR(32);

-- Add totp_enabled column (Boolean flag)
ALTER TABLE users ADD COLUMN totp_enabled BOOLEAN NOT NULL DEFAULT 0;

-- Add backup_codes column (JSON array of hashed backup codes)
ALTER TABLE users ADD COLUMN backup_codes TEXT;

-- Create index on totp_enabled for faster queries
CREATE INDEX IF NOT EXISTS idx_users_totp_enabled ON users(totp_enabled);
