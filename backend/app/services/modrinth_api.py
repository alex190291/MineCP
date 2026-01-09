"""
Modrinth API client for mod/modpack downloads.
"""
import requests
from typing import List, Dict, Optional
from flask import current_app


class ModrinthAPI:
    """Client for Modrinth API."""

    BASE_URL = "https://api.modrinth.com/v2"

    def __init__(self):
        """Initialize Modrinth API client."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MinecraftManager/1.0'
        })

    def search_mods(self, query: str, minecraft_version: Optional[str] = None,
                   loader: Optional[str] = None, limit: int = 20,
                   project_types: Optional[List[str]] = None,
                   server_side_only: bool = False) -> List[Dict]:
        """
        Search for mods on Modrinth.

        Args:
            query: Search query
            minecraft_version: Filter by Minecraft version
            loader: Filter by mod loader (forge, fabric, etc.) - can be string or list
            limit: Max results
            server_side_only: Only show server-side compatible mods

        Returns:
            List of mod dictionaries
        """
        params = {
            'query': query,
            'limit': limit,
            'facets': []
        }

        # Add filters
        facets = []
        if minecraft_version:
            facets.append(f'["versions:{minecraft_version}"]')

        if loader:
            # Handle both single loader and list of loaders
            if isinstance(loader, list):
                # For multiple loaders, create OR condition
                loader_facets = ','.join([f'"categories:{l}"' for l in loader])
                facets.append(f'[{loader_facets}]')
            else:
                facets.append(f'["categories:{loader}"]')

        if project_types:
            type_facets = ','.join([f'"project_type:{project_type}"' for project_type in project_types])
            facets.append(f'[{type_facets}]')

        # Filter for server-side compatible results only
        if server_side_only:
            facets.append('["server_side:required","server_side:optional"]')

        if facets:
            params['facets'] = '[' + ','.join(facets) + ']'

        try:
            response = self.session.get(f"{self.BASE_URL}/search", params=params)
            response.raise_for_status()
            data = response.json()

            return [{
                'project_id': hit['project_id'],
                'slug': hit['slug'],
                'title': hit['title'],
                'description': hit['description'],
                'author': hit.get('author'),
                'downloads': hit['downloads'],
                'icon_url': hit.get('icon_url'),
                'project_type': hit.get('project_type'),
                'categories': hit.get('categories', []),
            } for hit in data.get('hits', [])]

        except Exception as e:
            current_app.logger.error(f"Modrinth search failed: {e}")
            return []

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project details."""
        try:
            response = self.session.get(f"{self.BASE_URL}/project/{project_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"Failed to get project {project_id}: {e}")
            return None

    def get_project_versions(self, project_id: str, minecraft_version: Optional[str] = None,
                           loader: Optional[str] = None) -> List[Dict]:
        """Get available versions for a project."""
        params = {}
        if minecraft_version:
            params['game_versions'] = f'["{minecraft_version}"]'
        if loader:
            params['loaders'] = f'["{loader}"]'

        try:
            response = self.session.get(
                f"{self.BASE_URL}/project/{project_id}/version",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"Failed to get versions for {project_id}: {e}")
            return []

    def get_download_url(self, version_id: str) -> Optional[str]:
        """Get download URL for a specific version."""
        try:
            response = self.session.get(f"{self.BASE_URL}/version/{version_id}")
            response.raise_for_status()
            data = response.json()

            if data.get('files'):
                return data['files'][0]['url']

            return None
        except Exception as e:
            current_app.logger.error(f"Failed to get download URL for {version_id}: {e}")
            return None
