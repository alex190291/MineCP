"""
File management API endpoints for server files.
"""
import os
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.extensions import db, limiter
from app.models.server import Server
from app.models.user import User
from app.utils.decorators import limit_content_length
from app.utils.permissions import user_has_server_permission

bp = Blueprint('files', __name__)


def _get_server_data_path(server_id: str) -> Path:
    """Get the data directory path for a server."""
    base_path = current_app.config.get('MC_SERVER_DATA_DIR', Path('/data/minecraft/servers'))
    return Path(base_path) / server_id / 'data'


def _is_safe_path(base_path: Path, requested_path: Path) -> bool:
    """Check if requested path is within the base path (prevent directory traversal)."""
    try:
        resolved_base = base_path.resolve()
        resolved_requested = requested_path.resolve()
        return resolved_requested.is_relative_to(resolved_base)
    except (ValueError, RuntimeError):
        return False


def _require_server_access(user, server):
    """Check if user has access to server."""
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if not user or not user_has_server_permission(user, server, 'server.files.view'):
        return jsonify({'error': 'Forbidden'}), 403

    return None


@bp.route('/servers/<server_id>/files', methods=['GET'])
@jwt_required()
def list_files(server_id):
    """
    List files and directories in server's data directory.

    Query params:
        path: Relative path within server directory (default: '')
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    base_path = _get_server_data_path(server_id)
    relative_path = request.args.get('path', '')

    # Construct requested path
    if relative_path:
        requested_path = base_path / relative_path
    else:
        requested_path = base_path

    # Security check: prevent directory traversal
    if not _is_safe_path(base_path, requested_path):
        return jsonify({'error': 'Invalid path'}), 400

    if not requested_path.exists():
        return jsonify({'error': 'Path not found'}), 404

    if not requested_path.is_dir():
        return jsonify({'error': 'Path is not a directory'}), 400

    # List directory contents
    items = []
    try:
        for item in sorted(requested_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            relative_item_path = item.relative_to(base_path)

            item_data = {
                'name': item.name,
                'path': str(relative_item_path),
                'type': 'directory' if item.is_dir() else 'file',
                'size': item.stat().st_size if item.is_file() else 0,
                'modified': item.stat().st_mtime,
            }

            # Add file extension for files
            if item.is_file():
                item_data['extension'] = item.suffix.lstrip('.')

            items.append(item_data)

    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403

    return jsonify({
        'path': relative_path,
        'items': items
    }), 200


@bp.route('/servers/<server_id>/files/read', methods=['GET'])
@jwt_required()
def read_file(server_id):
    """
    Read a file's contents.

    Query params:
        path: Relative path to file
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    base_path = _get_server_data_path(server_id)
    relative_path = request.args.get('path', '')

    if not relative_path:
        return jsonify({'error': 'Path required'}), 400

    file_path = base_path / relative_path

    # Security check
    if not _is_safe_path(base_path, file_path):
        return jsonify({'error': 'Invalid path'}), 400

    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404

    if not file_path.is_file():
        return jsonify({'error': 'Path is not a file'}), 400

    # Check file size (don't read files > 10MB)
    file_size = file_path.stat().st_size
    if file_size > 10 * 1024 * 1024:
        return jsonify({'error': 'File too large to read (max 10MB)'}), 400

    try:
        # Try to read as text
        content = file_path.read_text(encoding='utf-8')
        return jsonify({
            'path': relative_path,
            'content': content,
            'size': file_size,
            'encoding': 'utf-8'
        }), 200
    except UnicodeDecodeError:
        # Binary file
        return jsonify({'error': 'Cannot read binary file'}), 400


