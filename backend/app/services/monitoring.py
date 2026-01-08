"""
Monitoring service for collecting server metrics.
"""
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Optional
from flask import current_app

from app.services.docker_manager import DockerManager
from app.services.rcon_client import RCONClient, get_online_players


class MetricsCollector:
    """Collect and store metrics for servers."""

    def __init__(self, retention_seconds: int = 3600):
        """
        Initialize metrics collector.

        Args:
            retention_seconds: How long to keep metrics in memory
        """
        self.retention_seconds = retention_seconds
        self.metrics = {}  # server_id -> deque of (timestamp, metrics)

    def collect_server_metrics(self, server_id: str, container_id: str,
                               rcon_host: str, rcon_port: int, rcon_password: str) -> Optional[Dict]:
        """
        Collect metrics for a server.

        Args:
            server_id: Server ID
            container_id: Docker container ID
            rcon_host: RCON host
            rcon_port: RCON port
            rcon_password: RCON password

        Returns:
            Metrics dictionary
        """
        docker_manager = DockerManager()

        # Get Docker stats
        stats = docker_manager.get_stats(container_id)
        if not stats:
            return None

        # Get online players via RCON
        players = get_online_players(rcon_host, rcon_port, rcon_password) or []

        # Combine metrics
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_percent': stats['cpu_percent'],
            'memory_usage': stats['memory_usage'],
            'memory_limit': stats['memory_limit'],
            'memory_percent': stats['memory_percent'],
            'network_rx': stats['network_rx'],
            'network_tx': stats['network_tx'],
            'online_players': len(players),
            'player_names': players
        }

        # Store in memory
        self._store_metrics(server_id, metrics)

        return metrics

    def _store_metrics(self, server_id: str, metrics: Dict):
        """Store metrics in memory with TTL."""
        if server_id not in self.metrics:
            self.metrics[server_id] = deque(maxlen=720)  # 720 * 5 sec = 1 hour

        timestamp = datetime.utcnow()
        self.metrics[server_id].append((timestamp, metrics))

        # Clean old metrics
        self._cleanup_old_metrics(server_id)

    def _cleanup_old_metrics(self, server_id: str):
        """Remove metrics older than retention period."""
        if server_id not in self.metrics:
            return

        cutoff = datetime.utcnow() - timedelta(seconds=self.retention_seconds)

        while self.metrics[server_id]:
            timestamp, _ = self.metrics[server_id][0]
            if timestamp < cutoff:
                self.metrics[server_id].popleft()
            else:
                break

    def get_recent_metrics(self, server_id: str, limit: int = 60) -> list:
        """
        Get recent metrics for a server.

        Args:
            server_id: Server ID
            limit: Number of recent metrics to return

        Returns:
            List of metrics dictionaries
        """
        if server_id not in self.metrics:
            return []

        recent = list(self.metrics[server_id])[-limit:]
        return [metrics for _, metrics in recent]

    def get_latest_metrics(self, server_id: str) -> Optional[Dict]:
        """Get latest metrics for a server."""
        if server_id not in self.metrics or not self.metrics[server_id]:
            return None

        _, metrics = self.metrics[server_id][-1]
        return metrics


# Global metrics collector
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
