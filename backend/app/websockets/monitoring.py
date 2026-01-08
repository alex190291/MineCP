"""
WebSocket handlers for real-time monitoring.
"""
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app.extensions import socketio
from app.models.server import Server


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    try:
        verify_jwt_in_request()
        get_jwt_identity()
        emit('connected', {'message': 'Connected to monitoring'})
    except Exception:
        return False


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    pass


@socketio.on('subscribe_server')
def handle_subscribe_server(data):
    """Subscribe to server updates."""
    try:
        verify_jwt_in_request()
        server_id = data.get('server_id') if data else None

        if not server_id:
            emit('error', {'message': 'server_id required'})
            return

        server = Server.query.get(server_id)
        if not server:
            emit('error', {'message': 'Server not found'})
            return

        join_room(f'server_{server_id}')
        emit('subscribed', {'server_id': server_id})

    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('unsubscribe_server')
def handle_unsubscribe_server(data):
    """Unsubscribe from server updates."""
    server_id = data.get('server_id') if data else None
    if server_id:
        leave_room(f'server_{server_id}')
        emit('unsubscribed', {'server_id': server_id})


def broadcast_server_metrics(server_id, metrics):
    """Broadcast metrics to all clients subscribed to this server."""
    socketio.emit('server_metrics', {
        'server_id': server_id,
        'metrics': metrics
    }, room=f'server_{server_id}')


def broadcast_server_status(server_id, status):
    """Broadcast status change."""
    socketio.emit('server_status', {
        'server_id': server_id,
        'status': status
    }, room=f'server_{server_id}')
