## Project Overview
This is an automated data collection tool written in Python. It scrapes used-car listings from [bazos.sk](https://www.bazos.sk), cleans the data, and stores it in a structured SQLite database.

Unlike a simple "page downloader," this script includes logic to filter out noise (e.g., spare parts disguised as cars) and deduplicates entries to ensure the dataset remains clean for future analysis.

### Features
* Parsing: Extracts price, location, title, and direct links from unstructured HTML.
* Noise Filtering: Automatically ignores listings under €500 to filter out wrecks, spare parts, and irrelevant accessories. Listings without a numeric price (e.g. "Dohodou") are kept.
* Deduplication: The listing link is the table's primary key, so a listing that is already stored is skipped (`INSERT OR IGNORE`).
* Storage: Stores all data in a local SQLite database (`bazos_cars.db`, next to the script).
* Configurable search: The search query is a command-line argument.
* Analysis: `analyze.py` draws charts from the collected data.
* Web interface: `web.py` serves a simple page for browsing, filtering and sorting the stored listings (Python standard library only).

### Technical Implementation
The scraper goes through the search results page by page until there are no more listings:

1. Request & Parse: Fetches the search results using `requests` (10 s timeout) and parses the HTML with BeautifulSoup4. Network errors are logged and stop the run cleanly.
2. Data Cleaning:
   * Normalizes prices (removes "€" and spaces) into an integer `price_eur`.
   * Keeps the original price text in `price_raw`, so non-numeric prices are not lost.
   * Turns relative links into absolute URLs.
3. Storage: Inserts the listings with parameterized `INSERT OR IGNORE` queries and logs how many new listings each page added.
4. Rate Limiting: Waits 1 second between page requests and identifies itself with an honest User-Agent (`bazos-car-scraper/1.0`).

### Database Schema
Table `cars`:

| Column       | Type    | Description                                                        |
|--------------|---------|--------------------------------------------------------------------|
| `link`       | TEXT    | Absolute URL of the listing (primary key)                          |
| `title`      | TEXT    | Listing title                                                      |
| `price_eur`  | INTEGER | Price in EUR, `NULL` if the price is not a number (e.g. "Dohodou") |
| `price_raw`  | TEXT    | Price exactly as shown on the site                                 |
| `location`   | TEXT    | Location text from the listing                                     |
| `first_seen` | TEXT    | ISO timestamp (local time) of when the scraper first stored it     |

### How to run
```bash
# create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# scrape with the default query ("honda civic 1.8 vtec")
python scraper.py

# scrape with a custom query
python scraper.py "skoda octavia"

# generate charts into docs/
python analyze.py

# browse the listings at http://127.0.0.1:8000
python web.py

# on the homelab: make the page reachable from other devices on the local network
python web.py --host 0.0.0.0 --port 8000

# look at the data
sqlite3 bazos_cars.db "SELECT title, price_eur, location FROM cars ORDER BY first_seen DESC LIMIT 10;"
```

### Charts
`analyze.py` saves these charts to `docs/`:

* `docs/price_histogram.png` - distribution of listing prices
* `docs/new_listings_per_day.png` - number of new listings per day

_Charts will be added here once enough data has been collected._

<!--
![Price histogram](docs/price_histogram.png)
![New listings per day](docs/new_listings_per_day.png)
-->

### Deployment (Homelab)
This script is deployed on my Debian-based homelab server and scheduled via cron to run every hour. Because the database path is resolved relative to the script, it does not matter which directory cron starts it from.

```bash
0 * * * * /home/user/scripts/bazos_scraper/.venv/bin/python /home/user/scripts/bazos_scraper/scraper.py >> /home/user/scripts/bazos_scraper/scraper.log 2>&1
```


Copyright

© 2026 Jakub Ferencik. All Rights Reserved.
