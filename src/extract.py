import json
import logging
import time

import requests

from src.config import OPENWEATHER_API_KEY, BASE_URL, CITIES_PATH

logger = logging.getLogger(__name__)


def load_cities(path: str) -> list[dict]:
    """Read the list of cities from a JSON file."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def fetch_city_weather(city: dict, api_key: str, max_retries: int = 3) -> dict | None:
    """Fetch current weather for one city. Returns the raw JSON dict, or None if it failed."""
    city_name = city["name"]
    country = city["country"]
    params = {"q": f"{city_name},{country}", "units": "metric", "appid": api_key}

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()

            if response.status_code in (401, 404):
                # Retrying can't fix a bad key or an unknown city, so give up straight away.
                logger.error("%s: got %s, not retrying", city_name, response.status_code)
                return None

            # 429 (rate limited) or 5xx (server error): worth retrying.
            logger.warning(
                "%s: attempt %s/%s got %s",
                city_name, attempt, max_retries, response.status_code,
            )

        except (requests.Timeout, requests.ConnectionError) as e:
            logger.warning("%s: attempt %s/%s failed: %s", city_name, attempt, max_retries, e)

        # Exponential backoff: wait 1s, 2s, 4s... but not after the last attempt.
        if attempt < max_retries:
            time.sleep(2 ** (attempt - 1))

    logger.error("%s: giving up after %s attempts", city_name, max_retries)
    return None


def extract_all(cities: list[dict], api_key: str) -> list[dict]:
    """Fetch weather for every city; skip failures. Returns a list of raw JSON dicts."""
    results = []
    for city in cities:
        data = fetch_city_weather(city, api_key)
        if data is not None:
            results.append(data)

    logger.info("Extracted %s of %s cities", len(results), len(cities))

    if not results:
        # Every city failed: likely a bad key or the API is down. Fail loudly.
        raise RuntimeError("Extract failed: no city data was fetched")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cities = load_cities(CITIES_PATH)
    results = extract_all(cities, OPENWEATHER_API_KEY)
    print(f"Got {len(results)} results")
    print(json.dumps(results, indent=2, ensure_ascii=False))
