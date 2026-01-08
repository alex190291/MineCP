"""
Minecraft versions API endpoints.
"""
import requests
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

bp = Blueprint('versions', __name__)


@bp.route('/minecraft', methods=['GET'])
@jwt_required()
def get_minecraft_versions():
    """
    Get available Minecraft versions from various sources.

    Returns versions for:
    - Vanilla: From Mojang's version manifest
    - Paper: From PaperMC API
    - Forge: From official Forge API
    - Fabric: From Fabric meta API
    """
    versions = {
        'vanilla': [],
        'paper': [],
        'forge': [],
        'fabric': [],
        'all': []
    }

    try:
        # Get Paper versions (most reliable for server software)
        response = requests.get('https://api.papermc.io/v2/projects/paper', timeout=5)
        if response.status_code == 200:
            data = response.json()
            paper_versions = data.get('versions', [])
            versions['paper'] = paper_versions[-20:]  # Last 20 versions
            versions['all'] = paper_versions[-20:]
    except Exception as e:
        print(f'Failed to fetch Paper versions: {e}')

    try:
        # Get Mojang versions (official vanilla)
        response = requests.get('https://launchermeta.mojang.com/mc/game/version_manifest.json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            vanilla_versions = []
            for v in data.get('versions', []):
                if v['type'] == 'release':
                    vanilla_versions.append(v['id'])
                if len(vanilla_versions) >= 20:
                    break
            versions['vanilla'] = vanilla_versions

            # Add vanilla versions to 'all' if not already present
            for v in vanilla_versions:
                if v not in versions['all']:
                    versions['all'].append(v)
    except Exception as e:
        print(f'Failed to fetch Mojang versions: {e}')

    # Sort 'all' versions in descending order
    try:
        versions['all'] = sorted(
            versions['all'],
            key=lambda x: [int(n) for n in x.split('.')],
            reverse=True
        )
    except:
        pass

    return jsonify(versions), 200
