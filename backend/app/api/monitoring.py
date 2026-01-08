"""
Monitoring API endpoints.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.server import Server
from app.models.user import User
from app.models.player import Player
from app.extensions import db
from datetime import datetime
from app.services.monitoring import get_metrics_collector
from app.services.rcon_client import get_online_players, execute_rcon_command
from app.services.docker_manager import DockerManager
from pathlib import Path
import json
import re

bp = Blueprint('monitoring', __name__)


def _get_rcon_host(server: Server) -> str:
    """Get RCON host for a server (container IP address)."""
    if not server.container_id:
        return 'localhost'

    docker_manager = DockerManager()
    container_ip = docker_manager.get_container_ip(server.container_id)
    if container_ip:
        return container_ip

    # Fallback to localhost if we can't get the IP
    return 'localhost'


def _get_ops_list(server_id: str) -> list:
    """Get list of OPs from ops.json file."""
    try:
        from flask import current_app
        server_data_dir = Path(current_app.config.get('MC_SERVER_DATA_DIR', '/data/servers'))
        ops_file = server_data_dir / server_id / 'data' / 'ops.json'

        if ops_file.exists():
            with open(ops_file, 'r') as f:
                ops_data = json.load(f)
                # ops.json format: [{"uuid": "...", "name": "PlayerName", "level": 4, ...}, ...]
                return [op.get('name') for op in ops_data if op.get('name')]
    except Exception as e:
        pass
    return []


@bp.route('/servers/<server_id>/metrics', methods=['GET'])
@jwt_required()
def get_server_metrics(server_id):
    """Get current metrics for a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    if server.status != 'running' or not server.container_id:
        return jsonify({'error': 'Server not running'}), 400

    metrics_collector = get_metrics_collector()
    metrics = metrics_collector.get_latest_metrics(server_id)

    if not metrics:
        return jsonify({'error': 'No metrics available'}), 404

    return jsonify(metrics), 200


@bp.route('/servers/<server_id>/metrics/history', methods=['GET'])
@jwt_required()
def get_server_metrics_history(server_id):
    """Get metrics history for a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    metrics_collector = get_metrics_collector()
    history = metrics_collector.get_recent_metrics(server_id, limit=60)

    return jsonify({'history': history}), 200


@bp.route('/servers/<server_id>/players', methods=['GET'])
@jwt_required()
def get_online_players_endpoint(server_id):
    """Get online players."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    if server.status != 'running':
        return jsonify({'players': []}), 200

    rcon_host = _get_rcon_host(server)
    players = get_online_players(
        rcon_host,
        25575,  # Internal RCON port
        server.rcon_password or ''
    )

    return jsonify({'players': players or []}), 200


