"""
LDAP configuration API endpoints.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.ldap_config import LDAPConfig
from app.models.user import User

bp = Blueprint('ldap_config', __name__)


def _require_admin(user: User):
    if not user or user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    return None


@bp.route('', methods=['GET'])
@jwt_required()
def get_ldap_config():
    """Get LDAP config (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    admin_check = _require_admin(user)
    if admin_check:
        return admin_check

    config = LDAPConfig.query.get(1)
    if not config:
        config = LDAPConfig(id=1, enabled=False)
        db.session.add(config)
        db.session.commit()

    return jsonify(config.to_dict()), 200


@bp.route('', methods=['PUT'])
@jwt_required()
def update_ldap_config():
    """Update LDAP config (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    admin_check = _require_admin(user)
    if admin_check:
        return admin_check

    data = request.get_json() or {}

    config = LDAPConfig.query.get(1)
    if not config:
        config = LDAPConfig(id=1)
        db.session.add(config)

    for field in [
        'enabled',
        'server_uri',
        'bind_dn',
        'bind_password',
        'user_search_base',
        'user_search_filter',
        'group_search_base',
        'group_search_filter',
    ]:
        if field in data:
            setattr(config, field, data[field])

    config.updated_by = user_id
    db.session.commit()

    return jsonify(config.to_dict()), 200


@bp.route('/test', methods=['POST'])
@jwt_required()
def test_ldap_connection():
    """Test LDAP connection (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    admin_check = _require_admin(user)
    if admin_check:
        return admin_check

    data = request.get_json() or {}

    server_uri = data.get('server_uri')
    bind_dn = data.get('bind_dn')
    bind_password = data.get('bind_password')

    if not server_uri or not bind_dn or not bind_password:
        return jsonify({'error': 'server_uri, bind_dn, and bind_password required'}), 400

    try:
        import ssl
        from urllib.parse import urlparse
        from ldap3 import Server, Connection, ALL, Tls

        def parse_server_uri(uri: str):
            if '://' not in uri:
                parsed = urlparse(f"ldap://{uri}")
            else:
                parsed = urlparse(uri)
            scheme = parsed.scheme or 'ldap'
            host = parsed.hostname or uri
            port = parsed.port or (636 if scheme == 'ldaps' else 389)
            return host, port, scheme == 'ldaps'

        host, port, use_ssl = parse_server_uri(server_uri)
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2) if use_ssl else None
        server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL, tls=tls_config)
        conn = Connection(server, user=bind_dn, password=bind_password, auto_bind=True)
        conn.unbind()
        return jsonify({'message': 'LDAP connection successful'}), 200
    except Exception as e:
        return jsonify({'error': f'LDAP connection failed: {e}'}), 400
