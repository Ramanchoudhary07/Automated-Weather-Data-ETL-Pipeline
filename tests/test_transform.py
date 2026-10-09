import pandas as pd
import pytest

from src.transform import (
    convert_timestamps,
    flatten_record,
    split_dim_fact,
    to_dataframe,
    validate,
)


@pytest.fixture
def sample_raw():
    """One API response, trimmed to the fields we use."""
    return {
        "id": 1270407,
        "name": "Hanumangarh",
        "sys": {"country": "IN"},
        "coord": {"lat": 29.5833, "lon": 74.3167},
        "dt": 1791468108,
        "main": {"temp": 31.36, "feels_like": 30.21, "humidity": 31, "pressure": 1010},
        "wind": {"speed": 3.62},
        "weather": [{"main": "Clear"}],
    }


def prepare(records: list[dict]) -> pd.DataFrame:
    """Flatten and convert records: the steps that run before validate."""
    return convert_timestamps(to_dataframe(records))


# ---------- flatten_record ----------

def test_flatten_record_maps_fields(sample_raw):
    row = flatten_record(sample_raw)

    assert row["city_id"] == 1270407
    assert row["country"] == "IN"
    assert row["temperature_c"] == 31.36
    assert row["weather_main"] == "Clear"


def test_flatten_record_empty_weather_gives_none(sample_raw):
    sample_raw["weather"] = []

    row = flatten_record(sample_raw)

    assert row["weather_main"] is None


# ---------- convert_timestamps ----------

def test_convert_timestamps_gives_naive_utc(sample_raw):
    df = prepare([sample_raw])

    observed = df["observed_at_utc"].iloc[0]

    assert observed == pd.Timestamp("2026-10-08 14:01:48")
    assert observed.tz is None


# ---------- validate ----------

def test_validate_drops_out_of_range_temperature(sample_raw):
    hot = {**sample_raw, "id": 2, "main": {**sample_raw["main"], "temp": 304.5}}

    result = validate(prepare([sample_raw, hot]))

    assert len(result) == 1
    assert result["city_id"].iloc[0] == 1270407


def test_validate_drops_bad_humidity(sample_raw):
    humid = {**sample_raw, "id": 2, "main": {**sample_raw["main"], "humidity": 150}}

    result = validate(prepare([sample_raw, humid]))

    assert len(result) == 1
    assert result["city_id"].iloc[0] == 1270407


def test_validate_drops_duplicate_rows(sample_raw):
    result = validate(prepare([sample_raw, sample_raw]))

    assert len(result) == 1


def test_validate_keeps_good_rows(sample_raw):
    result = validate(prepare([sample_raw]))

    assert len(result) == 1


# ---------- split_dim_fact ----------

def test_split_dim_fact_one_row_per_city(sample_raw):
    later = {**sample_raw, "dt": sample_raw["dt"] + 3600}

    dim_city, fact_weather = split_dim_fact(validate(prepare([sample_raw, later])))

    assert len(dim_city) == 1
    assert len(fact_weather) == 2
