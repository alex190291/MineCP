"""
Application configuration classes.
"""
import os
import sys
from datetime import timedelta
from pathlib import Path
import secrets
from cryptography.fernet import Fernet

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / 'data'
LOGS_DIR = BASE_DIR / 'logs'


def _read_secret_file(file_path: Path) -> str | None:
    try:
        if not file_path.exists():
            return None
        value = file_path.read_text().strip()
        return value or None
    except OSError:
        return None


def _write_secret_file(file_path: Path, value: str) -> bool:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, 'w') as handle:
        handle.write(value)
    return True


def get_or_generate_secret_key() -> str:
    """Get SECRET_KEY from env or persistently generate a strong random one."""
    key = os.getenv('SECRET_KEY')
    if key and key != 'dev-secret-key-change-in-production':
        return key

    secret_path = DATA_DIR / 'flask_secret'
    persisted = _read_secret_file(secret_path)
    if persisted:
        return persisted

    generated = secrets.token_hex(32)
    if not _write_secret_file(secret_path, generated):
        persisted = _read_secret_file(secret_path)
        if persisted:
            return persisted
    print("WARNING: SECRET_KEY not set in environment. Using auto-generated secure random key.", file=sys.stderr)
    print("For production, set SECRET_KEY environment variable to persist across restarts.", file=sys.stderr)
    return generated


def get_or_generate_jwt_secret() -> str:
    """Get JWT_SECRET_KEY from env or persistently generate a strong random one."""
    key = os.getenv('JWT_SECRET_KEY')
    if key and key != 'jwt-secret-key-change-in-production':
        return key

    secret_path = DATA_DIR / 'jwt_secret'
    persisted = _read_secret_file(secret_path)
    if persisted:
        return persisted

    generated = secrets.token_hex(32)
    if not _write_secret_file(secret_path, generated):
        persisted = _read_secret_file(secret_path)
        if persisted:
            return persisted
    print("WARNING: JWT_SECRET_KEY not set in environment. Using auto-generated secure random key.", file=sys.stderr)
    print("For production, set JWT_SECRET_KEY environment variable to persist across restarts.", file=sys.stderr)
    return generated


def get_or_generate_encryption_key() -> str:
    """Get ENCRYPTION_KEY from env or persistently generate a strong random one."""
    key = os.getenv('ENCRYPTION_KEY')
    if key:
        return key

    secret_path = DATA_DIR / 'encryption_key'
    persisted = _read_secret_file(secret_path)
    if persisted:
        return persisted

    generated = Fernet.generate_key().decode()
    if not _write_secret_file(secret_path, generated):
        persisted = _read_secret_file(secret_path)
        if persisted:
            return persisted
    print("WARNING: ENCRYPTION_KEY not set in environment. Using auto-generated secure random key.", file=sys.stderr)
    print("For production, set ENCRYPTION_KEY environment variable to persist across restarts.", file=sys.stderr)
    return generated

class Config:
    """Base configuration."""

    # Application
    APP_NAME = os.getenv('APP_NAME', 'Minecraft Server Manager')

    # Flask
    SECRET_KEY = get_or_generate_secret_key()

    # Encryption for sensitive data (RCON passwords, LDAP bind passwords)
    ENCRYPTION_KEY = get_or_generate_encryption_key()

    # Redis (optional - for token blacklist, falls back to in-memory)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{DATA_DIR}/mc_manager.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # JWT
    JWT_SECRET_KEY = get_or_generate_jwt_secret()
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800)))
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

    # File Upload
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 524288000))
    UPLOAD_FOLDER = Path(os.getenv('UPLOAD_FOLDER', str(DATA_DIR / 'uploads')))
    ALLOWED_EXTENSIONS = {'.jar', '.zip', '.mrpack'}

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = Path(os.getenv('LOG_FILE', str(LOGS_DIR / 'app.log')))

    # Docker
    DOCKER_SOCKET = os.getenv('DOCKER_SOCKET', 'unix://var/run/docker.sock')
    MC_SERVER_NETWORK = os.getenv('MC_SERVER_NETWORK', 'minecraft-network')
    MC_SERVER_DATA_DIR = DATA_DIR / 'servers'
    MC_BACKUP_DIR = DATA_DIR / 'backups'

    # Default Admin
    DEFAULT_ADMIN_USERNAME = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', 'changeme')
    DEFAULT_ADMIN_EMAIL = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@localhost')
    BOOTSTRAP_USERNAME = os.getenv('BOOTSTRAP_USERNAME', 'setup')
    BOOTSTRAP_PASSWORD = os.getenv('BOOTSTRAP_PASSWORD', 'changeme')
    BOOTSTRAP_EMAIL = os.getenv('BOOTSTRAP_EMAIL', 'setup@localhost')

    # SocketIO
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS
    SOCKETIO_ASYNC_MODE = os.getenv('SOCKETIO_ASYNC_MODE', 'eventlet')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
