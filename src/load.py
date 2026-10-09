import logging

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from src.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

logger = logging.getLogger(__name__)

UPSERT_DIM_CITY = """
    INSERT INTO dim_city (city_id, city_name, country, latitude, longitude)
    VALUES %s
    ON CONFLICT (city_id) DO UPDATE SET
        city_name = EXCLUDED.city_name,
        country   = EXCLUDED.country,
        latitude  = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude
"""

UPSERT_FACT_WEATHER = """
    INSERT INTO fact_weather (
        city_id, observed_at_utc, temperature_c, feels_like_c,
        humidity_pct, pressure_hpa, wind_speed_ms, weather_main
    )
    VALUES %s
    ON CONFLICT (city_id, observed_at_utc) DO UPDATE SET
        temperature_c = EXCLUDED.temperature_c,
        feels_like_c  = EXCLUDED.feels_like_c,
        humidity_pct  = EXCLUDED.humidity_pct,
        pressure_hpa  = EXCLUDED.pressure_hpa,
        wind_speed_ms = EXCLUDED.wind_speed_ms,
        weather_main  = EXCLUDED.weather_main,
        loaded_at     = NOW() AT TIME ZONE 'UTC'
"""


def get_connection():
    """Open a connection to Postgres using settings from .env."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )


def df_to_rows(df: pd.DataFrame) -> list[tuple]:
    """Convert a DataFrame to plain-Python tuples, turning NaN into None (SQL NULL)."""
    clean = df.astype(object).where(df.notna(), None)
    return list(clean.itertuples(index=False, name=None))


def upsert(cur, sql: str, df: pd.DataFrame) -> int:
    """Upsert all rows of df using sql; return the number of rows sent."""
    rows = df_to_rows(df)
    execute_values(cur, sql, rows)
    return len(rows)


def load(dim_city: pd.DataFrame, fact_weather: pd.DataFrame) -> None:
    """Upsert both tables in a single transaction."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # dim_city first: fact_weather.city_id has a foreign key to it.
                city_count = upsert(cur, UPSERT_DIM_CITY, dim_city)
                logger.info("Upserted %s rows into dim_city", city_count)

                fact_count = upsert(cur, UPSERT_FACT_WEATHER, fact_weather)
                logger.info("Upserted %s rows into fact_weather", fact_count)
    finally:
        conn.close()


if __name__ == "__main__":
    from src.config import CITIES_PATH, OPENWEATHER_API_KEY
    from src.extract import extract_all, load_cities
    from src.transform import transform

    logging.basicConfig(level=logging.INFO)
    raw = extract_all(load_cities(CITIES_PATH), OPENWEATHER_API_KEY)
    dim_city, fact_weather = transform(raw)
    load(dim_city, fact_weather)
