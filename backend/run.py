"""
Development server entry point.
"""
from app import create_app, socketio

app = create_app('development')

if __name__ == '__main__':
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
