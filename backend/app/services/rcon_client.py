"""
RCON Client - Communicate with Minecraft servers via RCON protocol.
"""
import socket
import struct
import time
from typing import Optional
from flask import current_app


class RCONClient:
    """Minecraft RCON client."""

    PACKET_AUTH = 3
    PACKET_COMMAND = 2
    PACKET_RESPONSE = 0
    PACKET_AUTH_RESPONSE = 2

    def __init__(self, host: str, port: int, password: str):
        """
        Initialize RCON client.

        Args:
            host: Server hostname or IP
            port: RCON port
            password: RCON password
        """
        self.host = host
        self.port = port
        self.password = password
        self.socket: Optional[socket.socket] = None
        self.request_id = 0

    def connect(self, timeout: int = 10) -> bool:
        """
        Connect to RCON server.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))

            # Authenticate
            return self._authenticate()

        except Exception as e:
            current_app.logger.error(f"RCON connection failed: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """Disconnect from RCON server."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    def _authenticate(self) -> bool:
        """Authenticate with RCON server."""
        self._send_packet(self.PACKET_AUTH, self.password)
        response_id, response_type, _ = self._receive_packet()

        if response_id == -1:
            current_app.logger.error("RCON authentication failed")
            return False

        return True

    def _send_packet(self, packet_type: int, payload: str):
        """Send RCON packet."""
        self.request_id = (self.request_id + 1) % 2147483648  # Keep within int32 range

        payload_bytes = payload.encode('utf-8')
        packet_size = len(payload_bytes) + 10

        packet = struct.pack('<iii', packet_size, self.request_id, packet_type)
        packet += payload_bytes
        packet += b'\x00\x00'

        self.socket.sendall(packet)

    def _receive_packet(self) -> tuple:
        """Receive RCON packet."""
        # Read packet size
        size_data = self._receive_bytes(4)
        packet_size = struct.unpack('<i', size_data)[0]

        # Read packet data
        packet_data = self._receive_bytes(packet_size)

        request_id, response_type = struct.unpack('<ii', packet_data[:8])
        payload = packet_data[8:-2].decode('utf-8', errors='ignore')

        return request_id, response_type, payload

    def _receive_bytes(self, length: int) -> bytes:
        """Receive exact number of bytes."""
        data = b''
        while len(data) < length:
            chunk = self.socket.recv(length - len(data))
            if not chunk:
                raise ConnectionError("Connection closed by server")
            data += chunk
        return data

    def send_command(self, command: str) -> Optional[str]:
        """
        Send command to server.

        Args:
            command: Minecraft command (without leading /)

        Returns:
            Command response or None if failed
        """
        if not self.socket:
            if not self.connect():
                return None

        try:
            self._send_packet(self.PACKET_COMMAND, command)
            _, _, response = self._receive_packet()
            return response
        except Exception as e:
            current_app.logger.error(f"RCON command failed: {e}")
            self.disconnect()
            return None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Helper functions for common commands

def execute_rcon_command(host: str, port: int, password: str, command: str) -> Optional[str]:
    """
    Execute a generic RCON command.

    Args:
        host: Server hostname or IP
        port: RCON port
        password: RCON password
        command: Command to execute

    Returns:
        Command response or None if failed
    """
    with RCONClient(host, port, password) as rcon:
        return rcon.send_command(command)


def get_online_players(host: str, port: int, password: str) -> Optional[list]:
    """Get list of online players."""
    with RCONClient(host, port, password) as rcon:
        response = rcon.send_command('list')
        if response:
            # Parse response: "There are X of a max of Y players online: player1, player2"
            if 'players online:' in response:
                players_str = response.split('players online:')[1].strip()
                if players_str:
                    return [p.strip() for p in players_str.split(',')]
            return []
        return None


def kick_player(host: str, port: int, password: str, player_name: str, reason: str = "") -> bool:
    """Kick a player."""
    with RCONClient(host, port, password) as rcon:
        command = f"kick {player_name}"
        if reason:
            command += f" {reason}"
        response = rcon.send_command(command)
        return response is not None and "Kicked" in response


def ban_player(host: str, port: int, password: str, player_name: str, reason: str = "") -> bool:
    """Ban a player."""
    with RCONClient(host, port, password) as rcon:
        command = f"ban {player_name}"
        if reason:
            command += f" {reason}"
        response = rcon.send_command(command)
        return response is not None


def unban_player(host: str, port: int, password: str, player_name: str) -> bool:
    """Unban a player."""
    with RCONClient(host, port, password) as rcon:
        response = rcon.send_command(f"pardon {player_name}")
        return response is not None


def broadcast_message(host: str, port: int, password: str, message: str) -> bool:
    """Broadcast message to all players."""
    with RCONClient(host, port, password) as rcon:
        response = rcon.send_command(f"say {message}")
        return response is not None


def save_world(host: str, port: int, password: str) -> bool:
    """Force save world."""
    with RCONClient(host, port, password) as rcon:
        response = rcon.send_command("save-all")
        return response is not None and "Saved" in response
