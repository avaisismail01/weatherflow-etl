"""Build charts from the weather database into docs/images/.

Usage:  python charts.py
"""

import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files, no window needed
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from load import DB_PATH

OUT_DIR = Path(__file__).parent / "docs" / "images"
COLORS = {"Berlin": "#0072B2", "Munich": "#E69F00", "Nuremberg": "#009E73"}  # colorblind-safe


def read_readings(db_path=DB_PATH):
    series = defaultdict(lambda: {"time": [], "temp": [], "hum": []})
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT city, observed_at, temperature_c, humidity_pct "
            "FROM weather_readings ORDER BY observed_at"
        )
        for city, observed_at, temp, hum in rows:
            s = series[city]
            s["time"].append(datetime.fromisoformat(observed_at))
            s["temp"].append(temp)
            s["hum"].append(hum)
    return series


def style_axis(ax, ylabel):
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)


def plot_timeseries(series):
    fig, (ax_t, ax_h) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for city, s in series.items():
        ax_t.plot(s["time"], s["temp"], label=city, color=COLORS.get(city), linewidth=1.6)
        ax_h.plot(s["time"], s["hum"], label=city, color=COLORS.get(city), linewidth=1.6)

    ax_t.set_title("Hourly temperature and humidity (UTC)", loc="left", fontsize=14, weight="bold")
    ax_t.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    style_axis(ax_t, "Temperature (°C)")
    style_axis(ax_h, "Relative humidity (%)")
    ax_h.set_ylim(0, 100)
    ax_h.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax_t.legend(frameon=False, ncol=len(series), loc="upper right")

    fig.tight_layout()
    path = OUT_DIR / "hourly_weather.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_daily_range(series):
    """Daily min / average / max temperature per city."""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    cities = list(series)
    width = 0.8 / len(cities)

    all_days = sorted({t.date() for s in series.values() for t in s["time"]})
    for i, city in enumerate(cities):
        by_day = defaultdict(list)
        for t, temp in zip(series[city]["time"], series[city]["temp"]):
            by_day[t.date()].append(temp)
        xs = [d_i + (i - (len(cities) - 1) / 2) * width
              for d_i, d in enumerate(all_days) if d in by_day]
        days = [d for d in all_days if d in by_day]
        lows = [min(by_day[d]) for d in days]
        highs = [max(by_day[d]) for d in days]
        means = [sum(by_day[d]) / len(by_day[d]) for d in days]

        ax.bar(xs, [h - l for h, l in zip(highs, lows)], bottom=lows, width=width * 0.9,
               color=COLORS.get(city), alpha=0.35, label=city)
        ax.scatter(xs, means, color=COLORS.get(city), s=22, zorder=3)
        overall_low = min(lows + [overall_low]) if i else min(lows)
        overall_high = max(highs + [overall_high]) if i else max(highs)

    ax.set_ylim(overall_low - 1, overall_high + 2.5)  # room for legend, nothing clipped
    ax.set_xticks(range(len(all_days)), [d.strftime("%d %b") for d in all_days])
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_title("Daily temperature range (bar = min to max, dot = average)",
                 loc="left", fontsize=14, weight="bold")
    style_axis(ax, "Temperature (°C)")
    ax.legend(frameon=False, ncol=len(cities), loc="upper right")

    fig.tight_layout()
    path = OUT_DIR / "daily_temperature_range.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = read_readings()
    for p in (plot_timeseries(data), plot_daily_range(data)):
        print(f"Saved {p}")
