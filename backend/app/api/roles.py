"""
Role and permission management API endpoints.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.models.role import Role, Permission, ServerRoleAssignment, LdapGroupRoleAssignment
from app.models.server import Server
from app.models.ldap_config import LDAPConfig
from app.extensions import db

bp = Blueprint('roles', __name__)


def _require_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return None, (jsonify({'error': 'Forbidden'}), 403)
    return user, None


@bp.route('/roles', methods=['GET'])
@jwt_required()
def list_roles():
    """List all roles."""
    _, error = _require_admin()
    if error:
        return error

    roles = Role.query.order_by(Role.name.asc()).all()
    return jsonify([role.to_dict() for role in roles]), 200


@bp.route('/permissions', methods=['GET'])
@jwt_required()
def list_permissions():
    """List all permissions."""
    _, error = _require_admin()
    if error:
        return error

    permissions = Permission.query.order_by(Permission.name.asc()).all()
    return jsonify([permission.to_dict() for permission in permissions]), 200


@bp.route('/roles', methods=['POST'])
@jwt_required()
def create_role():
    """Create a new role."""
    _, error = _require_admin()
    if error:
        return error

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Role name required'}), 400

    if Role.query.filter_by(name=name).first():
        return jsonify({'error': 'Role already exists'}), 409

    role = Role(
        name=name,
        description=data.get('description'),
        is_system=False
    )
    db.session.add(role)

    permissions = data.get('permissions') or []
    if permissions:
        perms = Permission.query.filter(Permission.name.in_(permissions)).all()
        role.permissions = perms

    db.session.commit()
    return jsonify(role.to_dict()), 201


@bp.route('/roles/<role_id>', methods=['PATCH'])
@jwt_required()
def update_role(role_id):
    """Update a role."""
    _, error = _require_admin()
    if error:
        return error

    role = Role.query.get(role_id)
    if not role:
        return jsonify({'error': 'Role not found'}), 404

    data = request.get_json() or {}
    name = data.get('name')
    if name:
        name = name.strip()
        if name and name != role.name:
            if role.is_system:
                return jsonify({'error': 'Cannot rename system role'}), 400
            if Role.query.filter_by(name=name).first():
                return jsonify({'error': 'Role already exists'}), 409
            role.name = name

    if 'description' in data:
        role.description = data.get('description')

    if 'permissions' in data:
        perms = Permission.query.filter(Permission.name.in_(data.get('permissions') or [])).all()
        role.permissions = perms

    db.session.commit()
    return jsonify(role.to_dict()), 200


@bp.route('/roles/<role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(role_id):
    """Delete a role."""
    _, error = _require_admin()
    if error:
        return error

    role = Role.query.get(role_id)
    if not role:
        return jsonify({'error': 'Role not found'}), 404
    if role.is_system:
        return jsonify({'error': 'Cannot delete system role'}), 400

    ServerRoleAssignment.query.filter_by(role_id=role.id).delete()
    db.session.delete(role)
    db.session.commit()
    return jsonify({'message': 'Role deleted'}), 200


@bp.route('/servers/<server_id>/assignments', methods=['GET'])
@jwt_required()
def list_server_assignments(server_id):
    """List role assignments for a server."""
    _, error = _require_admin()
    if error:
        return error

    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    assignments = ServerRoleAssignment.query.filter_by(server_id=server_id).all()
    payload = []
    for assignment in assignments:
        payload.append({
            'user_id': assignment.user_id,
            'role_id': assignment.role_id,
            'role_name': assignment.role.name if assignment.role else None,
        })
    return jsonify(payload), 200


@bp.route('/servers/<server_id>/assignments', methods=['POST'])
@jwt_required()
def assign_server_role(server_id):
    """Assign a role to a user for a server."""
    _, error = _require_admin()
    if error:
        return error

    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    data = request.get_json() or {}
    user_id = data.get('user_id')
    role_id = data.get('role_id')

    if not user_id or not role_id:
        return jsonify({'error': 'user_id and role_id required'}), 400

    role = Role.query.get(role_id)
    if not role:
        return jsonify({'error': 'Role not found'}), 404

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    assignment = ServerRoleAssignment.query.filter_by(
        server_id=server_id,
        user_id=user_id
    ).first()

    if assignment:
        assignment.role_id = role_id
    else:
        assignment = ServerRoleAssignment(
            server_id=server_id,
            user_id=user_id,
            role_id=role_id
        )
        db.session.add(assignment)

    db.session.commit()
    return jsonify({'message': 'Assignment saved'}), 200


@bp.route('/servers/<server_id>/assignments/<user_id>', methods=['DELETE'])
@jwt_required()
def remove_server_assignment(server_id, user_id):
    """Remove a user's role assignment for a server."""
    _, error = _require_admin()
    if error:
        return error

    assignment = ServerRoleAssignment.query.filter_by(
        server_id=server_id,
        user_id=user_id
    ).first()
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({'message': 'Assignment removed'}), 200


