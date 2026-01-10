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
        from app.utils.security import validate_download_url

        file_path = None
        try:
            server = Server.query.get(server_id)
            if not server:
                current_app.logger.error(f"Server {server_id} not found for mod download")
                return

            # Validate URL to prevent SSRF (defense in depth)
            is_valid, error_msg = validate_download_url(mod_url)
            if not is_valid:
                current_app.logger.error(f"SSRF attempt in async download blocked: {mod_url} - {error_msg}")
                return

            # Download file
            response = requests.get(
                mod_url,
                stream=True,
                timeout=300,
                headers={'User-Agent': 'MineCP/1.0'},
            )
            response.raise_for_status()

            # Validate Content-Type (security: prevent downloading non-JAR files)
            content_type = response.headers.get('Content-Type', '').lower()
            allowed_types = [
                'application/java-archive',
                'application/zip',
                'application/octet-stream',
                'application/x-java-archive',
            ]
            if content_type and not any(allowed in content_type for allowed in allowed_types):
                current_app.logger.warning(f"Invalid content type for mod download: {content_type}")
                return

            # Validate Content-Length before download (security: prevent huge downloads)
            content_length = response.headers.get('Content-Length')
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 524288000)  # 500MB default
            if content_length and int(content_length) > max_size:
                current_app.logger.warning(f"File too large: {content_length} bytes (max: {max_size})")
                return

            # Save to server mods directory
            data_dir = current_app.config['MC_SERVER_DATA_DIR'] / server_id / 'data'
            if server.type and server.type.lower() in {'paper', 'spigot', 'purpur'}:
                mods_dir = data_dir / 'plugins'
            else:
                mods_dir = data_dir / 'mods'
            mods_dir.mkdir(parents=True, exist_ok=True)

            file_path = mods_dir / f"{mod_name}.jar"

            # Track downloaded size during streaming (defense-in-depth)
            downloaded_size = 0
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 524288000)

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    downloaded_size += len(chunk)
                    if downloaded_size > max_size:
                        current_app.logger.warning(f"Download exceeded max size: {downloaded_size} bytes")
                        if file_path.exists():
                            file_path.unlink()
                        return
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
    Includes ZIP bomb protection.

    Args:
        file_path: Path to the file to validate

    Returns:
        True if valid, False otherwise
    """
    import zipfile
    from pathlib import Path
    from flask import current_app

    file_path = Path(file_path)

    # Check file exists and has reasonable size
    if not file_path.exists():
        return False

    # Check minimum file size (1 KB)
    if file_path.stat().st_size < 1024:
        return False

    # ZIP bomb protection constants
    MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_COMPRESSION_RATIO = 100  # Flag if compression ratio > 100:1

    # Try to open as ZIP file
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Check total uncompressed size (ZIP bomb protection)
            total_size = sum(info.file_size for info in zip_file.infolist())
            if total_size > MAX_UNCOMPRESSED_SIZE:
                current_app.logger.warning(f"ZIP bomb detected: uncompressed size {total_size} bytes")
                return False

            # Check compression ratio for individual files (ZIP bomb protection)
            for info in zip_file.infolist():
                if info.compress_size > 0:
                    ratio = info.file_size / info.compress_size
                    if ratio > MAX_COMPRESSION_RATIO:
                        current_app.logger.warning(f"ZIP bomb detected: compression ratio {ratio:.1f}:1")
                        return False

            # Test the ZIP file integrity
            bad_file = zip_file.testzip()
            return bad_file is None
    except (zipfile.BadZipFile, OSError, Exception):
        return False
