"""
Mod/Plugin management API endpoints.
"""
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.server import Server
from app.models.server_mod import ServerMod
from app.models.user import User
from app.services.modrinth_api import ModrinthAPI
from app.services.spigot_api import SpigotAPI
from app.background.task_queue import get_task_queue
from app.background.server_tasks import download_mod_async

bp = Blueprint('mods', __name__)

def _require_server_access(user: User, server: Server):
    if not server:
        return jsonify({'error': 'Server not found'}), 404
    if not user:
        return jsonify({'error': 'Forbidden'}), 403
    if user and user.role != 'admin' and server.created_by != user.id:
        return jsonify({'error': 'Forbidden'}), 403
    return None


def _get_server_mods_dir(server: Server) -> Path:
    data_dir = current_app.config['MC_SERVER_DATA_DIR'] / server.id / 'data'
    if server.type and server.type.lower() in {'paper', 'spigot', 'purpur'}:
        return data_dir / 'plugins'
    return data_dir / 'mods'


def _parse_spigot_resource(mod_url: str):
    if not mod_url:
        return None, None

    url = mod_url.strip()
    if url.isdigit():
        return url, None

    if 'spigotmc.org' not in url:
        return None, None

    parsed = urlparse(url if '://' in url else f'https://{url}')
    path = parsed.path or ''
    if '/resources/' not in path:
        return None, None

    segment = path.split('/resources/', 1)[1].split('/', 1)[0]
    resource_id = None
    slug = None

    if segment:
        if '.' in segment:
            slug_candidate, id_candidate = segment.rsplit('.', 1)
            if id_candidate.isdigit():
                resource_id = id_candidate
                slug = slug_candidate or None
        elif segment.isdigit():
            resource_id = segment

    if not resource_id:
        match = re.search(r'/resources/(?:[^/]*\.)?(\d+)', path)
        if match:
            resource_id = match.group(1)

    return resource_id, slug


@bp.route('/mods/search', methods=['GET'])
@jwt_required()
def search_mods():
    """Search mods/plugins via Modrinth and SpigotMC."""
    query = request.args.get('query') or request.args.get('q')
    minecraft_version = request.args.get('version')
    loader = request.args.get('loader')
    server_type = request.args.get('serverType')
    limit = request.args.get('limit', default=20, type=int)

    if not query:
        return jsonify({'error': 'query parameter required'}), 400

    normalized_server_type = (server_type or '').lower()
    plugin_servers = {'paper', 'spigot', 'purpur'}

    # Map server type to Modrinth loader/category if provided
    if server_type and not loader:
        loader = _map_server_type_to_loader(server_type)

    project_types = ['plugin'] if normalized_server_type in plugin_servers else ['mod']
    server_side_only = normalized_server_type not in plugin_servers

    modrinth_api = ModrinthAPI()
    modrinth_results = modrinth_api.search_mods(
        query,
        minecraft_version,
        loader,
        limit=limit,
        project_types=project_types,
        server_side_only=server_side_only,
    )

    results = []
    for result in modrinth_results:
        content_type = result.get('project_type') or project_types[0]
        results.append({
            **result,
            'source': 'modrinth',
            'content_type': content_type,
        })

    if normalized_server_type in plugin_servers:
        spigot_api = SpigotAPI()
        spigot_results = spigot_api.search_resources(query, limit=limit)
        for result in spigot_results:
            results.append({
                **result,
                'source': 'spigotmc',
                'content_type': 'plugin',
            })

    return jsonify({'results': results}), 200


def _map_server_type_to_loader(server_type):
    """
    Map server type to Modrinth loader categories.

    Args:
        server_type: Server type (paper, forge, fabric, vanilla, etc.)

    Returns:
        Modrinth loader name or list of compatible loaders
    """
    mapping = {
        'paper': ['bukkit', 'spigot', 'paper', 'purpur'],
        'spigot': ['bukkit', 'spigot'],
        'forge': 'forge',
        'fabric': 'fabric',
        'vanilla': 'datapack',
    }
    return mapping.get(server_type.lower(), None)


@bp.route('/mods/upload', methods=['POST'])
@jwt_required()
def upload_mod():
    """Upload a custom mod file."""
    import zipfile

    if 'file' not in request.files:
        return jsonify({'error': 'file required'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'file required'}), 400

    filename = secure_filename(file.filename)

    # Validate file extension
    if not filename.lower().endswith('.jar'):
        return jsonify({'error': 'Only .jar files are allowed'}), 400

    upload_dir = current_app.config['UPLOAD_FOLDER']
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename
    file.save(file_path)

    # Validate the uploaded JAR file
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Test the ZIP file integrity
            bad_file = zip_file.testzip()
            if bad_file is not None:
                file_path.unlink()  # Delete corrupted file
                return jsonify({'error': f'Corrupted JAR file: {bad_file}'}), 400
    except zipfile.BadZipFile:
        file_path.unlink()  # Delete invalid file
        return jsonify({'error': 'Invalid JAR file - not a valid ZIP archive'}), 400
    except Exception as e:
        file_path.unlink()  # Delete problematic file
        return jsonify({'error': f'Failed to validate JAR file: {str(e)}'}), 400

    # Check minimum file size (1 KB)
    if file_path.stat().st_size < 1024:
        file_path.unlink()
        return jsonify({'error': 'File is too small to be a valid mod'}), 400

    return jsonify({
        'file_name': filename,
        'file_path': str(file_path),
    }), 201