@bp.route('/ldap/groups', methods=['GET'])
@jwt_required()
def list_ldap_groups():
    """List LDAP groups for role assignments."""
    _, error = _require_admin()
    if error:
        return error

    config = LDAPConfig.query.get(1)
    if not config or not config.enabled:
        return jsonify([]), 200

    if not config.server_uri or not config.group_search_base:
        return jsonify({'error': 'LDAP group search is not configured'}), 400

    try:
        import ssl
        from urllib.parse import urlparse
        from ldap3 import Server, Connection, ALL, Tls, SUBTREE
        from ldap3.utils.conv import escape_filter_chars

        def parse_server_uri(uri: str):
            if '://' not in uri:
                parsed = urlparse(f"ldap://{uri}")
            else:
                parsed = urlparse(uri)
            scheme = parsed.scheme or 'ldap'
            host = parsed.hostname or uri
            port = parsed.port or (636 if scheme == 'ldaps' else 389)
            return host, port, scheme == 'ldaps'

        def normalize_group_filter(filter_template: str) -> str:
            tokens = ['%uid', '%u', '%s', '{username}', '{email}', '{user}', '{dn}', '{user_dn}']
            result = filter_template
            for token in tokens:
                if token in result:
                    result = result.replace(token, escape_filter_chars('*'))
            return result

        host, port, use_ssl = parse_server_uri(config.server_uri)
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2) if use_ssl else None
        server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL, tls=tls_config)
        if config.bind_dn:
            conn = Connection(server, user=config.bind_dn, password=config.bind_password or '', auto_bind=True)
        else:
            conn = Connection(server, auto_bind=True)

        group_filter = config.group_search_filter or '(|(objectClass=groupOfNames)(objectClass=group)(objectClass=posixGroup))'
        group_filter = normalize_group_filter(group_filter)

        conn.search(
            search_base=config.group_search_base,
            search_filter=group_filter,
            search_scope=SUBTREE,
            attributes=['cn']
        )

        groups = []
        for entry in conn.entries:
            name = None
            if 'cn' in entry.entry_attributes_as_dict:
                cn_values = entry.entry_attributes_as_dict.get('cn')
                if isinstance(cn_values, (list, tuple)) and cn_values:
                    name = str(cn_values[0])
                elif cn_values:
                    name = str(cn_values)
            groups.append({'dn': entry.entry_dn, 'name': name or entry.entry_dn})

        conn.unbind()

        groups = sorted(groups, key=lambda g: g.get('name', ''))
        return jsonify(groups), 200
    except Exception as e:
        return jsonify({'error': f'LDAP group lookup failed: {e}'}), 400


@bp.route('/servers/<server_id>/group-assignments', methods=['GET'])
@jwt_required()
def list_group_assignments(server_id):
    """List LDAP group role assignments for a server."""
    _, error = _require_admin()
    if error:
        return error

    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    assignments = LdapGroupRoleAssignment.query.filter_by(server_id=server_id).all()
    payload = []
    for assignment in assignments:
        payload.append({
            'group_dn': assignment.group_dn,
            'group_name': assignment.group_name,
            'role_id': assignment.role_id,
            'role_name': assignment.role.name if assignment.role else None,
        })
    return jsonify(payload), 200


@bp.route('/servers/<server_id>/group-assignments', methods=['POST'])
@jwt_required()
def assign_group_role(server_id):
    """Assign a role to an LDAP group for a server."""
    _, error = _require_admin()
    if error:
        return error

    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    data = request.get_json() or {}
    group_dn = data.get('group_dn')
    role_id = data.get('role_id')

    if not group_dn or not role_id:
        return jsonify({'error': 'group_dn and role_id required'}), 400

    role = Role.query.get(role_id)
    if not role:
        return jsonify({'error': 'Role not found'}), 404

    assignment = LdapGroupRoleAssignment.query.filter_by(
        server_id=server_id,
        group_dn=group_dn
    ).first()

    if assignment:
        assignment.role_id = role_id
        assignment.group_name = data.get('group_name') or assignment.group_name
    else:
        assignment = LdapGroupRoleAssignment(
            server_id=server_id,
            group_dn=group_dn,
            group_name=data.get('group_name'),
            role_id=role_id
        )
        db.session.add(assignment)

    db.session.commit()
    return jsonify({'message': 'Group assignment saved'}), 200


@bp.route('/servers/<server_id>/group-assignments', methods=['DELETE'])
@jwt_required()
def remove_group_assignment(server_id):
    """Remove LDAP group assignment for a server."""
    _, error = _require_admin()
    if error:
        return error

    group_dn = request.args.get('group_dn')
    if not group_dn:
        return jsonify({'error': 'group_dn required'}), 400

    assignment = LdapGroupRoleAssignment.query.filter_by(
        server_id=server_id,
        group_dn=group_dn
    ).first()
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({'message': 'Group assignment removed'}), 200
