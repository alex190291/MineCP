"""
User model for authentication and authorization.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import generate_uuid

class User(db.Model):
    """User model."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for LDAP users

    # LDAP fields
    is_ldap_user = db.Column(db.Boolean, default=False, nullable=False)
    ldap_dn = db.Column(db.String(255), nullable=True)
    ldap_groups = db.Column(db.Text, nullable=True)  # JSON list of LDAP group DNs/names

    # Role and status
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=True)  # User's global role
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationship to role
    global_role = db.relationship('Role', foreign_keys=[role_id])

    # Two-Factor Authentication
    totp_secret = db.Column(db.String(32), nullable=True)  # Base32 encoded secret
    totp_enabled = db.Column(db.Boolean, default=False, nullable=False)
    backup_codes = db.Column(db.Text, nullable=True)  # JSON array of hashed backup codes

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    servers = db.relationship('Server', back_populates='creator', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash."""
        if self.is_ldap_user:
            return False  # LDAP users authenticate via LDAP
        return check_password_hash(self.password_hash, password)

    @property
    def role(self):
        """Backward compatibility property for role name."""
        if self.global_role:
            return self.global_role.name
        return 'user'  # Default fallback

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,  # Uses the property above
            'role_id': self.role_id,
            'is_ldap_user': self.is_ldap_user,
            'is_active': self.is_active,
            'totp_enabled': self.totp_enabled,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f'<User {self.username}>'
