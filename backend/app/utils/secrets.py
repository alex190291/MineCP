"""
Automatic secret key generation and management.
"""
import os
import secrets
from pathlib import Path
from cryptography.fernet import Fernet


def generate_jwt_secret() -> str:
    """Generate a secure random JWT secret key."""
    return secrets.token_hex(32)


def generate_flask_secret() -> str:
    """Generate a secure random Flask secret key."""
    return secrets.token_hex(32)


def generate_encryption_key() -> str:
    """Generate a secure Fernet encryption key."""
    return Fernet.generate_key().decode()


def ensure_secrets_exist(env_path: Path) -> dict:
    """
    Ensure all required secrets exist in .env file.
    Generates and persists them on first launch if missing.

    Args:
        env_path: Path to .env file

    Returns:
        dict: Dictionary of all secrets (for logging purposes)
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
        'JWT_SECRET_KEY': ['your-jwt-secret-key-change-in-production', 'jwt-secret-key-change-in-production'],
        'SECRET_KEY': ['your-secret-key-change-in-production', 'dev-secret-key-change-in-production'],
        'ENCRYPTION_KEY': ['your-encryption-key-change-in-production'],
    }

    # Check JWT_SECRET_KEY
    jwt_secret = env_vars.get('JWT_SECRET_KEY', '')
    if not jwt_secret or jwt_secret in insecure_defaults['JWT_SECRET_KEY']:
        jwt_secret = generate_jwt_secret()
        env_vars['JWT_SECRET_KEY'] = jwt_secret
        generated['JWT_SECRET_KEY'] = jwt_secret
        updated = True

    # Check SECRET_KEY
    secret_key = env_vars.get('SECRET_KEY', '')
    if not secret_key or secret_key in insecure_defaults['SECRET_KEY']:
        secret_key = generate_flask_secret()
        env_vars['SECRET_KEY'] = secret_key
        generated['SECRET_KEY'] = secret_key
        updated = True

    # Check ENCRYPTION_KEY
    encryption_key = env_vars.get('ENCRYPTION_KEY', '')
    if not encryption_key or encryption_key in insecure_defaults['ENCRYPTION_KEY']:
        encryption_key = generate_encryption_key()
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

        # Add any new keys that weren't in the file
        for key in ['JWT_SECRET_KEY', 'SECRET_KEY', 'ENCRYPTION_KEY']:
            if key not in keys_updated and key in env_vars:
                new_lines.append(f"\n# Auto-generated on first launch\n")
                new_lines.append(f"{key}={env_vars[key]}\n")

        # Write to file
        env_path.parent.mkdir(parents=True, exist_ok=True)
        with open(env_path, 'w') as f:
            f.writelines(new_lines)

        # Set restrictive permissions
        os.chmod(env_path, 0o600)

    return generated


def load_or_generate_secrets(env_path: Path = None) -> dict:
    """
    Load secrets from .env or generate them if missing.

    Args:
        env_path: Path to .env file (default: backend/.env)

    Returns:
        dict: Generated secrets (empty if all existed)
    """
    if env_path is None:
        # Assume we're in the backend directory or can find it
        backend_dir = Path(__file__).parent.parent.parent
        env_path = backend_dir / '.env'

    return ensure_secrets_exist(env_path)
