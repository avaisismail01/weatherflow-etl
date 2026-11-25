"""Transform step: turn raw Open-Meteo API responses into clean, flat records."""

from datetime import datetime, timezone


def to_utc_iso(api_time):
    """Open-Meteo returns times in GMT like "2026-11-26T10:15"; make it explicit UTC."""
    return datetime.fromisoformat(api_time).replace(tzinfo=timezone.utc).isoformat()


def make_record(city, latitude, longitude, temperature, humidity, observed_at, fetched_at):
    """Build one validated record.

    Raises ValueError if values are missing or out of range,
    so bad data never reaches the database.
    """
    if temperature is None or humidity is None:
        raise ValueError(f"Missing temperature or humidity for {city} at {observed_at}")

    # Basic sanity checks: reject physically impossible readings
    if not -90 <= temperature <= 60:
        raise ValueError(f"Temperature {temperature} out of range for {city}")
    if not 0 <= humidity <= 100:
        raise ValueError(f"Humidity {humidity} out of range for {city}")

    return {
        "city": city,
        "latitude": round(latitude, 4),
        "longitude": round(longitude, 4),
        "temperature_c": float(temperature),
        "humidity_pct": int(humidity),
        "observed_at": observed_at,
        "fetched_at": fetched_at,
    }


def transform(raw):
    """Convert one raw 'current weather' API response into a flat record."""
    current = raw.get("current")
    if not current:
        raise ValueError(f"No 'current' block in response for {raw.get('city')}")

    return make_record(
        raw["city"],
        raw["latitude"],
        raw["longitude"],
        current.get("temperature_2m"),
        current.get("relative_humidity_2m"),
        to_utc_iso(current["time"]),
        raw["fetched_at"],
    )
