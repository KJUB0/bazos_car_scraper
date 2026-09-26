import logging
import sqlite3
from pathlib import Path

import matplotlib

# render to files only, no display needed on a headless server
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DB_PATH = Path(__file__).parent / "bazos_cars.db"
DOCS_DIR = Path(__file__).parent / "docs"

BAR_COLOR = "#2a78d6"
TEXT_COLOR = "#52514e"

logger = logging.getLogger(__name__)


def load_prices(connection):
    rows = connection.execute("SELECT price_eur FROM cars WHERE price_eur IS NOT NULL").fetchall()
    return [row[0] for row in rows]


def load_new_per_day(connection):
    rows = connection.execute("""
        SELECT substr(first_seen, 1, 10) AS day, COUNT(*)
        FROM cars
        WHERE first_seen IS NOT NULL
        GROUP BY day
        ORDER BY day
    """).fetchall()
    days = [row[0] for row in rows]
    counts = [row[1] for row in rows]
    return days, counts


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e0e0e0", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=TEXT_COLOR)
    ax.yaxis.get_major_locator().set_params(integer=True)


def plot_price_histogram(prices, output_path):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bins = min(20, max(1, len(prices)))
    ax.hist(prices, bins=bins, color=BAR_COLOR, edgecolor="white", linewidth=1)
    ax.set_title(f"Listing prices (n = {len(prices)})")
    ax.set_xlabel("Price (EUR)")
    ax.set_ylabel("Number of listings")
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_new_per_day(days, counts, output_path):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    positions = range(len(days))
    ax.bar(positions, counts, width=0.6, color=BAR_COLOR)
    ax.set_xticks(positions, days)
    # with only a day or two of data, leave room for at least 7 bars so one bar isn't page-wide
    ax.set_xlim(-0.5, max(len(days), 7) - 0.5)
    ax.set_title("New listings per day")
    ax.set_xlabel("Date first seen")
    ax.set_ylabel("New listings")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if not DB_PATH.exists():
        logger.error("Database %s not found. Run scraper.py first.", DB_PATH)
        return

    DOCS_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    try:
        prices = load_prices(connection)
        days, counts = load_new_per_day(connection)
    finally:
        connection.close()

    if prices:
        output_path = DOCS_DIR / "price_histogram.png"
        plot_price_histogram(prices, output_path)
        logger.info("Saved %s", output_path)
    else:
        logger.warning("No numeric prices in the database, skipping the price histogram.")

    if days:
        output_path = DOCS_DIR / "new_listings_per_day.png"
        plot_new_per_day(days, counts, output_path)
        logger.info("Saved %s", output_path)
    else:
        logger.warning("No listings in the database, skipping the listings-per-day chart.")


if __name__ == "__main__":
    main()
