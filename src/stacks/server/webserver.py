from flask import Flask
from flask_cors import CORS
from stacks.config.config import Config
from stacks.constants import WWW_PATH, TIMESTAMP, CONFIG_FILE
from stacks.utils.logutils import setup_logging
from stacks.api import register_api
import logging
import os


def create_app(config_path: str = None, debug_mode: bool = False):
    """
    Create and configure the Flask application.

    In production mode (debug_mode=False):
    - Workers run as separate processes managed by main.py
    - Queue operations use SQLite via queue_ops
    - No worker thread is started

    In debug mode (debug_mode=True):
    - Uses old single-process architecture
    - DownloadQueue and DownloadWorker run in-process
    - Useful for development and debugging
    """
    # ---- Use default config path if none provided ----
    if config_path is None:
        config_path = os.environ.get("STACKS_CONFIG_PATH", str(CONFIG_FILE))

    # ---- Detect mode from environment if not explicitly set ----
    # This handles the case where create_app is called by Gunicorn without arguments
    if not debug_mode:
        debug_mode = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true")

    # ---- Setup logging ---
    setup_logging(None)
    logger = logging.getLogger("stacks.server")
    logger.info("Stacks server initializing...")

    app = Flask(
        __name__,
        template_folder=WWW_PATH,
        static_folder=WWW_PATH,
        static_url_path=""
    )
    CORS(app, supports_credentials=True)

    # ---- Enable template auto-reload in debug mode ----
    if debug_mode:
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching
        logger.info("Debug mode: Template auto-reload enabled")

    # ---- Load config ----
    config = Config(config_path)
    setup_logging(config)

    # ---- Set secret key from config ----
    app.secret_key = config.get("api", "session_secret")

    # ---- Store mode flag ----
    app.stacks_multiprocess = not debug_mode

    if debug_mode:
        # ---- Debug mode: use old single-process architecture ----
        logger.info("Debug mode: Using single-process architecture with worker thread")

        from stacks.server.queue import DownloadQueue
        from stacks.server.worker import DownloadWorker

        queue = DownloadQueue(config)
        worker = DownloadWorker(queue, config)
        worker.start()

        app.stacks_queue = queue
        app.stacks_worker = worker
    else:
        # ---- Production mode: workers are separate processes ----
        logger.info("Production mode: Using multi-process architecture")

        # Queue operations go through SQLite via queue_ops
        # Worker processes are managed by main.py
        app.stacks_queue = None
        app.stacks_worker = None

    # ---- Attach config to app ----
    app.stacks_config = config

    # ---- Set default port and host ----
    app.stacks_host = config.get("server", "host", default="0.0.0.0")
    app.stacks_port = config.get("server", "port", default=7788)

    # ---- Cache busting makes me feel good ----
    @app.context_processor
    def inject_constants():
        return dict(TIMESTAMP=TIMESTAMP)

    # ---- Register all API routes ----
    register_api(app)
    logger.info("Stacks initialized")
    return app
