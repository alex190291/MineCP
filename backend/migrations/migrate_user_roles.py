"""
Migration script to convert user roles from string to role_id.
Run this once to migrate existing users to the new role system.
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.role import Role
from sqlalchemy import text


def migrate_user_roles():
    """Migrate users from string role to role_id foreign key."""
    app = create_app()

    with app.app_context():
        # First, add role_id column if it doesn't exist
        try:
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN role_id VARCHAR(36)"
            ))
            db.session.commit()
            print("Added role_id column to users table")
        except Exception as e:
            print(f"role_id column may already exist: {e}")
            db.session.rollback()

        # Get or create default roles
        admin_role = Role.query.filter_by(name='admin').first()
        viewer_role = Role.query.filter_by(name='viewer').first()

        if not admin_role or not viewer_role:
            print("ERROR: Default roles not found. Run seed_permissions_and_roles() first.")
            print("You can do this by starting the app or running:")
            print("  python -c 'from app import create_app; from app.utils.permissions import seed_permissions_and_roles; app = create_app(); app.app_context().push(); seed_permissions_and_roles()'")
            return

        # Migrate users - read old role column if it exists
        try:
            users = db.session.execute(text("SELECT id, role FROM users WHERE role_id IS NULL")).fetchall()

            for user_row in users:
                user_id, old_role = user_row

                # Map old string role to new role_id
                if old_role == 'admin':
                    new_role_id = admin_role.id
                else:
                    new_role_id = viewer_role.id  # Default to viewer for non-admin users

                db.session.execute(
                    text("UPDATE users SET role_id = :role_id WHERE id = :user_id"),
                    {"role_id": new_role_id, "user_id": user_id}
                )
                print(f"Migrated user {user_id}: '{old_role}' -> role_id={new_role_id}")

            db.session.commit()
            print(f"Successfully migrated {len(users)} users")

            # Drop old role column (optional - comment out if you want to keep it for rollback)
            # print("\nNOTE: The old 'role' column is still present. You can remove it manually if desired:")
            # print("  ALTER TABLE users DROP COLUMN role;")

        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            raise


if __name__ == '__main__':
    migrate_user_roles()
