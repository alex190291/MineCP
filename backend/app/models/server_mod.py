"""
ServerMod model for tracking mods installed on servers.
"""
import os
from datetime import datetime
from app.extensions import db
from app.models import generate_uuid

class ServerMod(db.Model):
    """Server mod/plugin model."""
    __tablename__ = 'server_mods'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    server_id = db.Column(db.String(36), db.ForeignKey('servers.id'), nullable=False)

    # Mod information
    name = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(20), nullable=False)  # upload, modrinth, curseforge, spigotmc
    source_id = db.Column(db.String(100), nullable=True)  # External ID
    version = db.Column(db.String(50), nullable=True)

    # File information
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)

    # Status
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    installed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    server = db.relationship('Server', back_populates='mods')

    def to_dict(self):
        # Calculate file size if file exists
        file_size = 0
        try:
            if self.file_path and os.path.exists(self.file_path):
                file_size = os.path.getsize(self.file_path)
        except (OSError, IOError):
            file_size = 0

        mod_type = 'mod'
        file_path = self.file_path or ''
        if self.source == 'spigotmc':
            mod_type = 'plugin'
        elif '/plugins/' in file_path.replace('\\', '/'):
            mod_type = 'plugin'

        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'source': self.source,
            'source_id': self.source_id,
            'version': self.version,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': file_size,
            'content_type': mod_type,
            'enabled': self.enabled,
            'created_at': self.installed_at.isoformat()
        }

    def __repr__(self):
        return f'<ServerMod {self.name} on {self.server_id}>'
