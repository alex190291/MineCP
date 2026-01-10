"""
User management API endpoints.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db, limiter
from app.models.user import User
from app.utils.audit import log_user_create, log_user_delete, log_user_update, log_password_change
from app.utils.security import validate_password_strength

bp = Blueprint('users', __name__)

def _require_admin(user: User):
    if not user or user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    return None


@bp.route('', methods=['GET'])
@jwt_required()
def list_users():
    """List all users (admin only)."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    admin_check = _require_admin(current_user)
    if admin_check:
        return admin_check

    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@bp.route('', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def create_user():
    """Create a user (admin only)."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user or current_user.role != 'admin':
        if not current_user or current_user.role != 'bootstrap':
            return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    required = ['username', 'email', 'role']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    if current_user.role == 'bootstrap':
        if User.query.filter_by(role='admin').first():
            return jsonify({'error': 'Admin account already exists'}), 409
        if data.get('role') != 'admin':
            return jsonify({'error': 'Bootstrap can only create an admin account'}), 403
    else:
        if data.get('role') not in ['admin', 'user']:
            return jsonify({'error': 'Invalid role'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409

    user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user'),
        is_ldap_user=data.get('is_ldap_user', False),
        is_active=data.get('is_active', True),
    )

    if current_user.role == 'bootstrap':
        user.role = 'admin'
        user.is_ldap_user = False
        user.is_active = True

    if not user.is_ldap_user:
        password = data.get('password')
        if not password:
            return jsonify({'error': 'Password required for non-LDAP user'}), 400

        # Validate password strength
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # If bootstrap user created an admin, delete the bootstrap user and mark setup complete
    if current_user.role == 'bootstrap':
        from app.models.system_setup import SystemSetup
        try:
            db.session.delete(current_user)
            db.session.commit()
            SystemSetup.mark_setup_complete()
        except Exception as e:
            db.session.rollback()
            # Log the error but don't fail the user creation
            from flask import current_app as app
            app.logger.error(f"Failed to delete bootstrap user: {e}")

    # Audit log user creation
    log_user_create(user.id, user.username)

    return jsonify(user.to_dict()), 201


@bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get user details."""
    requester_id = get_jwt_identity()
    requester = User.query.get(requester_id)

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if requester and requester.role != 'admin' and user.id != requester_id:
        return jsonify({'error': 'Forbidden'}), 403

    return jsonify(user.to_dict()), 200


@bp.route('/<user_id>', methods=['PATCH'])
@jwt_required()
@limiter.limit("30 per hour")
def update_user(user_id):
    """Update user details."""
    requester_id = get_jwt_identity()
    requester = User.query.get(requester_id)

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if requester and requester.role != 'admin' and user.id != requester_id:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    fields_changed = []

    # Explicit field mapping with validation (prevent SQL injection via setattr)
    ALLOWED_FIELDS = {
        'username': lambda v: isinstance(v, str) and len(v) <= 100,
        'email': lambda v: isinstance(v, str) and '@' in v and len(v) <= 255,
        'is_active': lambda v: isinstance(v, bool),
    }

    ADMIN_ONLY_FIELDS = {
        'role': lambda v: v in ['user', 'admin'],
        'is_ldap_user': lambda v: isinstance(v, bool),
    }

    # Update allowed fields
    for field, validator in ALLOWED_FIELDS.items():
        if field in data:
            value = data[field]
            if not validator(value):
                return jsonify({'error': f'Invalid value for field: {field}'}), 400
            setattr(user, field, value)
            fields_changed.append(field)

    # Update admin-only fields
    if requester and requester.role == 'admin':
        for field, validator in ADMIN_ONLY_FIELDS.items():
            if field in data:
                value = data[field]
                if not validator(value):
                    return jsonify({'error': f'Invalid value for field: {field}'}), 400
                setattr(user, field, value)
                fields_changed.append(field)

    if 'password' in data and not user.is_ldap_user:
        password = data['password']

        # Validate password strength
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        user.set_password(password)
        fields_changed.append('password')
        # Audit log password change
        log_password_change(requester_id, user.id)

    db.session.commit()

    # Audit log user update
    if fields_changed:
        log_user_update(user.id, fields_changed)

    return jsonify(user.to_dict()), 200


@bp.route('/<user_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per hour")
def delete_user(user_id):
    """Delete a user (admin only)."""
    requester_id = get_jwt_identity()
    requester = User.query.get(requester_id)
    admin_check = _require_admin(requester)
    if admin_check:
        return admin_check

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.id == requester_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    # Save user info before deletion
    deleted_username = user.username
    deleted_user_id = user.id

    db.session.delete(user)
    db.session.commit()

    # Audit log user deletion
    log_user_delete(deleted_user_id, deleted_username)

    return jsonify({'message': 'User deleted'}), 200
