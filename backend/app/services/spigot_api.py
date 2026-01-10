"""
SpigotMC (Spiget) API client for plugin search.
"""
from typing import Dict, List, Optional

import requests
from flask import current_app


class SpigotAPI:
    """Client for Spiget API (SpigotMC community API)."""

    BASE_URL = "https://api.spiget.org/v2"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MinecraftManager/1.0"
        })

    def search_resources(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for resources (plugins) on SpigotMC via Spiget.

        Args:
            query: Search term
            limit: Max results

        Returns:
            List of resource dictionaries
        """
        params = {"size": limit}
        try:
            response = self.session.get(f"{self.BASE_URL}/search/resources/{query}", params=params)
            response.raise_for_status()
            results = response.json() or []
            return [self._normalize_resource(resource) for resource in results]
        except Exception as e:
            current_app.logger.error(f"SpigotMC search failed: {e}")
            return []

    def _normalize_resource(self, resource: Dict) -> Dict:
        resource_id = resource.get("id")
        title = resource.get("name") or resource.get("title") or "Unknown"
        description = resource.get("tag") or resource.get("description") or ""
        downloads = resource.get("downloads") or 0

        icon_url = None
        icon = resource.get("icon")
        if isinstance(icon, dict):
            icon_url = icon.get("url")
        elif isinstance(icon, str):
            icon_url = icon

        categories = []
        category = resource.get("category")
        if isinstance(category, dict):
            name = category.get("name")
            if name:
                categories.append(name)

        return {
            "project_id": str(resource_id) if resource_id is not None else None,
            "slug": None,
            "title": title,
            "description": description,
            "downloads": downloads,
            "icon_url": icon_url,
            "categories": categories,
        }
