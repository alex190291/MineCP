#!/usr/bin/env python3
"""
Database setup script - initializes Flask-Migrate and creates tables.
"""
import os
import sys

# Check if we're in a virtual environment
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("WARNING: Not running in a virtual environment!")
    print("It's recommended to create and activate a virtual environment first:")
    print("  python3 -m venv venv")
    print("  source venv/bin/activate")
    print("")
    response = input("Continue anyway? (y/n): ")
    if response.lower() != 'y':
        sys.exit(0)

# Set Flask app environment variable
os.environ['FLASK_APP'] = 'app'

try:
    from app import create_app, db
    from flask_migrate import init, migrate, upgrade
    import subprocess

    print("Creating Flask application...")
    app = create_app('development')

    with app.app_context():
        print("\nInitializing Flask-Migrate...")
        # Check if migrations folder exists
        if not os.path.exists('migrations'):
            print("Creating migrations directory...")
            result = subprocess.run(['flask', 'db', 'init'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error initializing migrations: {result.stderr}")
                sys.exit(1)
            print("Migrations initialized successfully!")
        else:
            print("Migrations directory already exists.")

        print("\nCreating migration...")
        result = subprocess.run(['flask', 'db', 'migrate', '-m', 'Initial migration'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Warning: {result.stderr}")
        else:
            print("Migration created successfully!")

        print("\nApplying migrations...")
        result = subprocess.run(['flask', 'db', 'upgrade'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error applying migrations: {result.stderr}")
            sys.exit(1)
        print("Migrations applied successfully!")

        print("\n" + "="*50)
        print("Database setup complete!")
        print("="*50)
        print("\nYou can now start the Flask application with:")
        print("  python run.py")
        print("\nDefault admin credentials:")
        print("  Username: admin")
        print("  Password: changeme")
        print("="*50)

except ImportError as e:
    print(f"\nError: Missing dependencies - {e}")
    print("\nPlease install the required packages:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
