"""
LDAPConfig model for LDAP configuration.
"""
from datetime import datetime
from app.extensions import db

class LDAPConfig(db.Model):
    """LDAP configuration model (singleton)."""
    __tablename__ = 'ldap_config'

    id = db.Column(db.Integer, primary_key=True)  # Always 1

    # LDAP settings
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    server_uri = db.Column(db.String(255), nullable=True)
    bind_dn = db.Column(db.String(255), nullable=True)
    bind_password = db.Column(db.String(255), nullable=True)  # Should be encrypted

    # Search configuration
    user_search_base = db.Column(db.String(255), nullable=True)
    user_search_filter = db.Column(db.String(255), nullable=True)
    group_search_base = db.Column(db.String(255), nullable=True)
    group_search_filter = db.Column(db.String(255), nullable=True)

    # Role mapping
    admin_group_name = db.Column(db.String(255), nullable=True, default='admin')

    # Metadata
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'enabled': self.enabled,
            'server_uri': self.server_uri,
            'bind_dn': self.bind_dn,
            'user_search_base': self.user_search_base,
            'user_search_filter': self.user_search_filter,
            'group_search_base': self.group_search_base,
            'group_search_filter': self.group_search_filter,
            'admin_group_name': self.admin_group_name,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<LDAPConfig enabled={self.enabled}>'
