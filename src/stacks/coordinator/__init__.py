"""
Coordinator package for multi-process download management.

This package provides:
- SQLite-based queue management (database.py)
- Queue operations for adding/claiming/completing downloads (queue_ops.py)
- Download worker processes (download_worker.py)
- Scraper process for fetching metadata (scraper_process.py)
- Coordinator process for health monitoring (coordinator_process.py)
- Process lifecycle management (process_manager.py)
"""