@bp.route('/servers/<server_id>/mods', methods=['GET'])
@jwt_required()
def list_server_mods(server_id):
    """List all mods installed on a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    mods = ServerMod.query.filter_by(server_id=server_id).all()
    return jsonify([mod.to_dict() for mod in mods]), 200


@bp.route('/servers/<server_id>/mods', methods=['POST'])
@jwt_required()
def install_mod(server_id):
    """Install a mod on a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    data = request.get_json() or {}
    mod_name = data.get('mod_name')
    mod_url = data.get('mod_url')
    source = (data.get('source') or 'modrinth').lower()
    source_id = data.get('source_id')
    minecraft_version = data.get('version') or server.version
    upload_path = data.get('file_path')

    if source in {'spigot', 'spigotmc.org'}:
        source = 'spigotmc'
    if mod_url and 'spigotmc.org' in mod_url.lower():
        source = 'spigotmc'

    mods_dir = _get_server_mods_dir(server)
    mods_dir.mkdir(parents=True, exist_ok=True)

    # Handle file upload
    if upload_path:
        upload_path = Path(upload_path)
        if not upload_path.exists():
            return jsonify({'error': 'Uploaded file not found'}), 404
        filename = upload_path.name
        destination = mods_dir / filename
        shutil.move(str(upload_path), destination)
        mod_record = ServerMod(
            server_id=server.id,
            name=mod_name or filename,
            source='upload',
            source_id=source_id,
            version=minecraft_version,
            file_name=filename,
            file_path=str(destination),
        )
        db.session.add(mod_record)
        db.session.commit()
        return jsonify(mod_record.to_dict()), 201

    # Initialize variables
    download_url = None
    filename = None
    version_number = None
    slug = None

    # Handle Modrinth URL/slug resolution
    if source == 'modrinth' and mod_url:
        # Extract slug from URL if it's a full URL
        if 'modrinth.com' in mod_url:
            # URL format: https://modrinth.com/mod/slug or https://modrinth.com/plugin/slug
            parts = mod_url.rstrip('/').split('/')
            slug = parts[-1]
        else:
            slug = mod_url

        # Use Modrinth API to get download URL
        api = ModrinthAPI()
        project = api.get_project(slug)

        if not project:
            return jsonify({'error': f'Mod not found on Modrinth: {slug}'}), 404

        mod_name = project.get('title', slug)

        # Get compatible version
        loader_type = _map_server_type_to_loader(server.type)

        # For Paper/Bukkit, try plugins first (most compatible)
        if isinstance(loader_type, list):
            # Try loaders in order of preference
            versions = None
            for loader in loader_type:
                versions = api.get_project_versions(slug, minecraft_version, loader)
                if versions:
                    break
        else:
            versions = api.get_project_versions(slug, minecraft_version, loader_type)

        if not versions:
            return jsonify({'error': f'No compatible version found for {minecraft_version}'}), 404

        # Get the latest compatible version
        latest_version = versions[0]
        version_number = latest_version.get('version_number')

        # Get download URL from the version
        if not latest_version.get('files'):
            return jsonify({'error': 'No files available for this version'}), 404

        download_url = latest_version['files'][0]['url']
        filename = latest_version['files'][0]['filename']

    elif source == 'spigotmc':
        resource_id, slug = _parse_spigot_resource(mod_url or '') if mod_url else (None, None)
        if not resource_id and source_id:
            resource_id = str(source_id)
        if not resource_id:
            return jsonify({'error': 'Invalid SpigotMC resource URL'}), 400

        download_url = f"https://api.spiget.org/v2/resources/{resource_id}/download"
        mod_name = mod_name or slug or f"spigot-{resource_id}"
        filename = f"{mod_name}.jar"
        slug = resource_id
    elif mod_url:
        # Direct download URL provided
        download_url = mod_url
        filename = f"{mod_name}.jar" if mod_name else "mod.jar"
    else:
        return jsonify({'error': 'mod_url or source_id required'}), 400

    # Create database record
    file_path = mods_dir / filename
    mod_record = ServerMod(
        server_id=server.id,
        name=mod_name or filename.replace('.jar', ''),
        source=source,
        source_id=source_id or slug,
        version=version_number or minecraft_version,
        file_name=filename,
        file_path=str(file_path),
    )

    db.session.add(mod_record)
    db.session.commit()

    # Queue download task
    task_queue = get_task_queue()
    task_queue.submit(download_mod_async, server.id, download_url, filename.replace('.jar', ''))

    return jsonify(mod_record.to_dict()), 202


@bp.route('/servers/<server_id>/mods/<mod_id>', methods=['DELETE'])
@jwt_required()
def delete_mod(server_id, mod_id):
    """Remove a mod from a server."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    server = Server.query.get(server_id)

    access_check = _require_server_access(user, server)
    if access_check:
        return access_check

    mod = ServerMod.query.get(mod_id)
    if not mod or mod.server_id != server_id:
        return jsonify({'error': 'Mod not found'}), 404

    mod_path = Path(mod.file_path)
    if mod_path.exists():
        mod_path.unlink()

    db.session.delete(mod)
    db.session.commit()

    return jsonify({'message': 'Mod removed'}), 200
