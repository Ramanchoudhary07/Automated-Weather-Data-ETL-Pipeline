import logging
import sys
import time

from src.config import CITIES_PATH, OPENWEATHER_API_KEY
from src.extract import extract_all, load_cities
from src.transform import transform
from src.load import load
from src.logger import setup_logging

logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    """Run extract -> transform -> load once."""
    start = time.perf_counter()
    logger.info("Pipeline started")

    cities = load_cities(CITIES_PATH)
    raw_records = extract_all(cities, OPENWEATHER_API_KEY)
    dim_city, fact_weather = transform(raw_records)
    load(dim_city, fact_weather)

    elapsed = time.perf_counter() - start
    logger.info("Pipeline finished in %.1fs", elapsed)


def main() -> None:
    """Entry point: set up logging, run the pipeline, exit non-zero on failure."""
    setup_logging()
    try:
        run_pipeline()
    except Exception:
        logger.exception("Pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
