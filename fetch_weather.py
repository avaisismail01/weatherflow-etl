import requests
import json
from datetime import datetime, timezone

CITIES = ["Berlin", "Munich", "Nuremberg"]

def geocode_city(city_name):
    """Turn a city name into (lat, lon), preferring Germany matches."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 10}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        raise ValueError(f"No geocoding results for {city_name}")

    # Prefer a German match; fall back to the first result otherwise
    for r in results:
        if r["country_code"] == "DE":
            return r["latitude"], r["longitude"]
    return results[0]["latitude"], results[0]["longitude"]

def fetch_weather(city_name, lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    data["city"] = city_name
    data["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return data

if __name__ == "__main__":
    for city in CITIES:
        lat, lon = geocode_city(city)
        weather = fetch_weather(city, lat, lon)
        print(json.dumps(weather, indent=2))