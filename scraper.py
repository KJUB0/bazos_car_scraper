import argparse
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.bazos.sk"
SEARCH_URL = urljoin(BASE_URL, "/search.php")
DEFAULT_QUERY = "honda civic 1.8 vtec"

# resolved relative to the script so cron can run it from any directory
DB_PATH = Path(__file__).parent / "bazos_cars.db"

# listings cheaper than this are usually parts or wrecks, not whole cars
MIN_PRICE_EUR = 500

PAGE_SIZE = 20

REQUEST_DELAY = 1

HEADERS = {
    "User-Agent": "bazos-car-scraper/1.0 (+https://jakubferencik.com)"
}

logger = logging.getLogger(__name__)


def build_search_url(query, offset):
    params = {
        "hledat": query,
        "rubriky": "www",
        "hlokalita": "",
        "humkreis": 25,
        "cenaod": "",
        "cenado": "",
        "order": "",
        "kitx": "ano",
        "crz": offset,
    }
    return f"{SEARCH_URL}?{urlencode(params)}"


def download_page(url):
    logger.info("Downloading %s", url)

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
    except requests.RequestException as e:
        logger.error("Request failed: %s", e)
        return None

    if response.status_code != 200:
        logger.error("Unexpected HTTP status %s", response.status_code)
        return None

    return BeautifulSoup(response.text, "html.parser")


def find_listings(soup):
    return soup.find_all("div", {"class": "inzeraty inzeratyflex"})


def parse_price(raw_price):
    # "3 500 €" -> 3500, "Dohodou" -> None
    clean_price = "".join(raw_price.replace("€", "").split())
    if clean_price.isdigit():
        return int(clean_price)
    return None


def extract_listings(cards):
    listings = []
    for card in cards:
        title_element = card.find("h2", class_="nadpis")
        link_element = title_element.find("a") if title_element else None
        if not link_element or not link_element.get("href"):
            continue

        title = link_element.text.strip()
        link = urljoin(BASE_URL, link_element["href"])

        price_element = card.find("div", class_="inzeratycena")
        raw_price = price_element.text.strip() if price_element else None

        location_element = card.find("div", class_="inzeratylok")
        # the city and postcode are separated by <br>, so join the text parts with a space
        location = location_element.get_text(" ", strip=True) if location_element else None

        price_eur = parse_price(raw_price) if raw_price else None

        # skip parts and wrecks; listings without a numeric price ("Dohodou") are kept
        if price_eur is not None and price_eur < MIN_PRICE_EUR:
            continue

        listings.append({
            "link": link,
            "title": title,
            "price_eur": price_eur,
            "price_raw": raw_price,
            "location": location,
        })

    return listings


def init_db(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            link       TEXT PRIMARY KEY,
            title      TEXT,
            price_eur  INTEGER,
            price_raw  TEXT,
            location   TEXT,
            first_seen TEXT
        )
    """)
    connection.commit()


def save_listings(connection, listings):
    first_seen = datetime.now().isoformat(timespec="seconds")
    rows = [
        (item["link"], item["title"], item["price_eur"], item["price_raw"], item["location"], first_seen)
        for item in listings
    ]

    changes_before = connection.total_changes
    # link is the primary key, so INSERT OR IGNORE skips listings already stored
    connection.executemany(
        "INSERT OR IGNORE INTO cars (link, title, price_eur, price_raw, location, first_seen) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    connection.commit()
    return connection.total_changes - changes_before


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape used-car listings from bazos.sk into SQLite.")
    parser.add_argument(
        "query",
        nargs="?",
        default=DEFAULT_QUERY,
        help=f'search query (default: "{DEFAULT_QUERY}")',
    )
    return parser.parse_args()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    args = parse_args()
    logger.info('Searching for "%s", saving to %s', args.query, DB_PATH)

    connection = sqlite3.connect(DB_PATH)
    init_db(connection)

    offset = 0
    total_new = 0
    try:
        while True:
            soup = download_page(build_search_url(args.query, offset))
            if soup is None:
                logger.error("Could not load the page, stopping.")
                break

            cards = find_listings(soup)
            # no cards means we went past the last page
            if not cards:
                break

            listings = extract_listings(cards)
            new_rows = save_listings(connection, listings)
            total_new += new_rows
            logger.info(
                "Page at offset %d: %d cards, %d kept after filtering, %d new",
                offset, len(cards), len(listings), new_rows,
            )

            offset += PAGE_SIZE
            time.sleep(REQUEST_DELAY)
    finally:
        connection.close()

    logger.info("Done. %d new listings in total.", total_new)


if __name__ == "__main__":
    main()
