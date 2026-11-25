"""Load step: store clean weather records in a local SQLite database."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "weather.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS weather_readings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    city          TEXT    NOT NULL,
    latitude      REAL    NOT NULL,
    longitude     REAL    NOT NULL,
    temperature_c REAL    NOT NULL,
    humidity_pct  INTEGER NOT NULL,
    observed_at   TEXT    NOT NULL,
    fetched_at    TEXT    NOT NULL,
    UNIQUE (city, observed_at)
);
"""


def get_connection(db_path=DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    return conn


def load(records, db_path=DB_PATH):
    """Insert records; skip any reading already stored (same city + time).

    Returns the number of new rows inserted.
    """
    with get_connection(db_path) as conn:
        before = conn.total_changes
        conn.executemany(
            """
            INSERT OR IGNORE INTO weather_readings
                (city, latitude, longitude, temperature_c, humidity_pct,
                 observed_at, fetched_at)
            VALUES
                (:city, :latitude, :longitude, :temperature_c, :humidity_pct,
                 :observed_at, :fetched_at)
            """,
            records,
        )
        return conn.total_changes - before
