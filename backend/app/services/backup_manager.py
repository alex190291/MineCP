"""
Backup manager for server backups.
"""
import tarfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from flask import current_app

from app.services.rcon_client import RCONClient


class BackupManager:
    """Manage server backups."""

    def __init__(self):
        """Initialize backup manager."""
        self.backup_dir = current_app.config['MC_BACKUP_DIR']

    def create_backup(self, server_id: str, server_name: str,
                     rcon_host: str, rcon_port: int, rcon_password: str,
                     backup_name: Optional[str] = None) -> Optional[Path]:
        """
        Create a backup of a server.

        Args:
            server_id: Server ID
            server_name: Server name
            rcon_host: RCON host
            rcon_port: RCON port
            rcon_password: RCON password
            backup_name: Custom backup name

        Returns:
            Path to backup file
        """
        try:
            # Pause world saving
            with RCONClient(rcon_host, rcon_port, rcon_password) as rcon:
                rcon.send_command("save-off")
                rcon.send_command("save-all flush")

            # Wait for save to complete
            import time
            time.sleep(2)

            # Create backup
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_name = backup_name or f"{server_name}_{timestamp}"

            server_data_dir = current_app.config['MC_SERVER_DATA_DIR'] / server_id / 'data'
            backup_path = self.backup_dir / server_id / f"{backup_name}.tar.gz"
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Create tar.gz
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(server_data_dir, arcname='.')

            # Resume world saving
            with RCONClient(rcon_host, rcon_port, rcon_password) as rcon:
                rcon.send_command("save-on")

            current_app.logger.info(f"Backup created: {backup_path}")
            return backup_path

        except Exception as e:
            current_app.logger.error(f"Backup failed: {e}")
            # Ensure saving is re-enabled
            try:
                with RCONClient(rcon_host, rcon_port, rcon_password) as rcon:
                    rcon.send_command("save-on")
            except:
                pass
            return None

    def restore_backup(self, server_id: str, backup_path: Path) -> bool:
        """
        Restore a server from backup.

        Args:
            server_id: Server ID
            backup_path: Path to backup file

        Returns:
            True if successful
        """
        try:
            server_data_dir = current_app.config['MC_SERVER_DATA_DIR'] / server_id / 'data'

            # Create safety backup of current state
            safety_backup = self.backup_dir / server_id / f"pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            safety_backup.parent.mkdir(parents=True, exist_ok=True)

            with tarfile.open(safety_backup, 'w:gz') as tar:
                tar.add(server_data_dir, arcname='.')

            # Clear current data
            shutil.rmtree(server_data_dir)
            server_data_dir.mkdir(parents=True, exist_ok=True)

            # Extract backup
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(server_data_dir)

            current_app.logger.info(f"Backup restored: {backup_path}")
            return True

        except Exception as e:
            current_app.logger.error(f"Restore failed: {e}")
            return False

    def delete_backup(self, backup_path: Path) -> bool:
        """Delete a backup file."""
        try:
            backup_path.unlink()
            current_app.logger.info(f"Backup deleted: {backup_path}")
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to delete backup: {e}")
            return False

    def list_backups(self, server_id: str) -> list:
        """List all backups for a server."""
        backup_dir = self.backup_dir / server_id
        if not backup_dir.exists():
            return []

        backups = []
        for backup_file in backup_dir.glob('*.tar.gz'):
            stat = backup_file.stat()
            backups.append({
                'name': backup_file.stem,
                'path': str(backup_file),
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat()
            })

        return sorted(backups, key=lambda x: x['created_at'], reverse=True)
