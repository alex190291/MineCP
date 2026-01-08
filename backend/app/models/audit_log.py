"""
AuditLog model for tracking user actions.
"""
from datetime import datetime
from app.extensions import db
from app.models import generate_uuid

class AuditLog(db.Model):
    """Audit log model."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # Action details
    action = db.Column(db.String(100), nullable=False)  # e.g., 'server.create', 'player.ban'
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(36), nullable=True)

    # Additional details (JSON)
    details = db.Column(db.JSON, nullable=True)

    # Request metadata
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 can be up to 45 chars

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = db.relationship('User', back_populates='audit_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id}>'
