"""
Backup management API endpoints.
"""
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db, limiter
from app.models.backup import Backup
from app.models.server import Server
from app.models.user import User
from app.services.backup_manager import BackupManager
from app.utils.permissions import user_has_server_permission, get_accessible_servers

bp = Blueprint('backups', __name__)

def _require_server_access(user: User, server: Server):
    if not server:
        return jsonify({'error': 'Server not found'}), 404
    if not user:
        return jsonify({'error': 'Forbidden'}), 403
    if not user_has_server_permission(user, server, 'server.backups.view'):
        return jsonify({'error': 'Forbidden'}), 403
    return None


@bp.route('/backups', methods=['GET'])
@jwt_required()
def list_backups():
    """List all backups."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'Forbidden'}), 403

    if user.role == 'admin':
        backups = Backup.query.all()
    else:
        servers = get_accessible_servers(user, 'server.backups.view')
        server_ids = [server.id for server in servers]
        backups = Backup.query.filter(Backup.server_id.in_(server_ids)).all()

    return jsonify([backup.to_dict() for backup in backups]), 200


@bp.route('/servers/<server_id>/backups', methods=['GET'])
@jwt_required()
def list_server_backups(server_id):
    """List backups for a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    backups = Backup.query.filter_by(server_id=server_id).all()
    return jsonify([backup.to_dict() for backup in backups]), 200


@bp.route('/servers/<server_id>/backups', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def create_backup(server_id):
    """Create a backup for a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    if not user_has_server_permission(user, server, 'server.backups.manage'):
        return jsonify({'error': 'Forbidden'}), 403

    if server.status != 'running':
        return jsonify({'error': 'Server must be running to create a backup'}), 400

    data = request.get_json() or {}
    backup_name = data.get('name')

    # Get container IP for RCON
    from app.services.docker_manager import DockerManager
    docker_manager = DockerManager()
    rcon_host = docker_manager.get_container_ip(server.container_id) or 'localhost'

    backup_manager = BackupManager()
    backup_path = backup_manager.create_backup(
        server_id=server.id,
        server_name=server.name,
        rcon_host=rcon_host,
        rcon_port=25575,  # Internal RCON port
        rcon_password=server.rcon_password or '',
        backup_name=backup_name
    )

    if not backup_path:
        return jsonify({'error': 'Backup failed'}), 500

    backup_path = Path(backup_path)
    backup = Backup(
        server_id=server.id,
        name=backup_path.stem,
        size=backup_path.stat().st_size,
        backup_path=str(backup_path),
        type='manual',
        compressed=True,
        created_by=user_id
    )

    db.session.add(backup)
    db.session.commit()

    return jsonify(backup.to_dict()), 201


@bp.route('/backups/<backup_id>/restore', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def restore_backup(backup_id):
    """Restore a backup."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    backup = Backup.query.get(backup_id)
    if not backup:
        return jsonify({'error': 'Backup not found'}), 404

    server = Server.query.get(backup.server_id)
    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    if not user_has_server_permission(user, server, 'server.backups.manage'):
        return jsonify({'error': 'Forbidden'}), 403

    if server.status == 'running':
        return jsonify({'error': 'Stop the server before restoring a backup'}), 400

    backup_manager = BackupManager()
    success = backup_manager.restore_backup(server.id, Path(backup.backup_path))

    if not success:
        return jsonify({'error': 'Restore failed'}), 500

    return jsonify({'message': 'Backup restored'}), 200


@bp.route('/backups/<backup_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("20 per hour")
def delete_backup(backup_id):
    """Delete a backup."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    backup = Backup.query.get(backup_id)
    if not backup:
        return jsonify({'error': 'Backup not found'}), 404

    server = Server.query.get(backup.server_id)
    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    if not user_has_server_permission(user, server, 'server.backups.manage'):
        return jsonify({'error': 'Forbidden'}), 403

    backup_manager = BackupManager()
    backup_manager.delete_backup(Path(backup.backup_path))

    db.session.delete(backup)
    db.session.commit()

    return jsonify({'message': 'Backup deleted'}), 200


@bp.route('/backups/<backup_id>/download', methods=['GET'])
@jwt_required()
def download_backup(backup_id):
    """Download a backup file."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    backup = Backup.query.get(backup_id)
    if not backup:
        return jsonify({'error': 'Backup not found'}), 404

    server = Server.query.get(backup.server_id)
    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    backup_path = Path(backup.backup_path)
    if not backup_path.exists():
        return jsonify({'error': 'Backup file not found on disk'}), 404

    return send_file(
        backup_path,
        as_attachment=True,
        download_name=backup_path.name,
        mimetype='application/zip'
    )
