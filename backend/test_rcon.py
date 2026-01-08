"""Test RCON client."""
import time
from app import create_app
from app.services.rcon_client import RCONClient

app = create_app()

with app.app_context():
    # Connect to a running server
    # NOTE: You need to have a running Minecraft server with RCON enabled
    # Update these values with your actual server details
    rcon = RCONClient('localhost', 25575, 'your-rcon-password')

    if rcon.connect():
        print("✓ RCON connected")

        # Test command
        response = rcon.send_command('list')
        print(f"✓ Command response: {response}")

        rcon.disconnect()
        print("✓ RCON disconnected")
    else:
        print("✗ RCON connection failed")
