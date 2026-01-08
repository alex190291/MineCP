"""
Docker Manager - Handles Docker container lifecycle for Minecraft servers.
"""
import docker
import secrets
from pathlib import Path
from typing import Dict, Optional, List
from flask import current_app


class DockerManager:
    """Manage Docker containers for Minecraft servers."""

    def __init__(self):
        """Initialize Docker client."""
        self.client = docker.from_env()
        self.network_name = current_app.config['MC_SERVER_NETWORK']

    def ensure_network(self):
        """Ensure Minecraft network exists."""
        try:
            self.client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.client.networks.create(
                self.network_name,
                driver="bridge"
            )
            current_app.logger.info(f"Created network: {self.network_name}")

    def create_server(
        self,
        server_id: str,
        server_type: str,
        version: str,
        memory_limit: int,
        cpu_limit: float,
        host_port: int,
        rcon_password: str,
        server_properties: Dict,
        java_args: Optional[str] = None
    ) -> docker.models.containers.Container:
        """
        Create and start a Minecraft server container.

        Args:
            server_id: Unique server ID
            server_type: Server type (vanilla, paper, forge, etc.)
            version: Minecraft version
            memory_limit: Memory limit in MB
            cpu_limit: CPU limit in cores
            host_port: Host port to expose
            rcon_password: RCON password for server management
            server_properties: Server.properties configuration
            java_args: Additional Java arguments

        Returns:
            Docker container object
        """
        self.ensure_network()

        # Container name
        container_name = f"mc-server-{server_id[:8]}"

        # Data directories
        data_dir = current_app.config['MC_SERVER_DATA_DIR'] / server_id
        data_dir.mkdir(parents=True, exist_ok=True)

        # Environment variables
        env = {
            'EULA': 'TRUE',
            'VERSION': version,
            'TYPE': server_type.upper(),
            'MEMORY': f'{memory_limit}M',
            'ENABLE_RCON': 'true',
            'RCON_PASSWORD': rcon_password,
            'RCON_PORT': '25575',
            'ONLINE_MODE': server_properties.get('online_mode', 'true'),
            'DIFFICULTY': server_properties.get('difficulty', 'normal'),
            'MAX_PLAYERS': str(server_properties.get('max_players', 20)),
            'ALLOW_NETHER': str(server_properties.get('allow_nether', 'true')),
            'ANNOUNCE_PLAYER_ACHIEVEMENTS': str(server_properties.get('announce_player_achievements', 'true')),
            'ENABLE_COMMAND_BLOCK': str(server_properties.get('enable_command_block', 'false')),
            'SPAWN_PROTECTION': str(server_properties.get('spawn_protection', 16)),
            'VIEW_DISTANCE': str(server_properties.get('view_distance', 10)),
            'PVP': str(server_properties.get('pvp', 'true')),
            'GAMEMODE': server_properties.get('gamemode', 'survival'),
            'MOTD': server_properties.get('motd', 'A Minecraft Server'),
        }

        # Add custom Java args if provided
        if java_args:
            env['JVM_OPTS'] = java_args

        # Volume mounts
        volumes = {
            str(data_dir / 'data'): {'bind': '/data', 'mode': 'rw'},
        }

        # Port mappings
        ports = {
            '25565/tcp': host_port,  # Minecraft port
            '25575/tcp': None,  # RCON port (internal only)
        }

        # Resource limits
        mem_limit = f"{memory_limit}m"
        nano_cpus = int(cpu_limit * 1e9)  # Convert cores to nano CPUs

        try:
            # Create container
            container = self.client.containers.run(
                image='itzg/minecraft-server:latest',
                name=container_name,
                detach=True,
                environment=env,
                ports=ports,
                volumes=volumes,
                network=self.network_name,
                mem_limit=mem_limit,
                nano_cpus=nano_cpus,
                restart_policy={'Name': 'unless-stopped'},
                labels={
                    'mc-manager.server-id': server_id,
                    'mc-manager.server-type': server_type,
                }
            )

            current_app.logger.info(f"Created container {container_name} for server {server_id}")
            return container

        except Exception as e:
            current_app.logger.error(f"Failed to create container: {e}")
            raise

    def get_container(self, container_id: str) -> Optional[docker.models.containers.Container]:
        """Get container by ID."""
        try:
            return self.client.containers.get(container_id)
        except docker.errors.NotFound:
            return None

    def get_container_ip(self, container_id: str) -> Optional[str]:
        """Get container's IP address on the Minecraft network."""
        try:
            container = self.get_container(container_id)
            if container:
                container.reload()  # Refresh container data
                networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
                if self.network_name in networks:
                    return networks[self.network_name].get('IPAddress')
            return None
        except Exception as e:
            current_app.logger.error(f"Failed to get container IP: {e}")
            return None

    def start_server(self, container_id: str) -> bool:
        """Start a server container."""
        try:
            container = self.get_container(container_id)
            if container:
                container.start()
                current_app.logger.info(f"Started container {container_id}")
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Failed to start container: {e}")
            return False

    def stop_server(self, container_id: str, timeout: int = 30) -> bool:
        """Stop a server container gracefully."""
        try:
            container = self.get_container(container_id)
            if container:
                container.stop(timeout=timeout)
                current_app.logger.info(f"Stopped container {container_id}")
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Failed to stop container: {e}")
            return False

    def restart_server(self, container_id: str, timeout: int = 30) -> bool:
        """Restart a server container."""
        try:
            container = self.get_container(container_id)
            if container:
                container.restart(timeout=timeout)
                current_app.logger.info(f"Restarted container {container_id}")
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Failed to restart container: {e}")
            return False

    def delete_server(self, container_id: str, remove_volumes: bool = False) -> bool:
        """Delete a server container."""
        try:
            container = self.get_container(container_id)
            if container:
                # Stop if running
                if container.status == 'running':
                    container.stop(timeout=10)

                # Remove container
                container.remove(v=remove_volumes)
                current_app.logger.info(f"Deleted container {container_id}")
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Failed to delete container: {e}")
            return False

    def get_container_status(self, container_id: str) -> Optional[str]:
        """Get container status."""
        container = self.get_container(container_id)
        if container:
            return container.status
        return None

    def get_container_logs(self, container_id: str, tail: int = 100) -> Optional[str]:
        """Get container logs."""
        try:
            container = self.get_container(container_id)
            if container:
                logs = container.logs(tail=tail, timestamps=True)
                return logs.decode('utf-8')
            return None
        except Exception as e:
            current_app.logger.error(f"Failed to get logs: {e}")
            return None

    def stream_logs(self, container_id: str):
        """Stream container logs (generator)."""
        try:
            container = self.get_container(container_id)
            if container:
                for line in container.logs(stream=True, follow=True):
                    yield line.decode('utf-8')
        except Exception as e:
            current_app.logger.error(f"Failed to stream logs: {e}")

    def get_stats(self, container_id: str) -> Optional[Dict]:
        """Get container resource stats."""
        try:
            container = self.get_container(container_id)
            if container:
                stats = container.stats(stream=False)
                return self._parse_stats(stats)
            return None
        except Exception as e:
            current_app.logger.error(f"Failed to get stats: {e}")
            return None

    def _parse_stats(self, stats: Dict) -> Dict:
        """Parse Docker stats into usable metrics."""
        # CPU usage
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        cpu_count = stats['cpu_stats']['online_cpus']
        cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0 if system_delta > 0 else 0.0

        # Memory usage
        memory_usage = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats']['limit']
        memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0

        # Network I/O
        network_rx = 0
        network_tx = 0
        if 'networks' in stats:
            for interface in stats['networks'].values():
                network_rx += interface['rx_bytes']
                network_tx += interface['tx_bytes']

        return {
            'cpu_percent': round(cpu_percent, 2),
            'memory_usage': memory_usage,
            'memory_limit': memory_limit,
            'memory_percent': round(memory_percent, 2),
            'network_rx': network_rx,
            'network_tx': network_tx,
        }

    def list_all_servers(self) -> List[docker.models.containers.Container]:
        """List all Minecraft server containers."""
        try:
            return self.client.containers.list(
                all=True,
                filters={'label': 'mc-manager.server-id'}
            )
        except Exception as e:
            current_app.logger.error(f"Failed to list containers: {e}")
            return []
