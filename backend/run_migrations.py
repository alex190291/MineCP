#!/usr/bin/env python3
"""
Database migration runner for MineCP.
Checks for and applies pending SQL and Python migrations.
"""
import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "mc_manager.db"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_db_connection():
    """Get a connection to the SQLite database."""
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Please ensure the database is initialized before running migrations.")
        sys.exit(1)

    return sqlite3.connect(DB_PATH)


def ensure_migrations_table(conn):
    """Create the migrations tracking table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations_applied (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def get_applied_migrations(conn):
    """Get the set of already-applied migrations."""
    cursor = conn.cursor()
    cursor.execute("SELECT migration_name FROM migrations_applied")
    return {row[0] for row in cursor.fetchall()}


def get_available_migrations():
    """Get all migration files from the migrations directory."""
    if not MIGRATIONS_DIR.exists():
        print(f"WARNING: Migrations directory not found: {MIGRATIONS_DIR}")
        return []

    migrations = []
    for file in sorted(MIGRATIONS_DIR.iterdir()):
        if file.suffix in ['.sql', '.py'] and not file.name.startswith('_'):
            migrations.append(file.name)

    return sorted(migrations)


def apply_sql_migration(conn, migration_file):
    """Apply a SQL migration file."""
    print(f"  Applying SQL migration: {migration_file.name}")

    with open(migration_file, 'r') as f:
        sql_content = f.read()

    # Split by semicolon and execute each statement
    # Skip the final SELECT verification statements if present
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

    cursor = conn.cursor()
    for stmt in statements:
        # Skip SELECT statements (these are often verification queries)
        if stmt.upper().startswith('SELECT'):
            print(f"    Skipping verification query")
            continue

        try:
            cursor.execute(stmt)
        except sqlite3.OperationalError as e:
            # Check if it's a "duplicate column" error (migration already partially applied)
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"    Warning: {e} (may already be applied)")
            else:
                raise

    conn.commit()


def apply_python_migration(migration_file):
    """Apply a Python migration script."""
    print(f"  Applying Python migration: {migration_file.name}")

    # Add the backend directory to sys.path so the script can import app modules
    backend_dir = str(Path(__file__).parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Execute the Python migration script
    with open(migration_file, 'r') as f:
        migration_code = f.read()

    # Create a namespace for the migration
    migration_globals = {
        '__file__': str(migration_file),
        '__name__': '__main__',
    }

    try:
        exec(migration_code, migration_globals)
    except Exception as e:
        print(f"    ERROR: Failed to execute Python migration: {e}")
        raise


def mark_migration_applied(conn, migration_name):
    """Mark a migration as applied in the tracking table."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO migrations_applied (migration_name, applied_at) VALUES (?, ?)",
        (migration_name, datetime.now().isoformat())
    )
    conn.commit()


def run_migrations():
    """Main migration runner."""
    print("=" * 60)
    print("MineCP Database Migration Runner")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Migrations directory: {MIGRATIONS_DIR}")
    print()

    # Connect to database
    conn = get_db_connection()

    try:
        # Ensure migrations tracking table exists
        ensure_migrations_table(conn)

        # Get applied and available migrations
        applied = get_applied_migrations(conn)
        available = get_available_migrations()

        if not available:
            print("No migration files found.")
            return 0

        # Find pending migrations
        pending = [m for m in available if m not in applied]

        if not pending:
            print(f"✓ All migrations up to date ({len(applied)} applied)")
            return 0

        print(f"Found {len(pending)} pending migration(s):")
        for migration in pending:
            print(f"  - {migration}")
        print()

        # Apply pending migrations
        for migration_name in pending:
            migration_file = MIGRATIONS_DIR / migration_name

            print(f"Applying migration: {migration_name}")

            try:
                if migration_file.suffix == '.sql':
                    apply_sql_migration(conn, migration_file)
                elif migration_file.suffix == '.py':
                    apply_python_migration(migration_file)

                # Mark as applied
                mark_migration_applied(conn, migration_name)
                print(f"  ✓ Migration applied successfully")

            except Exception as e:
                print(f"  ✗ ERROR applying migration: {e}")
                print(f"\nMigration failed: {migration_name}")
                print("Please fix the issue and run migrations again.")
                conn.rollback()
                return 1

            print()

        print("=" * 60)
        print(f"✓ Successfully applied {len(pending)} migration(s)")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(run_migrations())
