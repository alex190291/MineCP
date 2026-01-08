"""
Backup model for server backups.
"""
from datetime import datetime
from app.extensions import db
from app.models import generate_uuid

class Backup(db.Model):
    """Server backup model."""
    __tablename__ = 'backups'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    server_id = db.Column(db.String(36), db.ForeignKey('servers.id'), nullable=False)

    # Backup information
    name = db.Column(db.String(200), nullable=False)
    size = db.Column(db.BigInteger, nullable=False)  # bytes
    backup_path = db.Column(db.String(500), nullable=False)

    # Type and metadata
    type = db.Column(db.String(20), default='manual', nullable=False)  # manual, scheduled, auto
    compressed = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    # Relationships
    server = db.relationship('Server', back_populates='backups')

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'size': self.size,
            'backup_path': self.backup_path,
            'type': self.type,
            'compressed': self.compressed,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by
        }

    def __repr__(self):
        return f'<Backup {self.name} for {self.server_id}>'
