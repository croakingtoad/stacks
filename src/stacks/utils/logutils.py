import logging
import sys
import flask
from stacks.constants import LOG_PATH, LOG_FORMAT, LOG_DATE_FORMAT, LOG_VIEW_LENGTH
from pathlib import Path
from datetime import datetime
from collections import deque

LOG_BUFFER = deque(maxlen=LOG_VIEW_LENGTH)

def setup_logging(config=None):
    """
    Setup logging.
    """

    # ---- Determine log level ----
    if config is None:
        log_level = logging.DEBUG
    else:
        log_level = getattr(
            logging,
            config.get('logging', 'level', default='WARNING').upper(),
            logging.WARNING
        )

    # ---- Create log directory ----
    log_path = Path(LOG_PATH)
    log_path.mkdir(parents=True, exist_ok=True)


    # ---- Generate Logfile name ----
    log_file = (
        log_path / f"log-{datetime.now().strftime('%Y-%m-%d')}.log"
    )

    # ---- Root logger ----
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # ---- Patch Flask and Werkzeug ----
    flask.cli.show_server_banner = lambda *args, **kwargs: None
    logging.getLogger('werkzeug').disabled = True

    # ---- Remove old handlers ----
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    # ---- Create console handler ----
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # ---- Add UI buffer handler ----
    ui_handler = UILogHandler()
    ui_handler.setLevel(log_level)
    ui_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(ui_handler)

    # ---- Create file handler only when config exists ----
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(file_handler)

    # ---- Configure werkzeug logger ----
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)
    werkzeug_logger.propagate = False

    # Wipe werkzeug handlers
    for handler in werkzeug_logger.handlers[:]:
        werkzeug_logger.removeHandler(handler)

    # Add minimal error handler
    werkzeug_handler = logging.StreamHandler(sys.stdout)
    werkzeug_handler.setLevel(logging.ERROR)
    werkzeug_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    werkzeug_logger.addHandler(werkzeug_handler)




class UILogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            LOG_BUFFER.append(msg)
        except Exception:
            pass


def get_log_file_path() -> Path:
    """Return today's log file path (same formula as setup_logging)."""
    return Path(LOG_PATH) / f"log-{datetime.now().strftime('%Y-%m-%d')}.log"


def get_recent_logs(n: int = LOG_VIEW_LENGTH) -> list:
    """
    Read the last n lines from the shared log file.
    Worker processes write to this file so their logs appear here too.
    Falls back to LOG_BUFFER if the file is not available (e.g. debug mode).
    """
    log_file = get_log_file_path()
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            return [line.rstrip('\n') for line in lines[-n:]]
        except Exception:
            pass
    return list(LOG_BUFFER)