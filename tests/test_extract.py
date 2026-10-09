import json
from unittest.mock import Mock

import pytest
import requests

from src import extract
from src.extract import extract_all, fetch_city_weather, load_cities

CITY = {"name": "London", "country": "GB"}


def fake_response(status_code: int, data: dict | None = None) -> Mock:
    """A stand-in for requests.Response with just the parts extract.py uses."""
    response = Mock()
    response.status_code = status_code
    response.json.return_value = data or {}
    return response


@pytest.fixture
def fake_get(monkeypatch):
    """Replace requests.get inside extract.py with a Mock we control."""
    mock_get = Mock()
    monkeypatch.setattr(extract.requests, "get", mock_get)
    return mock_get


@pytest.fixture
def fake_sleep(monkeypatch):
    """Replace time.sleep so retry tests don't actually wait."""
    mock_sleep = Mock()
    monkeypatch.setattr(extract.time, "sleep", mock_sleep)
    return mock_sleep


# ---------- load_cities ----------

def test_load_cities_reads_json(tmp_path):
    path = tmp_path / "cities.json"
    path.write_text(json.dumps([CITY]), encoding="utf-8")

    assert load_cities(str(path)) == [CITY]


# ---------- fetch_city_weather ----------

def test_fetch_success_returns_json(fake_get, fake_sleep):
    fake_get.return_value = fake_response(200, {"id": 1})

    result = fetch_city_weather(CITY, "key")

    assert result == {"id": 1}
    assert fake_get.call_count == 1
    fake_sleep.assert_not_called()


def test_fetch_sends_city_and_metric_units(fake_get, fake_sleep):
    fake_get.return_value = fake_response(200)

    fetch_city_weather(CITY, "key")

    params = fake_get.call_args.kwargs["params"]
    assert params["q"] == "London,GB"
    assert params["units"] == "metric"
    assert fake_get.call_args.kwargs["timeout"] == 10


@pytest.mark.parametrize("status", [401, 404])
def test_fetch_client_error_does_not_retry(fake_get, fake_sleep, status):
    fake_get.return_value = fake_response(status)

    result = fetch_city_weather(CITY, "key")

    assert result is None
    assert fake_get.call_count == 1
    fake_sleep.assert_not_called()


def test_fetch_retries_server_error_then_succeeds(fake_get, fake_sleep):
    fake_get.side_effect = [fake_response(500), fake_response(503), fake_response(200, {"id": 1})]

    result = fetch_city_weather(CITY, "key")

    assert result == {"id": 1}
    assert fake_get.call_count == 3


def test_fetch_gives_up_after_max_retries_with_backoff(fake_get, fake_sleep):
    fake_get.return_value = fake_response(429)

    result = fetch_city_weather(CITY, "key", max_retries=3)

    assert result is None
    assert fake_get.call_count == 3
    # Waits 1s then 2s between attempts, and not after the last one.
    assert [c.args[0] for c in fake_sleep.call_args_list] == [1, 2]


def test_fetch_retries_on_timeout(fake_get, fake_sleep):
    fake_get.side_effect = [requests.Timeout("too slow"), fake_response(200, {"id": 1})]

    result = fetch_city_weather(CITY, "key")

    assert result == {"id": 1}
    assert fake_get.call_count == 2


# ---------- extract_all ----------

def test_extract_all_skips_failed_cities(fake_get, fake_sleep):
    fake_get.side_effect = [fake_response(200, {"id": 1}), fake_response(404)]

    results = extract_all([CITY, {"name": "Nowhere", "country": "IN"}], "key")

    assert results == [{"id": 1}]


def test_extract_all_raises_when_every_city_fails(fake_get, fake_sleep):
    fake_get.return_value = fake_response(401)

    with pytest.raises(RuntimeError):
        extract_all([CITY, CITY], "key")
