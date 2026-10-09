"""Airflow DAG: extract -> transform -> load, once a day.

The ETL logic lives in src/ (unit-tested, runnable without Airflow).
This file only wires those functions into Airflow tasks.
"""
from datetime import datetime, timedelta

from airflow.sdk import dag, task


@dag(
    schedule="@daily",
    start_date=datetime(2026, 10, 1),
    catchup=False,  # don't backfill every day since start_date on first deploy
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["weather", "etl"],
)
def weather_etl():
    # Imports live inside the tasks: the DAG file is parsed every few seconds,
    # so keeping heavy imports like pandas out of the top level keeps parsing fast.

    @task
    def extract() -> list[dict]:
        from src.config import CITIES_PATH, OPENWEATHER_API_KEY
        from src.extract import extract_all, load_cities

        return extract_all(load_cities(CITIES_PATH), OPENWEATHER_API_KEY)

    @task
    def transform(raw_records: list[dict]) -> dict:
        from src.transform import transform as run_transform

        dim_city, fact_weather = run_transform(raw_records)
        return {"dim_city": dim_city, "fact_weather": fact_weather}

    @task
    def load(tables: dict) -> None:
        from src.load import load as run_load

        run_load(tables["dim_city"], tables["fact_weather"])

    load(transform(extract()))


weather_etl()
