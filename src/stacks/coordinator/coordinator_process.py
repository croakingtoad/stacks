"""
Coordinator process - health monitoring and cleanup.

This process monitors worker heartbeats and cleans up resources from
workers that have died (releases mirrors, requeues downloads).
"""

import logging
import signal
import time
from multiprocessing import Event

from stacks.constants import WORKER_TIMEOUT
from stacks.coordinator.queue_ops import QueueOperations
from stacks.utils.domainupdater import update_wiki_domains

logger = logging.getLogger(__name__)


def coordinator_process(stop_event: Event) -> None:
    """
    Coordinator process entry point.

    Responsibilities:
    - Monitor worker heartbeats
    - Release mirrors from dead workers
    - Requeue downloads from dead workers
    - Periodic cleanup tasks

    Args:
        stop_event: Event to signal the coordinator to stop
    """
    worker_id = "coordinator-1"

    # Setup logging - write to stdout AND the shared log file so /api/logs shows worker output
    import sys
    from stacks.utils.logutils import get_log_file_path, LOG_FORMAT, LOG_DATE_FORMAT
    _log_file = get_log_file_path()
    _log_file.parent.mkdir(parents=True, exist_ok=True)
    _formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    _root = logging.getLogger()
    _root.setLevel(logging.INFO)
    for _h in _root.handlers[:]:
        _root.removeHandler(_h)
        _h.close()
    _ch = logging.StreamHandler(sys.stdout)
    _ch.setFormatter(_formatter)
    _root.addHandler(_ch)
    _fh = logging.FileHandler(_log_file, encoding='utf-8')
    _fh.setFormatter(_formatter)
    _root.addHandler(_fh)
    coord_logger = logging.getLogger(f'worker.{worker_id}')
    coord_logger.info("Coordinator process starting")

    # Handle signals gracefully
    def signal_handler(signum, frame):
        coord_logger.info(f"Coordinator received signal {signum}, stopping")
        stop_event.set()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize
    queue_ops = QueueOperations()

    # Main coordinator loop
    check_interval = 10  # Check every 10 seconds
    last_domain_update = 0
    domain_update_interval = 6 * 3600  # 6 hours

    while not stop_event.is_set():
        try:
            # Send our own heartbeat
            queue_ops.heartbeat(worker_id, 'coordinator')

            # Refresh Anna's Archive domains from Wikipedia every 6 hours
            if time.time() - last_domain_update >= domain_update_interval:
                update_wiki_domains()
                last_domain_update = time.time()

            # Check for stale workers
            stale_workers = queue_ops.get_stale_workers(timeout_seconds=WORKER_TIMEOUT)

            for stale_worker_id in stale_workers:
                # Don't clean up ourselves
                if stale_worker_id == worker_id:
                    continue

                coord_logger.warning(f"Worker {stale_worker_id} appears dead (no heartbeat for {WORKER_TIMEOUT}s)")
                queue_ops.cleanup_dead_worker(stale_worker_id)

            # Wait before next check
            stop_event.wait(timeout=check_interval)

        except Exception as e:
            coord_logger.error(f"Coordinator loop error: {e}", exc_info=True)
            # Wait before retrying to avoid tight error loops
            stop_event.wait(timeout=5)

    # Cleanup
    coord_logger.info("Coordinator process stopping")
    queue_ops.remove_worker_heartbeat(worker_id)
    coord_logger.info("Coordinator process stopped")
