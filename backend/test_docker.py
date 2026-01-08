"""Test Docker manager."""
from app import create_app
from app.services.docker_manager import DockerManager

app = create_app()

with app.app_context():
    docker_manager = DockerManager()

    # Test network creation
    docker_manager.ensure_network()
    print("✓ Network created/verified")

    # Test container creation
    container = docker_manager.create_server(
        server_id='test-server-001',
        server_type='paper',
        version='1.20.4',
        memory_limit=2048,
        cpu_limit=2.0,
        host_port=25565,
        rcon_password='test-password-123',
        server_properties={'max_players': 10}
    )
    print(f"✓ Container created: {container.id}")

    # Wait for container to start
    import time
    time.sleep(10)

    # Test stats
    stats = docker_manager.get_stats(container.id)
    print(f"✓ Stats: CPU={stats['cpu_percent']}%, Memory={stats['memory_percent']}%")

    # Test logs
    logs = docker_manager.get_container_logs(container.id, tail=10)
    print(f"✓ Logs retrieved: {len(logs)} bytes")

    # Cleanup
    docker_manager.delete_server(container.id)
    print("✓ Container deleted")
