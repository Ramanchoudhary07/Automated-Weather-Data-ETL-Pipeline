# CLAUDE.md — Weather Data ETL Pipeline

This file gives Claude Code the context for this project. Read it before helping.

## About me and why this project exists

- I'm Raman Choudhary, a B.Tech Chemical Engineering graduate (SVNIT Surat, 2026) applying for **Data Engineer** roles.
- My resume has two EDA projects (Retail Sales Analysis with SQL/Pandas, Customer Churn EDA with Seaborn). I need one **engineering-focused Python project** to show I can build pipelines, not just analyse data.
- This project will replace the Professional Summary on my one-page resume.
- **I already know:** Python basics, Pandas, SQL (joins, CTEs, window functions), PostgreSQL/MySQL, Git/GitHub, Jupyter.
- **I'm new to:** writing Python as modules/scripts (not notebooks), REST APIs, psycopg2/SQLAlchemy, upserts, data modeling, Docker, Airflow, pytest, logging.
- **My machine:** Windows 11, VS Code, Python 3.11. Docker Desktop (WSL2) is needed later.

## How Claude should help me (important)

I'll have to explain every line of this project in interviews, so **teach me, don't just build it for me.**

- Explain the concept first, then show a small example. Let me write the main logic myself when I ask for guidance.
- When I ask "how do I do X", give hints or a skeleton with TODOs before a full solution, unless I explicitly ask for the full code.
- When reviewing my code, point out bugs and better practices and explain *why*.
- Keep code simple and readable. Don't add abstractions, frameworks or features beyond the current milestone.
- Point out things interviewers commonly ask about (idempotency, failure handling, scaling, schema design).
- Use Windows-friendly commands (PowerShell or Git Bash). Mention Windows-specific gotchas.
- Never commit secrets. API keys go in `.env`, which is git-ignored.

## Project goal

An automated pipeline that, every day:
1. **Extracts** current weather data for a list of cities from the OpenWeatherMap API.
2. **Transforms** and validates it with Pandas.
3. **Loads** it incrementally into PostgreSQL (a star schema) using idempotent upserts.
4. Is **scheduled** (cron/Task Scheduler first, then Airflow), **containerised** (Docker Compose), **tested** (pytest) and **logged**.

Data source alternatives if needed: CoinGecko (crypto, no key needed) or Open-Meteo (weather, no key needed).

## Tech stack

| Layer | Tool |
|---|---|
| Language | Python 3.11 |
| Extract | `requests` |
| Transform | `pandas` |
| Load | PostgreSQL 16, `psycopg2-binary` (or SQLAlchemy) |
| Config | `python-dotenv`, `.env` file |
| Logging | Python `logging` module |
| Testing | `pytest` |
| Containers | Docker, Docker Compose |
| Orchestration | Apache Airflow (via official docker-compose); cron/Task Scheduler before that |
| Version control | Git + GitHub |

## Planned folder structure

```
weather-etl-pipeline/
├── CLAUDE.md
├── README.md               # architecture diagram, setup steps, sample queries
├── .env.example            # template of required env vars (no real secrets)
├── .env                    # real secrets — git-ignored
├── .gitignore              # .env, venv/, __pycache__/, *.log, logs/
├── requirements.txt
├── config/
│   └── cities.json         # list of cities to fetch
├── src/
│   ├── __init__.py
│   ├── config.py           # loads env vars and settings
│   ├── extract.py          # API calls with retries/timeouts
│   ├── transform.py        # pure functions: DataFrame in -> DataFrame out
│   ├── load.py             # DB connection, create tables, upserts
│   ├── logger.py           # logging setup
│   └── pipeline.py         # runs extract -> transform -> load
├── sql/
│   ├── schema.sql          # CREATE TABLE statements
│   └── analysis.sql        # sample analytical queries for README
├── tests/
│   ├── test_transform.py
│   └── test_extract.py     # mock the API with sample JSON
├── dags/
│   └── weather_dag.py      # Airflow DAG (milestone 5)
├── Dockerfile
└── docker-compose.yml
```

## Data model (star schema)

```sql
-- dimension: one row per city
CREATE TABLE IF NOT EXISTS dim_city (
    city_id      INTEGER PRIMARY KEY,      -- OpenWeatherMap city id
    city_name    TEXT NOT NULL,
    country      TEXT,
    latitude     NUMERIC(8,5),
    longitude    NUMERIC(8,5)
);

-- fact: one row per city per observation time
CREATE TABLE IF NOT EXISTS fact_weather (
    city_id          INTEGER REFERENCES dim_city(city_id),
    observed_at_utc  TIMESTAMP NOT NULL,
    temperature_c    NUMERIC(5,2),
    feels_like_c     NUMERIC(5,2),
    humidity_pct     INTEGER,
    pressure_hpa     INTEGER,
    wind_speed_ms    NUMERIC(5,2),
    weather_main     TEXT,
    loaded_at        TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    PRIMARY KEY (city_id, observed_at_utc)  -- makes reruns idempotent
);
```

