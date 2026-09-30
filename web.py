import argparse
import json
import logging
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DB_PATH = Path(__file__).parent / "bazos_cars.db"
INDEX_PATH = Path(__file__).parent / "static" / "index.html"

logger = logging.getLogger(__name__)


def load_cars():
    if not DB_PATH.exists():
        return []

    # read-only, so the web page can never modify the data
    connection = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT link, title, price_eur, price_raw, location, mileage_km, first_seen "
            "FROM cars ORDER BY first_seen DESC"
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_body(200, "text/html; charset=utf-8", INDEX_PATH.read_bytes())
        elif self.path == "/api/cars":
            body = json.dumps(load_cars(), ensure_ascii=False).encode("utf-8")
            self.send_body(200, "application/json; charset=utf-8", body)
        else:
            self.send_body(404, "text/plain; charset=utf-8", b"Not found")

    def send_body(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logger.info("%s %s", self.address_string(), format % args)


def parse_args():
    parser = argparse.ArgumentParser(description="Serve a simple web page with the scraped listings.")
    # 127.0.0.1 = only this computer; use 0.0.0.0 to open it to the local network
    parser.add_argument("--host", default="127.0.0.1", help="address to listen on (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port to listen on (default: 8000)")
    return parser.parse_args()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    args = parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    logger.info("Serving on http://%s:%d (Ctrl+C to stop)", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
