"""
Development server entry point.
"""
import sys
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet


def ensure_secrets_in_env(env_path: Path) -> dict:
    """
    Ensure all required secrets exist in .env file.
    Generates and persists them on first launch if missing.

    Returns:
        dict: Dictionary of generated secrets
    """
    env_path = Path(env_path)

    # Read existing .env file if it exists
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

    # Track what was generated
    generated = {}
    updated = False

    # Default/placeholder values that should be replaced
    insecure_defaults = {
        'JWT_SECRET_KEY': ['your-jwt-secret-key-change-in-production', 'jwt-secret-key-change-in-production', ''],
        'SECRET_KEY': ['your-secret-key-change-in-production', 'dev-secret-key-change-in-production', ''],
        'ENCRYPTION_KEY': ['your-encryption-key-change-in-production', ''],
    }

    # Check JWT_SECRET_KEY
    jwt_secret = env_vars.get('JWT_SECRET_KEY', '')
    if not jwt_secret or jwt_secret in insecure_defaults['JWT_SECRET_KEY']:
        jwt_secret = secrets.token_hex(32)
        env_vars['JWT_SECRET_KEY'] = jwt_secret
        generated['JWT_SECRET_KEY'] = jwt_secret
        updated = True

    # Check SECRET_KEY
    secret_key = env_vars.get('SECRET_KEY', '')
    if not secret_key or secret_key in insecure_defaults['SECRET_KEY']:
        secret_key = secrets.token_hex(32)
        env_vars['SECRET_KEY'] = secret_key
        generated['SECRET_KEY'] = secret_key
        updated = True

    # Check ENCRYPTION_KEY
    encryption_key = env_vars.get('ENCRYPTION_KEY', '')
    if not encryption_key or encryption_key in insecure_defaults['ENCRYPTION_KEY']:
        encryption_key = Fernet.generate_key().decode()
        env_vars['ENCRYPTION_KEY'] = encryption_key
        generated['ENCRYPTION_KEY'] = encryption_key
        updated = True

    # Write back to .env if anything was generated
    if updated:
        # Preserve comments and structure, update only the values
        new_lines = []
        keys_updated = set()

        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and '=' in stripped:
                        key = stripped.split('=', 1)[0].strip()
                        if key in env_vars:
                            new_lines.append(f"{key}={env_vars[key]}\n")
                            keys_updated.add(key)
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)

        # Write to file
        env_path.parent.mkdir(parents=True, exist_ok=True)
        with open(env_path, 'w') as f:
            f.writelines(new_lines)

        # Set restrictive permissions
        os.chmod(env_path, 0o600)

    return generated


# Ensure secrets exist (generate on first launch if needed)
env_path = Path(__file__).parent / '.env'
generated = ensure_secrets_in_env(env_path)

if generated:
    print("=" * 60)
    print("🔐 SECURITY: Auto-generated secrets on first launch")
    print("=" * 60)
    for key in generated:
        print(f"  ✓ {key}: Generated")
    print(f"\nSecrets saved to: {env_path}")
    print("⚠️  Keep this .env file secure and do not commit it to git!")
    print("=" * 60)

# Load environment variables from .env file
# THIS MUST happen before importing app
load_dotenv(dotenv_path=env_path)

# Now import the app (config.py will read the environment variables we just loaded)
from app import create_app, socketio

app = create_app('development')

if __name__ == '__main__':
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
