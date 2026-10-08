import logging

import pandas as pd

logger = logging.getLogger(__name__)

DIM_CITY_COLUMNS = ["city_id", "city_name", "country", "latitude", "longitude"]
FACT_WEATHER_COLUMNS = [
    "city_id",
    "observed_at_utc",
    "temperature_c",
    "feels_like_c",
    "humidity_pct",
    "pressure_hpa",
    "wind_speed_ms",
    "weather_main",
]


def flatten_record(raw: dict) -> dict:
    """Turn one nested API response into a flat dict (one future row)."""
    main = raw.get("main", {})
    weather = raw.get("weather", [])

    return {
        "city_id": raw["id"],
        "city_name": raw["name"],
        "country": raw.get("sys", {}).get("country"),
        "latitude": raw["coord"]["lat"],
        "longitude": raw["coord"]["lon"],
        "observed_at_utc": raw["dt"],
        "temperature_c": main.get("temp"),
        "feels_like_c": main.get("feels_like"),
        "humidity_pct": main.get("humidity"),
        "pressure_hpa": main.get("pressure"),
        "wind_speed_ms": raw.get("wind", {}).get("speed"),
        "weather_main": weather[0].get("main") if weather else None,
    }


def to_dataframe(raw_records: list[dict]) -> pd.DataFrame:
    """Flatten every raw record and build a DataFrame."""
    return pd.DataFrame([flatten_record(raw) for raw in raw_records])


def convert_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Convert observed_at_utc from Unix seconds to a naive UTC datetime."""
    df = df.copy()
    df["observed_at_utc"] = (
        pd.to_datetime(df["observed_at_utc"], unit="s", utc=True)
        .dt.tz_localize(None)
    )
    return df


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows that break the validation rules; log how many were dropped."""
    rows_before = len(df)

    df = df.dropna(subset=["city_id", "observed_at_utc"])
    df = df[df["temperature_c"].between(-90, 60)]
    df = df[df["humidity_pct"].between(0, 100)]
    df = df.drop_duplicates(subset=["city_id", "observed_at_utc"])

    rows_after = len(df)
    logger.info("Validation: kept %s of %s rows", rows_after, rows_before)
    if rows_after < rows_before:
        logger.warning("Validation: dropped %s invalid rows", rows_before - rows_after)

    return df


def split_dim_fact(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the clean DataFrame into dim_city and fact_weather DataFrames."""
    dim_city = df[DIM_CITY_COLUMNS].drop_duplicates(subset=["city_id"])
    fact_weather = df[FACT_WEATHER_COLUMNS]
    return dim_city, fact_weather


def transform(raw_records: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the full transform: flatten -> convert -> validate -> split."""
    df = to_dataframe(raw_records)
    df = convert_timestamps(df)
    df = validate(df)
    return split_dim_fact(df)


if __name__ == "__main__":
    from src.config import CITIES_PATH, OPENWEATHER_API_KEY
    from src.extract import extract_all, load_cities

    logging.basicConfig(level=logging.INFO)
    raw = extract_all(load_cities(CITIES_PATH), OPENWEATHER_API_KEY)
    dim_city, fact_weather = transform(raw)
    print(dim_city)
    print(fact_weather)
    print(fact_weather.dtypes)
