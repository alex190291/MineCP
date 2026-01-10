"""
Authentication API endpoints.
"""
import json
import io
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import qrcode

from app.extensions import db, limiter
from app.models.ldap_config import LDAPConfig
from app.models.user import User
from app.utils.audit import log_login, log_logout

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    Authenticate user and return JWT tokens.
    ---
    POST /api/auth/login
    {
        "username": "admin",
        "password": "password"
    }
    """
    data = request.get_json() or {}

    username = data.get('username') or data.get('email')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User.query.filter_by(email=username).first()

    if user and not user.is_ldap_user and user.check_password(password):
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403

        # Check if user is using default admin credentials - require password change
        from flask import current_app
        default_admin_username = current_app.config.get('DEFAULT_ADMIN_USERNAME', 'admin')
        default_admin_password = current_app.config.get('DEFAULT_ADMIN_PASSWORD', 'changeme')

        if (user.username == default_admin_username and
            password == default_admin_password and
            user.role == 'admin'):
            require_password_change = True
        else:
            require_password_change = False

        # Check if 2FA is enabled for this user
        if user.totp_enabled:
            totp_code = data.get('totp_code')
            backup_code = data.get('backup_code')

            if not totp_code and not backup_code:
                return jsonify({
                    'error': '2FA required',
                    'message': 'Please provide your 6-digit 2FA code or a backup code',
                    'require_2fa': True,
                    'user_id': user.id
                }), 401

            # Verify TOTP code
            if totp_code:
                totp = pyotp.TOTP(user.totp_secret)
                if not totp.verify(totp_code, valid_window=1):
                    log_login(user.id, success=False, details={'method': 'local', 'username': username, 'reason': 'invalid_2fa_code'})
                    return jsonify({'error': 'Invalid 2FA code'}), 401

            # Verify backup code
            elif backup_code:
                if not user.backup_codes:
                    return jsonify({'error': 'No backup codes available'}), 401

                backup_codes = json.loads(user.backup_codes)
                backup_code_valid = False

                for idx, hashed_code in enumerate(backup_codes):
                    if check_password_hash(hashed_code, backup_code):
                        backup_code_valid = True
                        # Remove used backup code
                        backup_codes.pop(idx)
                        user.backup_codes = json.dumps(backup_codes)
                        db.session.commit()
                        break

                if not backup_code_valid:
                    log_login(user.id, success=False, details={'method': 'local', 'username': username, 'reason': 'invalid_backup_code'})
                    return jsonify({'error': 'Invalid backup code'}), 401

        user.last_login = datetime.utcnow()
        db.session.commit()

        access_token = create_access_token(
            identity=user.id,
            additional_claims={'setup_required': require_password_change}
        )
        refresh_token = create_refresh_token(identity=user.id)

        # Audit log successful login
        log_login(user.id, success=True, details={'method': 'local', 'username': username, '2fa_used': user.totp_enabled})

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'require_password_change': require_password_change
        }), 200

    ldap_result = _ldap_authenticate(username, password)
    if ldap_result and ldap_result.get('error'):
        error_code = ldap_result['error']
        if error_code == 'disabled':
            return jsonify({'error': 'Account is disabled'}), 403
        if error_code == 'totp_required':
            return jsonify({
                'error': 'TOTP code required. Append your 6-digit code to your password.'
            }), 401
        if error_code == 'totp_invalid':
            return jsonify({'error': 'Invalid TOTP code'}), 401
        return jsonify({'error': error_code}), 401

    if ldap_result:
        if user and not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403

        ldap_role = ldap_result.get('role', 'user')
        ldap_groups = ldap_result.get('groups') or []

        if not user:
            resolved_username = ldap_result.get('username') or username
            user = User(
                username=resolved_username,
                email=ldap_result.get('email') or f"{username}@ldap.local",
                role=ldap_role,
                is_ldap_user=True,
                ldap_dn=ldap_result.get('dn'),
                is_active=True
            )
            db.session.add(user)
        else:
            # Update existing user with LDAP info and role
            user.is_ldap_user = True
            user.ldap_dn = ldap_result.get('dn')
            user.role = ldap_role  # Update role based on current LDAP groups
            if ldap_result.get('email'):
                user.email = ldap_result['email']
        if ldap_groups:
            import json as _json
            user.ldap_groups = _json.dumps(ldap_groups)

        user.last_login = datetime.utcnow()
        db.session.commit()

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        # Audit log successful LDAP login
        log_login(user.id, success=True, details={'method': 'ldap', 'username': username})

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200

    # Audit log failed login attempt
    log_login(None, success=False, details={'username': username, 'reason': 'invalid_credentials'})

    return jsonify({'error': 'Invalid credentials'}), 401


def check_ldap_group_membership(
    connection,
    user_dn: str,
    user_entry,
    admin_group_name: str,
    group_search_base: str = None,
    group_search_filter: str = None
) -> bool:
    """
    Check if a user is a member of a specific LDAP group.

    There are two common approaches:
    1. Check memberOf attribute on user entry (Active Directory style)
    2. Search for group objects that contain the user DN (OpenLDAP style)

    Args:
        connection: Active LDAP connection
        user_dn: User's distinguished name
        user_entry: User's LDAP entry (may contain memberOf)
        admin_group_name: Name of the admin group to check
        group_search_base: Base DN for group searches
        group_search_filter: LDAP filter for group searches

    Returns:
        True if user is member of admin group, False otherwise
    """
    from ldap3 import SUBTREE
    from flask import current_app

    current_app.logger.info(f'Checking group membership for user DN: {user_dn}')
    current_app.logger.info(f'Admin group name: {admin_group_name}')

    # Approach 1: Check memberOf attribute (Active Directory, modern OpenLDAP)
    if user_entry:
        try:
            member_of_values = entry_attr_values(user_entry, 'memberOf')
            current_app.logger.info(f'User memberOf values: {member_of_values}')

            for group_dn in member_of_values:
                # Check if admin_group_name appears in the group DN
                # Case-insensitive matching
                if admin_group_name.lower() in group_dn.lower():
                    current_app.logger.info(f'✅ User is admin via memberOf: {group_dn}')
                    return True
        except Exception as e:
            current_app.logger.warning(f'Error checking memberOf: {e}')

    # Approach 2: Search for groups containing this user (fallback for OpenLDAP)
    if connection and group_search_base:
        try:
            # Search for group with matching name that contains this user
            search_filter = f'(&(cn={admin_group_name})(member={user_dn}))'
            current_app.logger.info(f'Searching groups with filter: {search_filter} in base: {group_search_base}')

            connection.search(
                search_base=group_search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['cn']
            )

            if connection.entries:
                current_app.logger.info(f'✅ User is admin via group search: {connection.entries}')
                return True
            else:
                current_app.logger.info(f'No matching groups found in group search')
        except Exception as e:
            current_app.logger.warning(f'Group search failed: {e}')
    else:
        if not connection:
            current_app.logger.warning('No LDAP connection available for group search')
        if not group_search_base:
            current_app.logger.warning('No group_search_base configured for group search')

    current_app.logger.info('❌ User is not in admin group')
    return False


def _ldap_authenticate(username: str, password: str):
    """Authenticate against LDAP and return user metadata if successful."""
    import ssl
    from urllib.parse import urlparse
    from flask import current_app

    config = LDAPConfig.query.get(1)
    if not config or not config.enabled:
        return None

    if not config.server_uri:
        current_app.logger.warning('LDAP config missing server_uri; skipping LDAP auth')
        return None

    filter_template = (config.user_search_filter or '').strip()
    if not filter_template:
        filter_template = '(uid={username})'

    if not config.user_search_base and filter_template.startswith('('):
        current_app.logger.warning('LDAP config incomplete; skipping LDAP auth')
        return None

    def normalize_filter(filter_template: str) -> str:
        from ldap3.utils.conv import escape_filter_chars

        safe_value = escape_filter_chars(username)
        tokens = ['%uid', '%u', '%s', '{username}', '{email}', '{user}']
        result = filter_template
        for token in tokens:
            if token in result:
                result = result.replace(token, safe_value)
        return result

    def normalize_dn(template: str) -> str:
        from ldap3.utils.dn import escape_dn_chars

        safe_value = escape_dn_chars(username)
        tokens = ['%uid', '%u', '%s', '{username}', '{email}', '{user}']
        result = template
        for token in tokens:
            if token in result:
                result = result.replace(token, safe_value)
        return result

    def infer_user_dn(filter_template: str, search_base: str) -> str:
        import re
        from ldap3.utils.dn import escape_dn_chars

        pattern = r'\(\s*([a-zA-Z0-9_-]+)\s*=\s*(\{username\}|\{email\}|%s|%u|%uid)\s*\)'
        match = re.search(pattern, filter_template)
        attr = match.group(1) if match else 'uid'
        return f"{attr}={escape_dn_chars(username)},{search_base}"

    def parse_server_uri(uri: str):
        if '://' not in uri:
            parsed = urlparse(f"ldap://{uri}")
        else:
            parsed = urlparse(uri)
        scheme = parsed.scheme or 'ldap'
        host = parsed.hostname or uri
        port = parsed.port or (636 if scheme == 'ldaps' else 389)
        return host, port, scheme == 'ldaps'

    def is_dn_template(value: str) -> bool:
        return bool(value and not value.startswith('(') and '=' in value and ',' in value)

    def entry_attr_values(entry, attr: str):
        if not entry:
            return []
        attrs = entry.entry_attributes_as_dict
        if attr not in attrs:
            return []
        value = attrs.get(attr)
        if isinstance(value, (list, tuple, set)):
            return [str(v) for v in value]
        return [str(value)]

    def parse_ldap_bool(value) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in ('true', '1', 'yes')
        return False

    def extract_group_name(dn: str) -> str | None:
        if not dn:
            return None
        parts = dn.split(',')
        for part in parts:
            if part.strip().lower().startswith('cn='):
                return part.split('=', 1)[1]
        return None

    def normalize_group_filter(filter_template: str, user_dn_value: str) -> str:
        from ldap3.utils.conv import escape_filter_chars

        safe_username = escape_filter_chars(username)
        safe_dn = escape_filter_chars(user_dn_value)
        tokens = {
            '{username}': safe_username,
            '{user}': safe_username,
            '{uid}': safe_username,
            '%s': safe_username,
            '%u': safe_username,
            '%uid': safe_username,
            '{dn}': safe_dn,
            '{user_dn}': safe_dn,
        }
        result = filter_template
        for token, value in tokens.items():
            result = result.replace(token, value)
        return result

    def get_user_groups(connection, user_dn_value: str, group_search_base: str, group_search_filter: str):
        groups = []
        # memberOf attribute (Active Directory, some LDAPs)
        member_of_dns = entry_attr_values(entry, 'memberOf')
        for group_dn in member_of_dns:
            group_name = extract_group_name(group_dn)
            groups.append({'dn': group_dn, 'name': group_name or group_dn})

        if connection and group_search_base:
            search_filter = group_search_filter or '(|(member={dn})(uniqueMember={dn})(memberUid={username}))'
            normalized_filter = normalize_group_filter(search_filter, user_dn_value)
            try:
                connection.search(
                    search_base=group_search_base,
                    search_filter=normalized_filter,
                    search_scope=SUBTREE,
                    attributes=['cn']
                )
                for entry_item in connection.entries:
                    group_dn = entry_item.entry_dn
                    group_name_values = entry_attr_values(entry_item, 'cn')
                    group_name = group_name_values[0] if group_name_values else extract_group_name(group_dn)
                    groups.append({'dn': group_dn, 'name': group_name or group_dn})
            except Exception as e:
                current_app.logger.warning(f'LDAP group search failed: {e}')

        # Deduplicate by DN
        unique = {}
        for group in groups:
            group_dn = group.get('dn')
            if group_dn and group_dn not in unique:
                unique[group_dn] = group
        return list(unique.values())

    def validate_totp_code(totp_code: str, secrets, valid_window: int = 1) -> bool:
        import base64
        import binascii
        import hmac
        import hashlib
        import struct
        import time

        def normalize_secret(raw_secret: str):
            cleaned = raw_secret.strip()
            try:
                secret_bytes = bytes.fromhex(cleaned)
                return secret_bytes
            except (ValueError, binascii.Error):
                pass

            padded = cleaned.upper()
            if len(padded) % 8:
                padded = padded + ('=' * (8 - len(padded) % 8))
            try:
                return base64.b32decode(padded)
            except Exception:
                return None

        def totp_for_secret(secret_bytes: bytes, for_time: float, digits: int = 6) -> str:
            counter = int(for_time // 30)
            msg = struct.pack('>Q', counter)
            digest = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
            offset = digest[-1] & 0x0F
            code = struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7fffffff
            return str(code % (10 ** digits)).zfill(digits)

        now = time.time()
        for secret in secrets:
            if not secret:
                continue
            secret_bytes = normalize_secret(str(secret))
            if not secret_bytes:
                continue
            for window in range(-valid_window, valid_window + 1):
                candidate = totp_for_secret(secret_bytes, now + (window * 30))
                if candidate == totp_code:
                    return True
        return False

    bind_conn = None
    user_conn = None

    try:
        from ldap3 import Server, Connection, ALL, Tls, SUBTREE, BASE

        host, port, use_ssl = parse_server_uri(config.server_uri)
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2) if use_ssl else None
        server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL, tls=tls_config)

        if config.bind_dn:
            try:
                bind_conn = Connection(
                    server,
                    user=config.bind_dn,
                    password=config.bind_password or '',
                    auto_bind=True
                )
            except Exception as e:
                current_app.logger.warning(f'LDAP bind DN connection failed: {e}')
                bind_conn = None
        else:
            try:
                bind_conn = Connection(server, auto_bind=True)
            except Exception as e:
                current_app.logger.warning(f'LDAP anonymous bind failed: {e}')
                bind_conn = None

        entry = None
        user_dn = None

        if is_dn_template(filter_template):
            user_dn = normalize_dn(filter_template)
            if bind_conn:
                bind_conn.search(
                    search_base=user_dn,
                    search_filter='(objectClass=*)',
                    search_scope=BASE,
                    attributes=['mail', 'uid', 'cn', 'loginDisabled', 'objectClass', 'oath-hotp-hex-secret']
                )
                if bind_conn.entries:
                    entry = bind_conn.entries[0]
        else:
            search_filter = normalize_filter(filter_template)
            if bind_conn:
                bind_conn.search(
                    search_base=config.user_search_base,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=['mail', 'uid', 'cn', 'loginDisabled', 'objectClass', 'oath-hotp-hex-secret']
                )

                if bind_conn.entries:
                    entry = bind_conn.entries[0]
                    user_dn = entry.entry_dn

            if not user_dn:
                user_dn = infer_user_dn(filter_template, config.user_search_base)

        if not user_dn:
            current_app.logger.warning('LDAP user DN could not be resolved')
            return None

        if entry:
            login_disabled = any(parse_ldap_bool(v) for v in entry_attr_values(entry, 'loginDisabled'))
            if login_disabled:
                return {'error': 'disabled'}

        totp_secrets = entry_attr_values(entry, 'oath-hotp-hex-secret')
        object_classes = [v.lower() for v in entry_attr_values(entry, 'objectClass')]
        totp_enabled = bool(totp_secrets) and any(
            cls in ('oathtotpuser', 'oath-totp-token') for cls in object_classes
        )
        actual_password = password
        totp_code = None

        if totp_enabled:
            if len(password) >= 6 and password[-6:].isdigit():
                actual_password = password[:-6]
                totp_code = password[-6:]
            else:
                return {'error': 'totp_required'}

        try:
            user_conn = Connection(
                server,
                user=user_dn,
                password=actual_password,
                auto_bind=True
            )
        except Exception:
            if totp_enabled and actual_password != password:
                user_conn = Connection(
                    server,
                    user=user_dn,
                    password=password,
                    auto_bind=True
                )
            else:
                raise

        if totp_enabled and totp_code:
            if not validate_totp_code(totp_code, totp_secrets, valid_window=1):
                return {'error': 'totp_invalid'}

        email = None
        resolved_username = None
        if entry:
            email_values = entry_attr_values(entry, 'mail')
            if email_values:
                email = email_values[0]
            uid_values = entry_attr_values(entry, 'uid')
            if uid_values:
                resolved_username = uid_values[0]
            elif entry_attr_values(entry, 'cn'):
                resolved_username = entry_attr_values(entry, 'cn')[0]

        # Determine user role based on group membership
        user_role = 'user'  # Default role

        # TODO: Implement group membership checking
        # Check if user is member of admin group to determine role
        if config.admin_group_name:
            is_admin = check_ldap_group_membership(
                bind_conn,
                user_dn,
                entry,
                config.admin_group_name,
                config.group_search_base,
                config.group_search_filter
            )
            if is_admin:
                user_role = 'admin'

        groups = get_user_groups(bind_conn, user_dn, config.group_search_base, config.group_search_filter)

        return {
            'dn': user_dn,
            'email': email,
            'username': resolved_username,
            'role': user_role,
            'groups': groups
        }

    except Exception as e:
        current_app.logger.warning(f'LDAP authentication failed: {e}')
        return None
    finally:
        if user_conn:
            user_conn.unbind()
        if bind_conn:
            bind_conn.unbind()


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token.
    ---
    POST /api/auth/refresh
    Authorization: Bearer <refresh_token>
    """
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token}), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information.
    ---
    GET /api/auth/me
    Authorization: Bearer <access_token>
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user.to_dict()), 200


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user (revoke JWT token).
    ---
    POST /api/auth/logout
    Authorization: Bearer <access_token>
    """
    from app.utils.token_blacklist import get_blacklist
    from flask import current_app

    user_id = get_jwt_identity()
    jwt_data = get_jwt()
    jti = jwt_data["jti"]
    exp_timestamp = jwt_data["exp"]

    # Calculate time until token expires
    now_timestamp = datetime.utcnow().timestamp()
    expires_in = int(exp_timestamp - now_timestamp)

    if expires_in > 0:
        # Add token to blacklist
        blacklist = get_blacklist()
        blacklist.add_token(jti, expires_in)
        current_app.logger.info(f"Token {jti} blacklisted for user {user_id}")

    # Audit log logout
    log_logout(user_id)

    return jsonify({'message': 'Logged out successfully'}), 200


@bp.route('/complete-setup', methods=['POST'])
@jwt_required()
def complete_setup():
    """Delete bootstrap/default admin user after setup and revoke token."""
    from app.utils.token_blacklist import get_blacklist
    from app.models.system_setup import SystemSetup
    from flask import current_app

    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    jwt_data = get_jwt()
    jti = jwt_data["jti"]
    exp_timestamp = jwt_data["exp"]

    setup_required = bool(jwt_data.get('setup_required'))

    if not user:
        return jsonify({'message': 'User already removed'}), 200

    if user.role != 'bootstrap' and not setup_required:
        return jsonify({'error': 'Setup completion not allowed'}), 403

    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete setup user: {e}")
        return jsonify({'error': 'Failed to complete setup'}), 500

    try:
        SystemSetup.mark_setup_complete()
    except Exception as e:
        current_app.logger.warning(f"Failed to mark setup complete: {e}")

    # Blacklist current token
    now_timestamp = datetime.utcnow().timestamp()
    expires_in = int(exp_timestamp - now_timestamp)
    if expires_in > 0:
        blacklist = get_blacklist()
        blacklist.add_token(jti, expires_in)

    return jsonify({'message': 'Setup completed'}), 200


@bp.route('/2fa/setup', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def setup_2fa():
    """
    Generate a new TOTP secret and QR code for 2FA setup.
    Does not enable 2FA until verified via /2fa/enable.
    ---
    POST /api/auth/2fa/setup
    Authorization: Bearer <access_token>
    """
    from flask import current_app

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.is_ldap_user:
        return jsonify({'error': '2FA setup not available for LDAP users'}), 400

    # Generate a new TOTP secret
    secret = pyotp.random_base32()

    # Create provisioning URI for QR code
    # Format: otpauth://totp/ServiceName:username?secret=SECRET&issuer=ServiceName
    app_name = current_app.config.get('APP_NAME', 'Minecraft Manager')
    provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.username,
        issuer_name=app_name
    )

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64 for easy transmission
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    import base64
    qr_code_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')

    # Store secret temporarily (not enabled yet)
    user.totp_secret = secret
    db.session.commit()

    return jsonify({
        'secret': secret,
        'qr_code': f'data:image/png;base64,{qr_code_base64}',
        'provisioning_uri': provisioning_uri,
        'message': 'Scan the QR code with your authenticator app, then verify with /2fa/enable'
    }), 200


@bp.route('/2fa/enable', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def enable_2fa():
    """
    Verify TOTP code and enable 2FA for the user.
    Also generates backup codes.
    ---
    POST /api/auth/2fa/enable
    Authorization: Bearer <access_token>
    Body: {"totp_code": "123456"}
    """
    import secrets

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.is_ldap_user:
        return jsonify({'error': '2FA not available for LDAP users'}), 400

    if not user.totp_secret:
        return jsonify({'error': 'Please run /2fa/setup first'}), 400

    if user.totp_enabled:
        return jsonify({'error': '2FA is already enabled'}), 400

    data = request.get_json() or {}
    totp_code = data.get('totp_code')

    if not totp_code:
        return jsonify({'error': 'totp_code required'}), 400

    # Verify the TOTP code
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(totp_code, valid_window=1):
        return jsonify({'error': 'Invalid TOTP code'}), 401

    # Generate backup codes
    backup_codes = []
    backup_codes_hashed = []

    for _ in range(10):
        # Generate 8-character alphanumeric backup codes
        code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        backup_codes.append(code)
        backup_codes_hashed.append(generate_password_hash(code))

    # Enable 2FA
    user.totp_enabled = True
    user.backup_codes = json.dumps(backup_codes_hashed)
    db.session.commit()

    return jsonify({
        'message': '2FA enabled successfully',
        'backup_codes': backup_codes,
        'warning': 'Save these backup codes in a secure location. They will not be shown again.'
    }), 200


@bp.route('/2fa/disable', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def disable_2fa():
    """
    Disable 2FA for the user.
    Requires current password for security.
    ---
    POST /api/auth/2fa/disable
    Authorization: Bearer <access_token>
    Body: {"password": "current_password"}
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.totp_enabled:
        return jsonify({'error': '2FA is not enabled'}), 400

    data = request.get_json() or {}
    password = data.get('password')

    if not password:
        return jsonify({'error': 'Password required to disable 2FA'}), 400

    # Verify current password
    if not user.check_password(password):
        return jsonify({'error': 'Invalid password'}), 401

    # Disable 2FA
    user.totp_enabled = False
    user.totp_secret = None
    user.backup_codes = None
    db.session.commit()

    return jsonify({'message': '2FA disabled successfully'}), 200


