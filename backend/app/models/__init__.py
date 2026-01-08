"""
Database models.
"""
import uuid
from datetime import datetime
from app.extensions import db

def generate_uuid():
    """Generate UUID4 as string."""
    return str(uuid.uuid4())

# Import all models for Alembic
from app.models.user import User
from app.models.server import Server
from app.models.server_mod import ServerMod
from app.models.backup import Backup
from app.models.player import Player
from app.models.audit_log import AuditLog
from app.models.ldap_config import LDAPConfig

__all__ = [
    'User',
    'Server',
    'ServerMod',
    'Backup',
    'Player',
    'AuditLog',
    'LDAPConfig'
]
