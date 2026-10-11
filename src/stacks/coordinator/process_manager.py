"""
Process lifecycle management.

Manages spawning, monitoring, and graceful shutdown of all worker processes:
- Coordinator process (health monitoring)
- Download worker processes (multiple)
- Scraper process
"""

import logging
import multiprocessing
from multiprocessing import Process, Event
from pathlib import Path
from typing import List, Tuple

from stacks.constants import DOWNLOAD_WORKERS, SCRAPER_WORKERS

logger = logging.getLogger(__name__)


class ProcessManager:
    """
    Spawns and manages worker processes.

    Usage:
        manager = ProcessManager(config_path)
        manager.start_all()
        # ... application runs ...
        manager.stop_all()
    """

    def __init__(self, config_path: Path):
        """
        Initialize the process manager.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.stop_event = Event()
        self.processes: List[Tuple[str, Process]] = []
        self.logger = logging.getLogger('process_manager')

    def start_all(self) -> None:
        """
        Spawn all worker processes.

        Starts:
        - 1 coordinator process
        - N download workers (DOWNLOAD_WORKERS constant)
        - 1 scraper process
        """
        # Import process functions here to avoid circular imports
        from stacks.coordinator.coordinator_process import coordinator_process
        from stacks.coordinator.download_worker import download_worker_process
        from stacks.coordinator.scraper_process import scraper_process

        self.logger.info("Starting worker processes")

        # Start coordinator process
        self.logger.info("Starting coordinator process")
        p = Process(
            target=coordinator_process,
            args=(self.stop_event,),
            name="coordinator"
        )
        p.start()
        self.processes.append(('coordinator', p))

        # Start download workers
        self.logger.info(f"Starting {DOWNLOAD_WORKERS} download worker(s)")
        for i in range(DOWNLOAD_WORKERS):
            worker_id = f"download-{i}"
            p = Process(
                target=download_worker_process,
                args=(worker_id, self.config_path, self.stop_event),
                name=worker_id
            )
            p.start()
            self.processes.append((worker_id, p))

        # Start scraper process(es)
        self.logger.info(f"Starting {SCRAPER_WORKERS} scraper worker(s)")
        for i in range(SCRAPER_WORKERS):
            worker_id = f"scraper-{i + 1}" if SCRAPER_WORKERS > 1 else "scraper-1"
            p = Process(
                target=scraper_process,
                args=(self.config_path, self.stop_event),
                name=worker_id
            )
            p.start()
            self.processes.append((worker_id, p))

        self.logger.info(f"Started {len(self.processes)} worker processes")

    def stop_all(self, timeout: int = 10) -> None:
        """
        Signal all processes to stop and wait for graceful shutdown.

        Args:
            timeout: Maximum seconds to wait for each process to stop
        """
        if not self.processes:
            return

        self.logger.info("Stopping all worker processes")

        # Signal all processes to stop
        self.stop_event.set()

        # Wait for each process to stop
        for name, process in self.processes:
            self.logger.info(f"Waiting for {name} to stop")
            process.join(timeout=timeout)

            if process.is_alive():
                self.logger.warning(f"Force terminating {name}")
                process.terminate()
                process.join(timeout=2)

                if process.is_alive():
                    self.logger.error(f"Failed to terminate {name}, killing")
                    process.kill()

        self.processes.clear()
        self.logger.info("All worker processes stopped")

    def is_running(self) -> bool:
        """Check if any worker processes are still running."""
        return any(p.is_alive() for _, p in self.processes)

    def get_status(self) -> dict:
        """
        Get status of all worker processes.

        Returns:
            Dictionary with process name as key and status info as value
        """
        status = {}
        for name, process in self.processes:
            status[name] = {
                'pid': process.pid,
                'alive': process.is_alive(),
                'exitcode': process.exitcode
            }
        return status

    def restart_dead_processes(self) -> int:
        """
        Restart any processes that have died unexpectedly.

        Returns:
            Number of processes restarted
        """
        # Import process functions here to avoid circular imports
        from stacks.coordinator.coordinator_process import coordinator_process
        from stacks.coordinator.download_worker import download_worker_process
        from stacks.coordinator.scraper_process import scraper_process

        restarted = 0

        for i, (name, process) in enumerate(self.processes):
            if not process.is_alive() and not self.stop_event.is_set():
                self.logger.warning(f"Process {name} died (exitcode: {process.exitcode}), restarting")

                # Determine process type and restart
                if name == 'coordinator':
                    p = Process(
                        target=coordinator_process,
                        args=(self.stop_event,),
                        name="coordinator"
                    )
                elif name.startswith('download-'):
                    p = Process(
                        target=download_worker_process,
                        args=(name, self.config_path, self.stop_event),
                        name=name
                    )
                elif name.startswith('scraper'):
                    p = Process(
                        target=scraper_process,
                        args=(self.config_path, self.stop_event),
                        name=name
                    )
                else:
                    self.logger.error(f"Unknown process type: {name}")
                    continue

                p.start()
                self.processes[i] = (name, p)
                restarted += 1

        return restarted