Loads use `INSERT ... ON CONFLICT (...) DO UPDATE` so running the pipeline twice never creates duplicates.

## Conventions

- Scripts and modules, not notebooks. Run with `python -m src.pipeline` from the project root.
- Small, single-purpose functions with type hints and short docstrings.
- Transform functions are **pure** (no API/DB calls) so they're easy to unit test.
- Store all timestamps in **UTC**.
- Use `logging`, not `print`. Log row counts at each stage (extracted / valid / loaded).
- Use parameterised SQL queries, never string-formatted SQL.
- API calls: set a timeout, retry up to 3 times with backoff, respect rate limits.
- Validation rules: no nulls in `city_id`/`observed_at_utc`, temperature between -90 and 60 °C, humidity 0–100, drop duplicates on the primary key.
- Commit after each working step with clear messages.

## Milestones (update the checkboxes as I go)

### Milestone 1: Local end-to-end (week 1)
- [x] Create venv, `requirements.txt`, `.gitignore`, `.env.example`; init Git repo
- [x] Get an OpenWeatherMap API key; fetch one city and print the JSON
- [x] `extract.py`: fetch all cities from `config/cities.json`, with timeout + retries
- [x] `transform.py`: flatten JSON -> DataFrame, convert units/timestamps, validate
- [x] Run PostgreSQL locally (installer or Docker) and create tables from `sql/schema.sql`
- [x] `load.py`: upsert `dim_city` and `fact_weather`
- [x] `pipeline.py`: run everything end to end; check data in Postgres

### Milestone 2: Make it solid (week 2)
- [x] Logging setup with row counts and errors
- [x] Config via `.env` (API key, DB credentials)
- [ ] Prove idempotency: run twice, row count unchanged
- [x] pytest tests for transform and validation functions; mock API responses for extract
- [ ] Push to GitHub

### Milestone 3: Docker (week 3)
- [ ] `Dockerfile` for the pipeline
- [ ] `docker-compose.yml` with `postgres` + `pipeline` services and a volume for DB data
- [ ] One-command run: `docker compose up`

### Milestone 4: Scheduling
- [ ] Simple schedule first (Windows Task Scheduler or cron in a container)

### Milestone 5: Airflow
- [ ] Run Airflow with the official docker-compose
- [ ] `dags/weather_dag.py`: extract -> transform -> load tasks, daily schedule, retries
- [ ] Screenshot of a successful DAG run for the README

### Milestone 6: Polish
- [ ] README: overview, architecture diagram, tech stack, setup, sample queries/results, what I'd improve
- [ ] `sql/analysis.sql`: e.g. hottest city per day, 7-day rolling average temperature (window functions)
- [ ] Record real numbers for my resume (cities, rows loaded, runtime, tests)

## Common commands (Windows)

```bash
python -m venv venv
venv\Scripts\activate            # PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.pipeline
pytest -v
docker compose up --build
docker compose down
```

## Interview questions this project must prepare me for

1. How do you prevent duplicates if the pipeline runs twice? (Primary key + upsert = idempotency)
2. What happens if the API is down or returns bad data? (Retries, validation, logging, failing loudly)
3. Why a star schema? What are facts vs. dimensions?
4. Full load vs. incremental load: which did you use and why?
5. How would you scale to 10,000 cities or hourly data? (Batching, async requests, partitioning, Spark)
6. Why Airflow instead of cron? (Dependencies, retries, monitoring, backfills)
7. How do you test a data pipeline?

## Target resume entry (fill in real numbers once built)

GitHub repo: https://github.com/Ramanchoudhary07/Automated-Weather-Data-ETL-Pipeline

The resume currently lists this project as "Oct 2026 – Present" with "Building / Designing" wording. Once the milestones are done, switch it to the past-tense version below with real numbers.

**Automated Weather Data ETL Pipeline** — *Python | PostgreSQL | Airflow | Docker | Pandas*
- Built an automated pipeline that ingests daily weather data for N cities from the OpenWeatherMap API into PostgreSQL.
- Wrote modular, unit-tested transformation and validation functions in Pandas (timestamps, missing values, deduplication).
- Designed a star schema with incremental, idempotent upserts so reruns are safe and nothing gets duplicated.
- Orchestrated daily runs with Airflow DAGs and containerised the stack with Docker Compose for one-command setup.
- Added pytest tests and structured logging; documented the architecture and setup in the GitHub README.

## Learning resources

- Real Python: `requests`, `logging`, `pytest` tutorials
- postgresqltutorial.com: data types, upsert (`ON CONFLICT`)
- Docker "Getting Started" guide; TechWorld with Nana (YouTube)
- Airflow official tutorial + "Running Airflow in Docker"
- DataTalksClub Data Engineering Zoomcamp (free on GitHub/YouTube)
