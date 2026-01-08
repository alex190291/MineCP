"""
Background tasks for server operations.
"""
import time
from flask import current_app
from app.extensions import db
from app.models.server import Server
from app.services.docker_manager import DockerManager
from app.background.task_queue import async_task


@async_task
def deploy_server_async(server_id: str):
    """
    Deploy a Minecraft server asynchronously.

    Args:
        server_id: Server ID to deploy
    """
    from app import create_app
    app = create_app()

    with app.app_context():
        server = Server.query.get(server_id)
        if not server:
            current_app.logger.error(f"Server {server_id} not found")
            return

        try:
            # Update status
            server.status = 'starting'
            db.session.commit()

            # Create Docker container
            docker_manager = DockerManager()
            container = docker_manager.create_server(
                server_id=server.id,
                server_type=server.type,
                version=server.version,
                memory_limit=server.memory_limit,
                cpu_limit=server.cpu_limit,
                host_port=server.host_port,
                rcon_password=server.rcon_password,
                server_properties=server.server_properties or {},
                java_args=server.java_args
            )

            # Update server record
            server.container_id = container.id
            server.status = 'running'
            db.session.commit()

            current_app.logger.info(f"Server {server_id} deployed successfully")

        except Exception as e:
            current_app.logger.error(f"Server deployment failed: {e}")
            server.status = 'error'
            db.session.commit()


@async_task
def download_mod_async(server_id: str, mod_url: str, mod_name: str):
    """
    Download a mod file asynchronously.

    Args:
        server_id: Server ID
        mod_url: URL to download mod from
        mod_name: Name of the mod
    """
    import requests
    import zipfile
    from pathlib import Path
    from app import create_app
    from app.models.server_mod import ServerMod

    app = create_app()

    with app.app_context():
        file_path = None
        try:
            # Download file
            response = requests.get(mod_url, stream=True, timeout=300)
            response.raise_for_status()

            # Save to server mods directory
            mods_dir = current_app.config['MC_SERVER_DATA_DIR'] / server_id / 'data' / 'mods'
            mods_dir.mkdir(parents=True, exist_ok=True)

            file_path = mods_dir / f"{mod_name}.jar"

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Validate the downloaded JAR file
            if not _validate_jar_file(file_path):
                current_app.logger.error(f"Downloaded file is not a valid JAR: {file_path}")
                # Delete corrupted file
                if file_path.exists():
                    file_path.unlink()
                # Mark mod as failed in database
                mod = ServerMod.query.filter_by(server_id=server_id, name=mod_name).first()
                if mod:
                    db.session.delete(mod)
                    db.session.commit()
                return

            current_app.logger.info(f"Mod {mod_name} downloaded and validated for server {server_id}")

        except Exception as e:
            current_app.logger.error(f"Mod download failed: {e}")
            # Clean up corrupted file if it exists
            if file_path and file_path.exists():
                file_path.unlink()
            # Remove from database
            mod = ServerMod.query.filter_by(server_id=server_id, name=mod_name).first()
            if mod:
                db.session.delete(mod)
                db.session.commit()


def _validate_jar_file(file_path) -> bool:
    """
    Validate that a file is a valid JAR (ZIP) file.

    Args:
        file_path: Path to the file to validate

    Returns:
        True if valid, False otherwise
    """
    import zipfile
    from pathlib import Path

    file_path = Path(file_path)

    # Check file exists and has reasonable size
    if not file_path.exists():
        return False

    # Check minimum file size (1 KB)
    if file_path.stat().st_size < 1024:
        return False

    # Try to open as ZIP file
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Test the ZIP file integrity
            bad_file = zip_file.testzip()
            return bad_file is None
    except (zipfile.BadZipFile, OSError, Exception):
        return False
