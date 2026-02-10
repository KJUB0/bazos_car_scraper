## Project Overview
This is an automated data collection tool written in Python. It scrapes car listings, cleans the data, and stores it in a structured SQLite database.

Unlike a simple "page downloader," this script includes logic to filter out noise (e.g., spare parts disguised as cars) and deduplicates entries to ensure the dataset remains clean for future analysis.

### Features
* Parsing: Extracts price, location, title, and direct links from unstructured HTML.
* Noise Filtering: Automatically ignores listings under €500 to filter out wrecks, spare parts, and irrelevant accessories.
* Deduplication: Uses Pandas to check the existing database before inserting, ensuring only new market entries are saved.
* Storage: Stores all data in a local sqlite3 database for easy querying and visualization.

### Technical Implementation
the scraper operates in a continuous loop until all pages are searched through:  

1. Request & Parse: Fetches the search results using requests and parses the DOM with BeautifulSoup4.
2. Data Cleaning:
   * Normalizes prices (removes "€", spaces).
   * Handles non-numeric prices (e.g., "Dohodou").
3. Storage Logic:
   * Loads existing links from the bazos_cars.db database.
   * Compares new scrape results against the DB.
   * Appends only unique new offers to the SQL table.
4. Rate Limiting: Includes sleep timers to behave politely towards the server.

### Deployment (Homelab)
This script is currently deployed on my Debian-based homelab server. It is scheduled via cron to run at fixed intervals, ensuring the database is always up-to-date without manual intervention.

```bash
0 * * * * /usr/bin/python3 /home/user/scripts/bazos_scraper/main.py >> /var/log/scraper.log 2>&1
```


Copyright

© 2026 Jakub Ferencik. All Rights Reserved.
