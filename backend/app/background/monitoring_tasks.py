"""
Background tasks for monitoring servers.
"""
import schedule
import threading
import time
from flask import current_app

from sqlalchemy.exc import OperationalError
from app.models.server import Server
from app.services.monitoring import get_metrics_collector
from app.websockets.monitoring import broadcast_server_metrics

_scheduler_thread = None
_scheduler_lock = threading.Lock()


def collect_metrics_for_all_servers(app):
    """Collect metrics for all running servers."""
    with app.app_context():
        try:
            servers = Server.query.filter_by(status='running').all()
        except OperationalError as e:
            current_app.logger.warning(f"Monitoring skipped (db not ready): {e}")
            return
        metrics_collector = get_metrics_collector()

        for server in servers:
            if not server.container_id:
                continue

            try:
                # Get container IP for RCON
                from app.services.docker_manager import DockerManager
                docker_manager = DockerManager()
                rcon_host = docker_manager.get_container_ip(server.container_id) or 'localhost'

                metrics = metrics_collector.collect_server_metrics(
                    server_id=server.id,
                    container_id=server.container_id,
                    rcon_host=rcon_host,
                    rcon_port=25575,  # Internal RCON port
                    rcon_password=server.rcon_password or ''
                )

                if metrics:
                    current_app.logger.debug(f"Collected metrics for {server.name}")
                    broadcast_server_metrics(server.id, metrics)

            except Exception as e:
                current_app.logger.error(f"Failed to collect metrics for {server.name}: {e}")


def run_scheduled_tasks(app):
    """Run scheduled monitoring tasks."""
    schedule.clear()
    schedule.every(5).seconds.do(collect_metrics_for_all_servers, app)

    while True:
        schedule.run_pending()
        time.sleep(1)


def start_monitoring_scheduler(app):
    """Start monitoring scheduler in background thread."""
    global _scheduler_thread
    with _scheduler_lock:
        if _scheduler_thread and _scheduler_thread.is_alive():
            return
        _scheduler_thread = threading.Thread(
            target=run_scheduled_tasks,
            args=(app,),
            name="MonitoringScheduler",
            daemon=True
        )
        _scheduler_thread.start()
