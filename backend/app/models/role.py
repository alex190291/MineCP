"""
Role and permission models for server access control.
"""
from datetime import datetime
from app.extensions import db
from app.models import generate_uuid


class Role(db.Model):
    """Role definition with a set of permissions."""
    __tablename__ = 'roles'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_system = db.Column(db.Boolean, default=False, nullable=False)

    permissions = db.relationship(
        'Permission',
        secondary='role_permissions',
        back_populates='roles'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_system': self.is_system,
            'permissions': sorted([p.name for p in self.permissions])
        }


class Permission(db.Model):
    """Permission definition."""
    __tablename__ = 'permissions'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    roles = db.relationship(
        'Role',
        secondary='role_permissions',
        back_populates='permissions'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }


class RolePermission(db.Model):
    """Role to permission mapping."""
    __tablename__ = 'role_permissions'

    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), primary_key=True)


class ServerRoleAssignment(db.Model):
    """Assign a role to a user for a specific server."""
    __tablename__ = 'server_role_assignments'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    server_id = db.Column(db.String(36), db.ForeignKey('servers.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('server_id', 'user_id', name='uq_server_user_role'),
    )

    role = db.relationship('Role')


class LdapGroupRoleAssignment(db.Model):
    """Assign a role to an LDAP group for a specific server."""
    __tablename__ = 'ldap_group_role_assignments'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    server_id = db.Column(db.String(36), db.ForeignKey('servers.id'), nullable=False)
    group_dn = db.Column(db.String(512), nullable=False)
    group_name = db.Column(db.String(255), nullable=True)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('server_id', 'group_dn', name='uq_server_group_role'),
    )

    role = db.relationship('Role')
