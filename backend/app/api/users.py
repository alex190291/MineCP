"""
User management API endpoints.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User

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
def create_user():
    """Create a user (admin only)."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    admin_check = _require_admin(current_user)
    if admin_check:
        return admin_check

    data = request.get_json() or {}
    required = ['username', 'email', 'role']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

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

    if not user.is_ldap_user:
        password = data.get('password')
        if not password:
            return jsonify({'error': 'Password required for non-LDAP user'}), 400
        user.set_password(password)

    db.session.add(user)
    db.session.commit()

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

    for field in ['username', 'email', 'is_active']:
        if field in data:
            setattr(user, field, data[field])

    if requester and requester.role == 'admin':
        if 'role' in data:
            user.role = data['role']
        if 'is_ldap_user' in data:
            user.is_ldap_user = data['is_ldap_user']

    if 'password' in data and not user.is_ldap_user:
        user.set_password(data['password'])

    db.session.commit()
    return jsonify(user.to_dict()), 200


@bp.route('/<user_id>', methods=['DELETE'])
@jwt_required()
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

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200
