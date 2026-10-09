import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths from this file's location, so the pipeline works from any folder
# (Task Scheduler, for example, does not start programs in the project folder).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
CITIES_PATH = PROJECT_ROOT / "config" / "cities.json"

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
