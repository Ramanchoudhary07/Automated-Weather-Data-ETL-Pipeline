import logging
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

LOG_FORMAT = "%(asctime)s UTC %(levelname)s %(name)s: %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """Send log messages to both the console and logs/pipeline.log, timestamped in UTC."""
    LOG_DIR.mkdir(exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)
    formatter.converter = time.gmtime  # log times in UTC, like everything else we store

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=level, handlers=[console_handler, file_handler], force=True)
