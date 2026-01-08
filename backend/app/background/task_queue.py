"""
Simple thread-based task queue for background jobs.
"""
import queue
import threading
import logging
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class TaskQueue:
    """Thread-based task queue."""

    def __init__(self, num_workers: int = 4):
        """
        Initialize task queue.

        Args:
            num_workers: Number of worker threads
        """
        self.task_queue = queue.Queue()
        self.workers = []
        self.running = True

        # Start worker threads
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker,
                name=f"TaskWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        logger.info(f"Task queue started with {num_workers} workers")

    def _worker(self):
        """Worker thread that processes tasks."""
        while self.running:
            try:
                func, args, kwargs = self.task_queue.get(timeout=1)

                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Task {func.__name__} failed: {e}", exc_info=True)
                finally:
                    self.task_queue.task_done()

            except queue.Empty:
                continue

    def submit(self, func: Callable, *args, **kwargs):
        """
        Submit a task to the queue.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        self.task_queue.put((func, args, kwargs))
        logger.info(f"Task submitted: {func.__name__}")

    def shutdown(self):
        """Shutdown the task queue."""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)
        logger.info("Task queue shut down")

    def wait_completion(self):
        """Wait for all tasks to complete."""
        self.task_queue.join()


# Global task queue instance
_task_queue = None


def get_task_queue() -> TaskQueue:
    """Get global task queue instance."""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue(num_workers=4)
    return _task_queue


def async_task(func: Callable) -> Callable:
    """
    Decorator to make a function execute asynchronously.

    Usage:
        @async_task
        def long_running_task(arg1, arg2):
            # ... do work ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        task_queue = get_task_queue()
        task_queue.submit(func, *args, **kwargs)
    return wrapper
