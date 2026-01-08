#!/usr/bin/env python3
"""
Validation script to check if the backend setup is correct.
This script checks for syntax errors and basic structure without requiring installed dependencies.
"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} - NOT FOUND")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists."""
    if Path(dirpath).is_dir():
        print(f"✓ {description}: {dirpath}")
        return True
    else:
        print(f"✗ {description}: {dirpath} - NOT FOUND")
        return False

def check_python_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        return True
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
        return False

def main():
    """Run validation checks."""
    print("="*60)
    print("Backend Setup Validation")
    print("="*60)
    print()

    errors = []

    # Check directory structure
    print("Checking directory structure...")
    directories = [
        ('app', 'Application directory'),
        ('app/api', 'API blueprints directory'),
        ('app/models', 'Models directory'),
        ('app/services', 'Services directory'),
        ('app/background', 'Background tasks directory'),
        ('app/schemas', 'Schemas directory'),
        ('app/utils', 'Utils directory'),
        ('app/websockets', 'WebSockets directory'),
        ('migrations', 'Migrations directory'),
        ('tests', 'Tests directory'),
        ('logs', 'Logs directory'),
    ]

    for dirpath, description in directories:
        if not check_directory_exists(dirpath, description):
            errors.append(f"Missing directory: {dirpath}")
    print()

    # Check configuration files
    print("Checking configuration files...")
    config_files = [
        ('requirements.txt', 'Requirements file'),
        ('.env', 'Environment file'),
        ('.env.example', 'Example environment file'),
        ('.gitignore', 'Git ignore file'),
        ('run.py', 'Development server entry point'),
        ('wsgi.py', 'Production WSGI entry point'),
    ]

    for filepath, description in config_files:
        if not check_file_exists(filepath, description):
            errors.append(f"Missing file: {filepath}")
    print()

    # Check core Python files
    print("Checking core Python files...")
    core_files = [
        ('app/__init__.py', 'App factory'),
        ('app/config.py', 'Configuration'),
        ('app/extensions.py', 'Extensions'),
    ]

    for filepath, description in core_files:
        if check_file_exists(filepath, description):
            if not check_python_syntax(filepath):
                errors.append(f"Syntax error in: {filepath}")
    print()

    # Check API blueprints
    print("Checking API blueprints...")
    api_files = [
        ('app/api/__init__.py', 'API init'),
        ('app/api/auth.py', 'Auth API'),
        ('app/api/servers.py', 'Servers API'),
        ('app/api/monitoring.py', 'Monitoring API'),
        ('app/api/mods.py', 'Mods API'),
        ('app/api/backups.py', 'Backups API'),
        ('app/api/users.py', 'Users API'),
        ('app/api/ldap_config.py', 'LDAP Config API'),
    ]

    for filepath, description in api_files:
        if check_file_exists(filepath, description):
            if not check_python_syntax(filepath):
                errors.append(f"Syntax error in: {filepath}")
    print()

    # Check models
    print("Checking database models...")
    model_files = [
        ('app/models/__init__.py', 'Models init'),
        ('app/models/user.py', 'User model'),
        ('app/models/server.py', 'Server model'),
        ('app/models/server_mod.py', 'ServerMod model'),
        ('app/models/backup.py', 'Backup model'),
        ('app/models/player.py', 'Player model'),
        ('app/models/audit_log.py', 'AuditLog model'),
        ('app/models/ldap_config.py', 'LDAPConfig model'),
    ]

    for filepath, description in model_files:
        if check_file_exists(filepath, description):
            if not check_python_syntax(filepath):
                errors.append(f"Syntax error in: {filepath}")
    print()

    # Summary
    print("="*60)
    if errors:
        print(f"Validation FAILED with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        print("="*60)
        return 1
    else:
        print("✓ All validation checks passed!")
        print()
        print("Next steps:")
        print("  1. Create virtual environment: python3 -m venv venv")
        print("  2. Activate it: source venv/bin/activate")
        print("  3. Install dependencies: pip install -r requirements.txt")
        print("  4. Initialize database: python3 setup_db.py")
        print("  5. Run server: python run.py")
        print("="*60)
        return 0

if __name__ == '__main__':
    sys.exit(main())
