"""Run the full WeatherFlow ETL pipeline: Extract -> Transform -> Load."""

import logging
import sys

from fetch_weather import CITIES, fetch_weather, geocode_city
from load import DB_PATH, load
from transform import transform

LOG_PATH = DB_PATH.parent / "pipeline.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Log to the console and to data/pipeline.log (so scheduled runs leave a record)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8")]
    # Scheduled runs use pythonw.exe, which has no console (sys.stderr is None)
    + ([logging.StreamHandler()] if sys.stderr else []),
)
log = logging.getLogger("weatherflow")


def run():
    records = []
    for city in CITIES:
        try:
            lat, lon = geocode_city(city)            # Extract
            raw = fetch_weather(city, lat, lon)
            record = transform(raw)                  # Transform
            records.append(record)
            log.info("%s: %.1f°C, %d%% humidity",
                     city, record["temperature_c"], record["humidity_pct"])
        except Exception as exc:
            # One failing city should not stop the others
            log.error("Skipping %s: %s", city, exc)

    inserted = load(records)                         # Load
    log.info("Loaded %d new reading(s) into %s (%d duplicate(s) skipped)",
             inserted, DB_PATH, len(records) - inserted)
    return inserted


if __name__ == "__main__":
    run()
