"""
Server management API endpoints.
"""
import secrets
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db, limiter
from app.models.server import Server
from app.models.user import User
from app.services.docker_manager import DockerManager
from app.background.task_queue import get_task_queue
from app.background.server_tasks import deploy_server_async
from app.utils.audit import log_server_create, log_server_delete, log_server_start, log_server_stop

bp = Blueprint('servers', __name__)


def _find_available_rcon_port(start_port=25575, max_attempts=100):
    """
    Find an available RCON port by checking existing servers.

    Args:
        start_port: Starting port number
        max_attempts: Maximum number of ports to check

    Returns:
        Available port number
    """
    for offset in range(max_attempts):
        port = start_port + offset
        existing = Server.query.filter_by(rcon_port=port).first()
        if not existing:
            return port

    raise RuntimeError("No available RCON ports found")


@bp.route('', methods=['GET'])
@jwt_required()
def list_servers():
    """List all servers."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user and user.role == 'admin':
        servers = Server.query.all()
    else:
        servers = Server.query.filter_by(created_by=user_id).all()

    return jsonify([server.to_dict() for server in servers]), 200


@bp.route('', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def create_server():
    """Create a new server."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    required = ['name', 'type', 'version', 'memory_limit', 'cpu_limit', 'host_port']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    existing = Server.query.filter_by(host_port=data['host_port']).first()
    if existing:
        return jsonify({'error': 'Port already in use'}), 409

    rcon_password = secrets.token_urlsafe(16)
    rcon_port = _find_available_rcon_port()

    server = Server(
        name=data['name'],
        type=data['type'],
        version=data['version'],
        status='stopped',
        container_name=f"mc-server-{data['name'].lower().replace(' ', '-')}",
        host_port=data['host_port'],
        rcon_port=rcon_port,
        rcon_password=rcon_password,
        memory_limit=data['memory_limit'],
        cpu_limit=data['cpu_limit'],
        disk_limit=data.get('disk_limit'),
        java_args=data.get('java_args'),
        server_properties=data.get('server_properties', {}),
        created_by=user_id
    )

    db.session.add(server)
    db.session.commit()

    # Audit log server creation
    log_server_create(server.id, server.name)

    task_queue = get_task_queue()
    task_queue.submit(deploy_server_async, server.id)

    return jsonify(server.to_dict()), 202


@bp.route('/<server_id>', methods=['GET'])
@jwt_required()
def get_server(server_id):
    """Get server details."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    return jsonify(server.to_dict()), 200


@bp.route('/<server_id>', methods=['PATCH'])
@jwt_required()
@limiter.limit("30 per hour")
def update_server(server_id):
    """Update server configuration."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    if server.status not in ['stopped', 'error']:
        return jsonify({'error': 'Server must be stopped to update'}), 400

    data = request.get_json() or {}

    for field in ['name', 'memory_limit', 'cpu_limit', 'java_args', 'server_properties']:
        if field in data:
            setattr(server, field, data[field])

    server.updated_at = db.func.now()
    db.session.commit()

    return jsonify(server.to_dict()), 200


@bp.route('/<server_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per hour")
def delete_server(server_id):
    """Delete a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    # Audit log before deletion
    server_name = server.name
    server_id_for_log = server.id

    if server.container_id:
        docker_manager = DockerManager()
        docker_manager.delete_server(server.container_id, remove_volumes=True)

    db.session.delete(server)
    db.session.commit()

    # Audit log server deletion
    log_server_delete(server_id_for_log, server_name)

    return jsonify({'message': 'Server deleted'}), 200


@bp.route('/<server_id>/start', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def start_server(server_id):
    """Start a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    if server.status == 'running':
        return jsonify({'error': 'Server already running'}), 400

    docker_manager = DockerManager()

    if server.container_id:
        docker_manager.start_server(server.container_id)
        server.status = 'running'
    else:
        task_queue = get_task_queue()
        task_queue.submit(deploy_server_async, server.id)
        server.status = 'starting'

    db.session.commit()

    # Audit log server start
    log_server_start(server.id)

    return jsonify(server.to_dict()), 200


@bp.route('/<server_id>/stop', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def stop_server(server_id):
    """Stop a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    if server.status == 'stopped':
        return jsonify({'error': 'Server already stopped'}), 400

    if not server.container_id:
        return jsonify({'error': 'Server not deployed'}), 400

    docker_manager = DockerManager()
    docker_manager.stop_server(server.container_id)

    server.status = 'stopped'
    db.session.commit()

    # Audit log server stop
    log_server_stop(server.id)

    return jsonify(server.to_dict()), 200


@bp.route('/<server_id>/restart', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def restart_server(server_id):
    """Restart a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    if not server.container_id:
        return jsonify({'error': 'Server not deployed'}), 400

    docker_manager = DockerManager()
    docker_manager.restart_server(server.container_id)

    server.status = 'running'
    db.session.commit()

    return jsonify(server.to_dict()), 200


@bp.route('/<server_id>/logs', methods=['GET'])
@jwt_required()
def get_server_logs(server_id):
    """Get server logs."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    if not server.container_id:
        return jsonify({'error': 'Server not deployed'}), 404

    tail = request.args.get('tail', default=100, type=int)

    docker_manager = DockerManager()
    logs = docker_manager.get_container_logs(server.container_id, tail=tail)

    if logs:
        logs = '\n'.join(
            line for line in logs.splitlines()
            if 'Thread RCON Client' not in line
        )

    return jsonify({'logs': logs or ''}), 200


@bp.route('/<server_id>/command', methods=['POST'])
@jwt_required()
@limiter.limit("60 per minute")
def send_server_command(server_id):
    """Send a command to the server via RCON."""
    from app.services.rcon_client import execute_rcon_command

    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    if server.status != 'running':
        return jsonify({'error': 'Server not running'}), 400

    data = request.get_json() or {}
    command = data.get('command', '').strip()

    if not command:
        return jsonify({'error': 'Command required'}), 400

    # Execute command via RCON - get container IP
    from app.services.docker_manager import DockerManager
    docker_manager = DockerManager()
    rcon_host = docker_manager.get_container_ip(server.container_id) or 'localhost'

    result = execute_rcon_command(
        rcon_host,
        25575,  # Internal RCON port
        server.rcon_password or '',
        command
    )

    if result is None:
        return jsonify({'error': 'Failed to send command (RCON connection failed)'}), 500

    return jsonify({'result': result, 'command': command}), 200


@bp.route('/<server_id>/settings', methods=['GET'])
@jwt_required()
def get_server_settings(server_id):
    """Get server.properties as JSON."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    # Return server properties from database
    # These are stored as JSON and can be edited
    return jsonify(server.server_properties or {}), 200


@bp.route('/<server_id>/settings', methods=['PUT'])
@jwt_required()
@limiter.limit("30 per hour")
def update_server_settings(server_id):
    """Update server.properties."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}

    # Update server properties
    server.server_properties = data
    server.updated_at = db.func.now()
    db.session.commit()

    # If server is running, restart is required for changes to take effect
    restart_required = server.status == 'running'

    return jsonify({
        'settings': server.server_properties,
        'restart_required': restart_required
    }), 200
