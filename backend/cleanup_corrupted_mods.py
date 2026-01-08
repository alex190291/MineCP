#!/usr/bin/env python3
"""
Script to find and remove corrupted JAR files from server mods directories.
"""
import sys
import zipfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.extensions import db
from app.models.server import Server
from app.models.server_mod import ServerMod


def validate_jar_file(file_path: Path) -> bool:
    """Check if a JAR file is valid."""
    if not file_path.exists():
        return False

    if file_path.stat().st_size < 1024:
        return False

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            bad_file = zip_file.testzip()
            return bad_file is None
    except (zipfile.BadZipFile, OSError, Exception):
        return False


def cleanup_corrupted_mods():
    """Find and remove corrupted mod files."""
    app = create_app()

    with app.app_context():
        servers = Server.query.all()
        total_corrupted = 0
        total_cleaned = 0

        for server in servers:
            print(f"\nChecking server: {server.name} ({server.id})")

            mods_dir = Path(app.config['MC_SERVER_DATA_DIR']) / server.id / 'data' / 'mods'

            if not mods_dir.exists():
                print(f"  No mods directory found")
                continue

            # Check all JAR files in mods directory
            jar_files = list(mods_dir.glob('*.jar'))

            if not jar_files:
                print(f"  No JAR files found")
                continue

            for jar_file in jar_files:
                print(f"  Checking: {jar_file.name}...", end=' ')

                if validate_jar_file(jar_file):
                    print("OK")
                else:
                    print("CORRUPTED - Removing...")
                    total_corrupted += 1

                    # Delete the corrupted file
                    try:
                        jar_file.unlink()
                        print(f"    Deleted: {jar_file}")
                        total_cleaned += 1

                        # Remove from database if exists
                        mod = ServerMod.query.filter_by(
                            server_id=server.id,
                            file_name=jar_file.name
                        ).first()

                        if mod:
                            db.session.delete(mod)
                            db.session.commit()
                            print(f"    Removed from database")

                    except Exception as e:
                        print(f"    ERROR: Failed to delete: {e}")

        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  Total corrupted files found: {total_corrupted}")
        print(f"  Successfully cleaned: {total_cleaned}")
        print(f"{'='*60}")


if __name__ == '__main__':
    print("Minecraft Mod Cleanup Utility")
    print("="*60)
    print("This will scan all servers for corrupted JAR files and remove them.")
    print()

    response = input("Continue? (y/n): ")

    if response.lower() == 'y':
        cleanup_corrupted_mods()
    else:
        print("Cancelled.")
