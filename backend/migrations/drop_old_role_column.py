"""
Drop the old 'role' column from users table.
This migration is safe to run after all users have been migrated to role_id.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text


def drop_old_role_column():
    """Remove the old 'role' column from users table."""
    app = create_app()

    with app.app_context():
        print("Starting migration to drop old 'role' column...")

        # Check if old column exists
        result = db.session.execute(text("PRAGMA table_info(users)")).fetchall()
        columns = [row[1] for row in result]

        if 'role' not in columns:
            print("Old 'role' column doesn't exist. Migration not needed.")
            return

        print("Old 'role' column found. Recreating table without it...")

        # SQLite requires recreating the table to drop a column
        # Drop indexes first
        migration_sql = """
        -- Drop existing indexes
        DROP INDEX IF EXISTS ix_users_username;
        DROP INDEX IF EXISTS ix_users_email;
        DROP INDEX IF EXISTS idx_users_totp_enabled;

        -- Create new table without the old 'role' column
        CREATE TABLE users_new (
            id VARCHAR(36) NOT NULL,
            username VARCHAR(80) NOT NULL,
            email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(255),
            is_ldap_user BOOLEAN NOT NULL,
            ldap_dn VARCHAR(255),
            ldap_groups TEXT,
            role_id VARCHAR(36),
            is_active BOOLEAN NOT NULL,
            totp_secret VARCHAR(32),
            totp_enabled BOOLEAN NOT NULL DEFAULT 0,
            backup_codes TEXT,
            created_at DATETIME NOT NULL,
            last_login DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(role_id) REFERENCES roles (id)
        );

        -- Copy data from old table (excluding 'role' column)
        INSERT INTO users_new (
            id, username, email, password_hash, is_ldap_user, ldap_dn,
            ldap_groups, role_id, is_active, totp_secret, totp_enabled,
            backup_codes, created_at, last_login
        )
        SELECT
            id, username, email, password_hash, is_ldap_user, ldap_dn,
            ldap_groups, role_id, is_active, totp_secret, totp_enabled,
            backup_codes, created_at, last_login
        FROM users;

        -- Drop old table
        DROP TABLE users;

        -- Rename new table
        ALTER TABLE users_new RENAME TO users;

        -- Recreate indexes
        CREATE UNIQUE INDEX ix_users_username ON users (username);
        CREATE UNIQUE INDEX ix_users_email ON users (email);
        CREATE INDEX idx_users_totp_enabled ON users(totp_enabled);
        """

        try:
            # Execute migration in parts
            for statement in migration_sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    db.session.execute(text(statement))

            db.session.commit()
            print("✓ Successfully dropped old 'role' column")

            # Verify
            result = db.session.execute(text("PRAGMA table_info(users)")).fetchall()
            new_columns = [row[1] for row in result]
            print(f"✓ New users table columns: {new_columns}")

            # Verify data integrity
            user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            print(f"✓ Users in table: {user_count}")

        except Exception as e:
            print(f"✗ Error during migration: {e}")
            db.session.rollback()
            raise


if __name__ == '__main__':
    drop_old_role_column()