@bp.route('/servers/<server_id>/files/write', methods=['POST'])
@jwt_required()
@limiter.limit("60 per hour")
@limit_content_length(10 * 1024 * 1024)  # 10MB for config file writes
def write_file(server_id):
    """
    Write content to a file.

    Body:
        path: Relative path to file
        content: File content
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    if not user_has_server_permission(user, server, 'server.files.manage'):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    relative_path = data.get('path', '')
    content = data.get('content', '')

    if not relative_path:
        return jsonify({'error': 'Path required'}), 400

    base_path = _get_server_data_path(server_id)
    file_path = base_path / relative_path

    # Security check
    if not _is_safe_path(base_path, file_path):
        return jsonify({'error': 'Invalid path'}), 400

    # Create parent directories if needed
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        file_path.write_text(content, encoding='utf-8')
        return jsonify({
            'message': 'File saved',
            'path': relative_path,
            'size': file_path.stat().st_size
        }), 200
    except Exception as e:
        current_app.logger.error(f'Failed to write file: {e}')
        return jsonify({'error': 'Failed to write file'}), 500


@bp.route('/servers/<server_id>/files/delete', methods=['DELETE'])
@jwt_required()
@limiter.limit("60 per hour")
def delete_file(server_id):
    """
    Delete a file or directory.

    Body:
        path: Relative path to file/directory
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    if not user_has_server_permission(user, server, 'server.files.manage'):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    relative_path = data.get('path', '')

    if not relative_path:
        return jsonify({'error': 'Path required'}), 400

    base_path = _get_server_data_path(server_id)
    target_path = base_path / relative_path

    # Security check
    if not _is_safe_path(base_path, target_path):
        return jsonify({'error': 'Invalid path'}), 400

    if not target_path.exists():
        return jsonify({'error': 'Path not found'}), 404

    # Prevent deleting critical files
    critical_files = ['server.properties', 'eula.txt']
    if target_path.name in critical_files:
        return jsonify({'error': f'Cannot delete critical file: {target_path.name}'}), 400

    try:
        if target_path.is_file():
            target_path.unlink()
        elif target_path.is_dir():
            import shutil
            shutil.rmtree(target_path)

        return jsonify({'message': 'Deleted successfully', 'path': relative_path}), 200
    except Exception as e:
        current_app.logger.error(f'Failed to delete: {e}')
        return jsonify({'error': 'Failed to delete'}), 500


@bp.route('/servers/<server_id>/files/upload', methods=['POST'])
@jwt_required()
@limiter.limit("30 per hour")
@limit_content_length(100 * 1024 * 1024)  # 100MB for file uploads
def upload_file(server_id):
    """
    Upload a file to server directory.

    Form data:
        file: File to upload
        path: Target directory path (optional, defaults to root)
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    if not user_has_server_permission(user, server, 'server.files.manage'):
        return jsonify({'error': 'Forbidden'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file extension (whitelist approach)
    filename = secure_filename(file.filename)
    allowed_extensions = {
        # Config files
        '.properties', '.yml', '.yaml', '.json', '.toml', '.conf', '.cfg',
        # Text files
        '.txt', '.log',
        # Java/Minecraft files
        '.jar',
        # World/data files
        '.dat', '.mca', '.mcr',
        # Other common files
        '.png', '.jpg', '.jpeg'
    }

    file_ext = Path(filename).suffix.lower()
    if file_ext not in allowed_extensions:
        return jsonify({
            'error': f'File type not allowed: {file_ext}',
            'allowed_types': list(allowed_extensions)
        }), 400

    # Get target directory
    relative_path = request.form.get('path', '')
    base_path = _get_server_data_path(server_id)

    if relative_path:
        target_dir = base_path / relative_path
    else:
        target_dir = base_path

    # Security check
    if not _is_safe_path(base_path, target_dir):
        return jsonify({'error': 'Invalid path'}), 400

    # Secure filename
    filename = secure_filename(file.filename)
    target_path = target_dir / filename

    # Create directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        file.save(str(target_path))
        return jsonify({
            'message': 'File uploaded',
            'filename': filename,
            'path': str(target_path.relative_to(base_path)),
            'size': target_path.stat().st_size
        }), 200
    except Exception as e:
        current_app.logger.error(f'Failed to upload file: {e}')
        return jsonify({'error': 'Failed to upload file'}), 500


@bp.route('/servers/<server_id>/files/download', methods=['GET'])
@jwt_required()
def download_file(server_id):
    """
    Download a file.

    Query params:
        path: Relative path to file
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    base_path = _get_server_data_path(server_id)
    relative_path = request.args.get('path', '')

    if not relative_path:
        return jsonify({'error': 'Path required'}), 400

    file_path = base_path / relative_path

    # Security check
    if not _is_safe_path(base_path, file_path):
        return jsonify({'error': 'Invalid path'}), 400

    if not file_path.exists() or not file_path.is_file():
        return jsonify({'error': 'File not found'}), 404

    try:
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=file_path.name
        )
    except Exception as e:
        current_app.logger.error(f'Failed to download file: {e}')
        return jsonify({'error': 'Failed to download file'}), 500