@bp.route('/2fa/status', methods=['GET'])
@jwt_required()
def get_2fa_status():
    """
    Get 2FA status for current user.
    ---
    GET /api/auth/2fa/status
    Authorization: Bearer <access_token>
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    backup_codes_count = 0
    if user.backup_codes:
        try:
            backup_codes_count = len(json.loads(user.backup_codes))
        except:
            pass

    return jsonify({
        'enabled': user.totp_enabled,
        'is_ldap_user': user.is_ldap_user,
        'backup_codes_remaining': backup_codes_count if user.totp_enabled else None
    }), 200


@bp.route('/2fa/regenerate-backup-codes', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def regenerate_backup_codes():
    """
    Regenerate backup codes for 2FA.
    Requires TOTP code verification.
    ---
    POST /api/auth/2fa/regenerate-backup-codes
    Authorization: Bearer <access_token>
    Body: {"totp_code": "123456"}
    """
    import secrets

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.totp_enabled:
        return jsonify({'error': '2FA is not enabled'}), 400

    data = request.get_json() or {}
    totp_code = data.get('totp_code')

    if not totp_code:
        return jsonify({'error': 'totp_code required'}), 400

    # Verify the TOTP code
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(totp_code, valid_window=1):
        return jsonify({'error': 'Invalid TOTP code'}), 401

    # Generate new backup codes
    backup_codes = []
    backup_codes_hashed = []

    for _ in range(10):
        code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        backup_codes.append(code)
        backup_codes_hashed.append(generate_password_hash(code))

    user.backup_codes = json.dumps(backup_codes_hashed)
    db.session.commit()

    return jsonify({
        'message': 'Backup codes regenerated successfully',
        'backup_codes': backup_codes,
        'warning': 'Save these backup codes in a secure location. They will not be shown again.'
    }), 200
