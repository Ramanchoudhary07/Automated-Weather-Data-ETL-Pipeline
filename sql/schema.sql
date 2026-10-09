CREATE TABLE IF NOT EXISTS dim_city (
    city_id INTEGER PRIMARY KEY,
    city_name TEXT NOT NULL,
    country TEXT,
    latitude NUMERIC(8,5),
    longitude NUMERIC(8,5)
);

CREATE TABLE IF NOT EXISTS fact_weather(
    city_id INTEGER REFERENCES dim_city(city_id),
    observed_at_utc  TIMESTAMP NOT NULL,
    temperature_c    NUMERIC(5,2),
    feels_like_c     NUMERIC(5,2),
    humidity_pct     INTEGER,
    pressure_hpa     INTEGER,
    wind_speed_ms    NUMERIC(5,2),
    weather_main     TEXT,
    loaded_at        TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (city_id, observed_at_utc)
);