-- Migration: Unify role system
-- This migration converts the user.role string field to user.role_id foreign key
-- Run this AFTER running the seed_permissions_and_roles() function to create default roles

-- Step 1: Add role_id column (nullable initially)
-- Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
-- This migration assumes migrate_user_roles.py has already added the column
-- ALTER TABLE users ADD COLUMN role_id VARCHAR(36);

-- Step 2: Add foreign key constraint
-- Note: SQLite requires recreating the table to add foreign key constraints
-- This is handled by the SQLAlchemy models, so we skip this step
-- ALTER TABLE users ADD CONSTRAINT fk_users_role_id
--   FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL;

-- Step 3: Migrate existing data
-- Map 'admin' string role to admin role_id
UPDATE users
SET role_id = (SELECT id FROM roles WHERE name = 'admin' LIMIT 1)
WHERE role = 'admin' AND role_id IS NULL;

-- Map all other users to 'viewer' role_id (default role for regular users)
UPDATE users
SET role_id = (SELECT id FROM roles WHERE name = 'viewer' LIMIT 1)
WHERE role_id IS NULL AND role != 'bootstrap';

-- Step 4: (Optional) Remove old role column after verifying migration
-- ONLY run this after confirming all users have been migrated correctly!
-- You can check with: SELECT id, username, role, role_id FROM users;
--
-- ALTER TABLE users DROP COLUMN role;

-- Step 5: Verify migration
SELECT
  u.id,
  u.username,
  u.role as old_role_field,
  u.role_id,
  r.name as new_role_name
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
ORDER BY u.username;
