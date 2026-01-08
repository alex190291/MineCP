"""
Player model for tracking Minecraft players.
"""
from datetime import datetime
from app.extensions import db
from app.models import generate_uuid

class Player(db.Model):
    """Minecraft player model."""
    __tablename__ = 'players'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    minecraft_uuid = db.Column(db.String(36), unique=True, nullable=True, index=True)
    username = db.Column(db.String(16), nullable=False)
    server_id = db.Column(db.String(36), db.ForeignKey('servers.id'), nullable=False)

    # Ban information
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    ban_reason = db.Column(db.Text, nullable=True)
    banned_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    banned_at = db.Column(db.DateTime, nullable=True)

    # Activity
    first_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    server = db.relationship('Server', back_populates='players')

    def to_dict(self):
        return {
            'id': self.id,
            'minecraft_uuid': self.minecraft_uuid,
            'username': self.username,
            'server_id': self.server_id,
            'is_banned': self.is_banned,
            'ban_reason': self.ban_reason,
            'banned_by': self.banned_by,
            'banned_at': self.banned_at.isoformat() if self.banned_at else None,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }

    def __repr__(self):
        return f'<Player {self.username}>'
