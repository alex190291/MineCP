-- Migration: Add ldap_groups column for LDAP group caching
-- Date: 2026-01-12
-- Description: Adds ldap_groups JSON text column to users table
-- Compatible with SQLite

ALTER TABLE users ADD COLUMN ldap_groups TEXT;
