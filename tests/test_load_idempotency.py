import psycopg2
import pytest

from src.load import get_connection, load
from src.transform import transform

# A city id OpenWeatherMap never uses, so test rows can't clash with real data.
TEST_CITY_ID = -1

pytestmark = pytest.mark.integration


def make_raw(temp: float) -> dict:
    """One fake API response for the test city."""
    return {
        "id": TEST_CITY_ID,
        "name": "Test City",
        "sys": {"country": "XX"},
        "coord": {"lat": 10.0, "lon": 20.0},
        "dt": 1791468108,
        "main": {"temp": temp, "feels_like": temp, "humidity": 50, "pressure": 1000},
        "wind": {"speed": 1.0},
        "weather": [{"main": "Clear"}],
    }


def query_one(sql: str):
    """Run a query and return the first column of the first row."""
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sql, (TEST_CITY_ID,))
            return cur.fetchone()[0]
    finally:
        conn.close()


def delete_test_rows() -> None:
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            # fact first: it references dim_city
            cur.execute("DELETE FROM fact_weather WHERE city_id = %s", (TEST_CITY_ID,))
            cur.execute("DELETE FROM dim_city WHERE city_id = %s", (TEST_CITY_ID,))
    finally:
        conn.close()


@pytest.fixture
def clean_db():
    """Skip if Postgres isn't reachable; remove test rows before and after the test."""
    try:
        delete_test_rows()
    except psycopg2.OperationalError:
        pytest.skip("PostgreSQL is not available")
    yield
    delete_test_rows()


def test_loading_same_data_twice_does_not_duplicate(clean_db):
    dim_city, fact_weather = transform([make_raw(temp=25.0)])

    load(dim_city, fact_weather)
    load(dim_city, fact_weather)

    assert query_one("SELECT COUNT(*) FROM dim_city WHERE city_id = %s") == 1
    assert query_one("SELECT COUNT(*) FROM fact_weather WHERE city_id = %s") == 1


def test_reloading_updates_existing_row(clean_db):
    load(*transform([make_raw(temp=25.0)]))
    load(*transform([make_raw(temp=26.5)]))  # same city + time, corrected value

    assert query_one("SELECT COUNT(*) FROM fact_weather WHERE city_id = %s") == 1
    temp = query_one("SELECT temperature_c FROM fact_weather WHERE city_id = %s")
    assert float(temp) == 26.5