@bp.route('/servers/<server_id>/players/all', methods=['GET'])
@jwt_required()
def get_all_players_endpoint(server_id):
    """Get all players who have ever connected to this server by parsing logs."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    # Get currently online players
    online_players = []
    if server.status == 'running' and server.container_id:
        rcon_host = _get_rcon_host(server)
        online_players = get_online_players(
            rcon_host,
            25575,  # Internal RCON port
            server.rcon_password or ''
        ) or []

    # Get list of OPs
    ops_list = _get_ops_list(server_id)

    # Parse recent logs to find new players and update database
    if server.container_id:
        try:
            docker_manager = DockerManager()
            # Get recent logs to capture new player joins
            logs = docker_manager.get_container_logs(server.container_id, tail=500)

            if logs:
                # Extract player info with UUIDs
                player_data = {}

                # Pattern to match: UUID of player Username is uuid-here
                uuid_pattern = r'UUID of player (\w+) is ([0-9a-f-]+)'
                join_pattern = r':\s*(\w+)\s+joined the game'

                for line in logs.split('\n'):
                    # Try to extract UUID
                    uuid_match = re.search(uuid_pattern, line)
                    if uuid_match:
                        username = uuid_match.group(1)
                        uuid = uuid_match.group(2)
                        if 3 <= len(username) <= 16:
                            player_data[username] = uuid

                    # Also look for join messages without UUIDs
                    join_match = re.search(join_pattern, line)
                    if join_match:
                        username = join_match.group(1)
                        if 3 <= len(username) <= 16:
                            if username.lower() not in ['server', 'thread', 'info', 'warn', 'error']:
                                if username not in player_data:
                                    player_data[username] = None

                # Update database with found players
                for username, uuid in player_data.items():
                    player = Player.query.filter_by(server_id=server_id, username=username).first()
                    if not player:
                        player = Player(
                            server_id=server_id,
                            username=username,
                            minecraft_uuid=uuid,
                            first_seen=datetime.utcnow()
                        )
                        db.session.add(player)
                    else:
                        # Update UUID if we found it and don't have it yet
                        if uuid and not player.minecraft_uuid:
                            player.minecraft_uuid = uuid
                    player.last_seen = datetime.utcnow()

                if player_data:
                    db.session.commit()
        except Exception as e:
            pass

    # Get all players from database
    db_players = Player.query.filter_by(server_id=server_id).all()

    # Build response
    players_data = []
    for player in db_players:
        players_data.append({
            'username': player.username,
            'minecraft_uuid': player.minecraft_uuid or '',
            'is_online': player.username in online_players,
            'first_seen': player.first_seen.isoformat() if player.first_seen else '',
            'last_seen': player.last_seen.isoformat() if player.last_seen else '',
            'is_banned': player.is_banned,
            'ban_reason': player.ban_reason,
            'is_op': player.username in ops_list,
        })

    # Add online players that aren't in the database yet
    for username in online_players:
        if not any(p['username'] == username for p in players_data):
            player = Player(
                server_id=server_id,
                username=username,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            db.session.add(player)
            players_data.append({
                'username': username,
                'minecraft_uuid': '',
                'is_online': True,
                'first_seen': player.first_seen.isoformat(),
                'last_seen': player.last_seen.isoformat(),
                'is_banned': False,
                'ban_reason': None,
                'is_op': username in ops_list,
            })

    db.session.commit()

    return jsonify({'players': sorted(players_data, key=lambda x: x['username'])}), 200


@bp.route('/servers/<server_id>/players/ban', methods=['POST'])
@jwt_required()
def ban_player(server_id):
    """Ban a player."""
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
    player_name = data.get('player_name')
    reason = data.get('reason', 'Banned by admin')

    if not player_name:
        return jsonify({'error': 'player_name required'}), 400

    rcon_host = _get_rcon_host(server)
    command = f"ban {player_name} {reason}"
    result = execute_rcon_command(
        rcon_host,
        25575,  # Internal RCON port
        server.rcon_password or '',
        command
    )

    if result is None:
        return jsonify({'error': 'Failed to execute ban command'}), 500

    # Update player in database
    player = Player.query.filter_by(server_id=server_id, username=player_name).first()
    if player:
        player.is_banned = True
        player.ban_reason = reason
        db.session.commit()

    return jsonify({'message': f'Player {player_name} banned', 'result': result}), 200


@bp.route('/servers/<server_id>/players/unban', methods=['POST'])
@jwt_required()
def unban_player(server_id):
    """Unban a player."""
    from flask import current_app

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
    player_name = data.get('player_name')

    if not player_name:
        return jsonify({'error': 'player_name required'}), 400

    try:
        rcon_host = _get_rcon_host(server)
        current_app.logger.info(f"Unbanning player {player_name} on server {server_id}, RCON host: {rcon_host}")

        command = f"pardon {player_name}"
        result = execute_rcon_command(
            rcon_host,
            25575,  # Internal RCON port
            server.rcon_password or '',
            command
        )

        current_app.logger.info(f"RCON result for unban: {result}")

        if result is None:
            current_app.logger.error(f"Failed to execute unban command for {player_name}")
            return jsonify({'error': 'Failed to execute unban command - RCON connection failed'}), 500

        # Update player in database
        player = Player.query.filter_by(server_id=server_id, username=player_name).first()
        if player:
            player.is_banned = False
            player.ban_reason = None
            db.session.commit()
            current_app.logger.info(f"Updated database: {player_name} is_banned=False")
        else:
            current_app.logger.warning(f"Player {player_name} not found in database")

        return jsonify({'message': f'Player {player_name} unbanned', 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Exception during unban: {e}")
        return jsonify({'error': f'Unban failed: {str(e)}'}), 500


@bp.route('/servers/<server_id>/players/op', methods=['POST'])
@jwt_required()
def op_player(server_id):
    """Give operator privileges to a player."""
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
    player_name = data.get('player_name')

    if not player_name:
        return jsonify({'error': 'player_name required'}), 400

    rcon_host = _get_rcon_host(server)
    command = f"op {player_name}"
    result = execute_rcon_command(
        rcon_host,
        25575,  # Internal RCON port
        server.rcon_password or '',
        command
    )

    if result is None:
        return jsonify({'error': 'Failed to execute OP command'}), 500

    return jsonify({'message': f'Player {player_name} given OP', 'result': result}), 200


@bp.route('/servers/<server_id>/players/deop', methods=['POST'])
@jwt_required()
def deop_player(server_id):
    """Remove operator privileges from a player."""
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
    player_name = data.get('player_name')

    if not player_name:
        return jsonify({'error': 'player_name required'}), 400

    rcon_host = _get_rcon_host(server)
    command = f"deop {player_name}"
    result = execute_rcon_command(
        rcon_host,
        25575,  # Internal RCON port
        server.rcon_password or '',
        command
    )

    if result is None:
        return jsonify({'error': 'Failed to execute De-OP command'}), 500

    return jsonify({'message': f'Player {player_name} deoped', 'result': result}), 200


@bp.route('/servers/<server_id>/players/kick', methods=['POST'])
@jwt_required()
def kick_player(server_id):
    """Kick a player."""
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
    player_name = data.get('player_name')
    reason = data.get('reason', 'Kicked by admin')

    if not player_name:
        return jsonify({'error': 'player_name required'}), 400

    rcon_host = _get_rcon_host(server)
    command = f"kick {player_name} {reason}"
    result = execute_rcon_command(
        rcon_host,
        25575,  # Internal RCON port
        server.rcon_password or '',
        command
    )

    if result is None:
        return jsonify({'error': 'Failed to execute kick command'}), 500

    return jsonify({'message': f'Player {player_name} kicked', 'result': result}), 200


@bp.route('/servers/<server_id>/players/banned', methods=['GET'])
@jwt_required()
def get_banned_players(server_id):
    """Get list of banned players."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    if user and user.role != 'admin' and server.created_by != user_id:
        return jsonify({'error': 'Forbidden'}), 403

    if server.status != 'running':
        return jsonify({'banned_players': []}), 200

    # Get ban list using RCON command
    rcon_host = _get_rcon_host(server)
    command = "banlist"
    result = execute_rcon_command(
        rcon_host,
        25575,  # Internal RCON port
        server.rcon_password or '',
        command
    )

    # Parse the banlist result
    # Format: "There are X ban(s):PlayerName1 was banned by Rcon: reasonPlayerName2 was banned by Rcon: reason"
    # Note: entries are concatenated without separators
    # or "There are no bans"
    banned_players = []
    if result:
        if 'no bans' not in result.lower():
            # Pattern: Find all instances of capital letter followed by name, then " was banned by"
            # This handles concatenated entries like "...Test banPlayerName was banned..."
            pattern = r'([A-Z]\w{2,15})\s+was banned by'
            matches = re.findall(pattern, result)
            # Filter out duplicates
            banned_players = list(dict.fromkeys(matches))

    return jsonify({'banned_players': banned_players}), 200
