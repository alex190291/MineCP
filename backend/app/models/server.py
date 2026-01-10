"""
Server model for Minecraft server instances.
"""
from datetime import datetime
from app.extensions import db
from app.models import generate_uuid
from flask import current_app

class Server(db.Model):
    """Minecraft server model."""
    __tablename__ = 'servers'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(100), nullable=False)

    # Server type and version
    type = db.Column(db.String(20), nullable=False)  # vanilla, paper, forge, fabric, etc.
    version = db.Column(db.String(20), nullable=False)  # e.g., "1.20.4"

    # Status
    status = db.Column(db.String(20), default='stopped', nullable=False)
    # Statuses: stopped, starting, running, stopping, error

    # Docker container info
    container_id = db.Column(db.String(64), unique=True, nullable=True)
    container_name = db.Column(db.String(100), unique=True, nullable=False)

    # Network configuration
    host_port = db.Column(db.Integer, unique=True, nullable=False)
    rcon_port = db.Column(db.Integer, unique=True, nullable=True)
    _rcon_password = db.Column('rcon_password', db.String(512), nullable=True)  # Encrypted

    # Resource limits
    memory_limit = db.Column(db.Integer, nullable=False)  # MB
    cpu_limit = db.Column(db.Float, nullable=False)  # cores
    disk_limit = db.Column(db.Integer, nullable=True)  # GB (optional)

    # Java configuration
    java_args = db.Column(db.Text, nullable=True)

    # Server properties (JSON)
    server_properties = db.Column(db.JSON, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Foreign keys
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # Relationships
    creator = db.relationship('User', back_populates='servers')
    mods = db.relationship('ServerMod', back_populates='server', cascade='all, delete-orphan')
    backups = db.relationship('Backup', back_populates='server', cascade='all, delete-orphan')
    players = db.relationship('Player', back_populates='server', cascade='all, delete-orphan')

    @property
    def rcon_password(self):
        """Decrypt and return RCON password."""
        if not self._rcon_password:
            return None

        # Check if password is already plaintext (for migration compatibility)
        # Encrypted values will be longer and contain base64 characters
        if len(self._rcon_password) < 100 and '=' not in self._rcon_password[-10:]:
            # Likely plaintext, return as-is (will be encrypted on next save)
            return self._rcon_password

        try:
            from app.utils.encryption import decrypt_value
            return decrypt_value(self._rcon_password)
        except Exception as e:
            current_app.logger.error(f"Failed to decrypt RCON password for server {self.id}: {e}")
            # Return None on decryption failure to avoid exposing corrupted data
            return None

    @rcon_password.setter
    def rcon_password(self, plaintext):
        """Encrypt and store RCON password."""
        if not plaintext:
            self._rcon_password = None
            return

        try:
            from app.utils.encryption import encrypt_value
            self._rcon_password = encrypt_value(plaintext)
        except Exception as e:
            current_app.logger.error(f"Failed to encrypt RCON password: {e}")
            # Fall back to plaintext if encryption fails (better than losing data)
            self._rcon_password = plaintext

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'version': self.version,
            'status': self.status,
            'container_id': self.container_id,
            'container_name': self.container_name,
            'host_port': self.host_port,
            'memory_limit': self.memory_limit,
            'cpu_limit': self.cpu_limit,
            'disk_limit': self.disk_limit,
            'java_args': self.java_args,
            'server_properties': self.server_properties,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by
        }

    def __repr__(self):
        return f'<Server {self.name} ({self.type} {self.version})>'
