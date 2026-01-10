"""
Permission helpers for server access control.
"""
from app.extensions import db
from sqlalchemy import or_
import json
from app.models.role import Role, Permission, ServerRoleAssignment, LdapGroupRoleAssignment
from app.models.server import Server
from app.models.user import User

PERMISSIONS = {
    'server.view': 'View server overview and metrics',
    'server.settings.view': 'View server settings',
    'server.settings.edit': 'Edit server settings',
    'server.mods.view': 'View server mods',
    'server.mods.manage': 'Manage server mods',
    'server.players.view': 'View server players',
    'server.players.manage': 'Manage server players',
    'server.backups.view': 'View server backups',
    'server.backups.manage': 'Manage server backups',
    'server.console.view': 'View server console/logs',
    'server.console.command': 'Send server console commands',
    'server.files.view': 'View server files',
    'server.files.manage': 'Manage server files',
    'server.control': 'Start/stop/restart servers',
    'server.update': 'Update server configuration',
    'server.delete': 'Delete servers',
}

DEFAULT_ROLES = {
    'admin': {
        'description': 'Full access to all server actions',
        'permissions': list(PERMISSIONS.keys()),
        'is_system': True,
    },
    'operator': {
        'description': 'Console, backups, player management, and server control',
        'permissions': [
            'server.view',
            'server.console.view',
            'server.console.command',
            'server.backups.view',
            'server.backups.manage',
            'server.players.view',
            'server.players.manage',
            'server.control',
        ],
        'is_system': True,
    },
    'viewer': {
        'description': 'View-only access to server status',
        'permissions': [
            'server.view',
        ],
        'is_system': True,
    },
}


def seed_permissions_and_roles():
    """Ensure base permissions and default roles exist."""
    permission_map = {}
    for name, description in PERMISSIONS.items():
        permission = Permission.query.filter_by(name=name).first()
        if not permission:
            permission = Permission(name=name, description=description)
            db.session.add(permission)
        permission_map[name] = permission

    for role_name, role_data in DEFAULT_ROLES.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(
                name=role_name,
                description=role_data.get('description'),
                is_system=role_data.get('is_system', False)
            )
            db.session.add(role)

        role_permissions = set(role_data.get('permissions', []))
        for perm_name in role_permissions:
            perm = permission_map.get(perm_name)
            if perm and perm not in role.permissions:
                role.permissions.append(perm)

    db.session.commit()


def ensure_creator_assignments():
    """Ensure server creators have admin role assignments for existing servers."""
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        return

    servers = Server.query.all()
    for server in servers:
        exists = ServerRoleAssignment.query.filter_by(
            server_id=server.id,
            user_id=server.created_by
        ).first()
        if not exists:
            assignment = ServerRoleAssignment(
                server_id=server.id,
                user_id=server.created_by,
                role_id=admin_role.id
            )
            db.session.add(assignment)

    db.session.commit()


def get_user_role_for_server(user_id: str, server_id: str):
    assignment = ServerRoleAssignment.query.filter_by(
        server_id=server_id,
        user_id=user_id
    ).first()
    if assignment:
        return assignment.role
    return None


def _parse_ldap_groups(user: User):
    if not user or not user.is_ldap_user or not user.ldap_groups:
        return []
    try:
        groups = json.loads(user.ldap_groups)
        if isinstance(groups, list):
            return groups
    except json.JSONDecodeError:
        return []
    return []


def _best_role(roles):
    if not roles:
        return None
    return max(roles, key=lambda role: len(role.permissions))


def get_group_role_for_server(user: User, server: Server):
    groups = _parse_ldap_groups(user)
    if not groups:
        return None

    group_dns = [g.get('dn') for g in groups if isinstance(g, dict) and g.get('dn')]
    group_names = [g.get('name') for g in groups if isinstance(g, dict) and g.get('name')]

    assignments = LdapGroupRoleAssignment.query.filter(
        LdapGroupRoleAssignment.server_id == server.id
    ).filter(
        or_(
            LdapGroupRoleAssignment.group_dn.in_(group_dns or ['']),
            LdapGroupRoleAssignment.group_name.in_(group_names or [''])
        )
    ).all()

    roles = [assignment.role for assignment in assignments if assignment.role]
    return _best_role(roles)


def user_has_server_permission(user: User, server: Server, permission: str) -> bool:
    if not user or not server:
        return False
    if user.role == 'admin':
        return True
    role = get_user_role_for_server(user.id, server.id)
    if not role:
        role = get_group_role_for_server(user, server)
    if not role:
        if server.created_by == user.id:
            return True
        return False
    return any(p.name == permission for p in role.permissions)


def get_accessible_servers(user: User, permission: str | None = None):
    if user.role == 'admin':
        return Server.query.all()

    assignment_ids = db.session.query(ServerRoleAssignment.server_id).filter(
        ServerRoleAssignment.user_id == user.id
    )

    group_assignment_ids = None
    if user.is_ldap_user:
        groups = _parse_ldap_groups(user)
        group_dns = [g.get('dn') for g in groups if isinstance(g, dict) and g.get('dn')]
        group_names = [g.get('name') for g in groups if isinstance(g, dict) and g.get('name')]
        if group_dns or group_names:
            group_assignment_ids = db.session.query(LdapGroupRoleAssignment.server_id).filter(
                or_(
                    LdapGroupRoleAssignment.group_dn.in_(group_dns or ['']),
                    LdapGroupRoleAssignment.group_name.in_(group_names or [''])
                )
            )

    filters = [
        Server.created_by == user.id,
        Server.id.in_(assignment_ids),
    ]
    if group_assignment_ids is not None:
        filters.append(Server.id.in_(group_assignment_ids))

    servers = Server.query.filter(or_(*filters)).all()

    if not permission:
        return servers

    return [server for server in servers if user_has_server_permission(user, server, permission)]
