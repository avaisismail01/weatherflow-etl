"""Backfill: load past hourly weather so the database has history from day one.

Usage:  python backfill.py            # last 7 days
        python backfill.py --days 30  # up to 92 days
"""

import argparse
import logging
from datetime import datetime, timezone

import requests

from fetch_weather import CITIES, geocode_city
from load import DB_PATH, load
from transform import make_record, to_utc_iso

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("weatherflow.backfill")


def fetch_history(lat, lon, days):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m",
        "past_days": days,
        "forecast_days": 1,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def backfill(days=7):
    now = datetime.now(timezone.utc)
    fetched_at = now.isoformat()
    total = 0

    for city in CITIES:
        lat, lon = geocode_city(city)
        data = fetch_history(lat, lon, days)
        hourly = data["hourly"]

        records = []
        for time, temp, hum in zip(
            hourly["time"], hourly["temperature_2m"], hourly["relative_humidity_2m"]
        ):
            observed_at = to_utc_iso(time)
            if datetime.fromisoformat(observed_at) > now:
                continue  # skip forecast hours: we only store what already happened
            try:
                records.append(make_record(
                    city, data["latitude"], data["longitude"],
                    temp, hum, observed_at, fetched_at,
                ))
            except ValueError as exc:
                log.warning("Skipping bad reading: %s", exc)

        inserted = load(records)
        total += inserted
        log.info("%s: %d hourly readings, %d new", city, len(records), inserted)

    log.info("Backfill done: %d new reading(s) in %s", total, DB_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="days of history (1-92)")
    backfill(parser.parse_args().days)
