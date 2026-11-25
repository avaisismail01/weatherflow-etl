"""Transform step: turn raw Open-Meteo API responses into clean, flat records."""

from datetime import datetime, timezone


def transform(raw):
    """Convert one raw API response into a flat dict ready for the database.

    Raises ValueError if required fields are missing or values are out of range,
    so bad data never reaches the database.
    """
    current = raw.get("current")
    if not current:
        raise ValueError(f"No 'current' block in response for {raw.get('city')}")

    temperature = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    if temperature is None or humidity is None:
        raise ValueError(f"Missing temperature or humidity for {raw.get('city')}")

    # Basic sanity checks: reject physically impossible readings
    if not -90 <= temperature <= 60:
        raise ValueError(f"Temperature {temperature} out of range for {raw['city']}")
    if not 0 <= humidity <= 100:
        raise ValueError(f"Humidity {humidity} out of range for {raw['city']}")

    # Open-Meteo returns times in GMT like "2026-11-26T10:15"; make it explicit UTC
    observed_at = (
        datetime.fromisoformat(current["time"])
        .replace(tzinfo=timezone.utc)
        .isoformat()
    )

    return {
        "city": raw["city"],
        "latitude": round(raw["latitude"], 4),
        "longitude": round(raw["longitude"], 4),
        "temperature_c": float(temperature),
        "humidity_pct": int(humidity),
        "observed_at": observed_at,
        "fetched_at": raw["fetched_at"],
    }
