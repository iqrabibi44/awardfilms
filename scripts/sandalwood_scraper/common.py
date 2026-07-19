"""
common.py
Shared helpers for all award-ceremony scrapers.

Uses the Wikipedia REST/Action API (not raw HTML scraping) for stability:
- https://en.wikipedia.org/w/api.php?action=parse  -> returns page HTML we can parse with BeautifulSoup
This avoids brittle CSS-selector scraping of the live site rendering.
"""

import os
import re
import csv
import time
import logging
import hashlib
import requests
from bs4 import BeautifulSoup

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "TollywoodAwardsResearchBot/1.0 (contact: awardfilms.com dataset project)"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("scraper")

SCHEMA = [
    "award_show", "year", "ceremony_edition", "category",
    "nominee_name", "work_title", "role_or_character",
    "result", "language", "source_url",
]

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".wiki_cache"))


def fetch_wikipedia_html(page_title: str, retries: int = 3, sleep: float = 1.0) -> str:
    """Fetch the rendered HTML body of a Wikipedia article via the Action API with local file caching."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    filename = hashlib.md5(page_title.encode("utf-8")).hexdigest() + ".html"
    cache_path = os.path.join(CACHE_DIR, filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            content = f.read()
            if content.strip():
                return content

    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text",
        "redirects": 1,
    }
    last_err = None
    for attempt in range(retries):
        # Respect rate limits and sleep 1 second between non-cached requests
        time.sleep(1.0)
        try:
            resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(data["error"])
            html_content = data["parse"]["text"]["*"]
            
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            return html_content
        except Exception as e:  # noqa: BLE001
            last_err = e
            log.warning("Fetch failed for '%s' (attempt %d/%d): %s", page_title, attempt + 1, retries, e)
            time.sleep(sleep * (attempt + 1))
    raise RuntimeError(f"Could not fetch '{page_title}': {last_err}")


def clean_text(s: str) -> str:
    """Strip footnote markers, citation brackets, and extra whitespace."""
    if s is None:
        return ""
    s = re.sub(r"\[\d+\]", "", s)          # [1], [23]
    s = re.sub(r"\[citation needed\]", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" \u2021\u2020*†‡|")    # strip winner-marker symbols too


def page_url(page_title: str) -> str:
    return "https://en.wikipedia.org/wiki/" + page_title.replace(" ", "_")


def get_tables(html: str):
    """Return all wikitable elements from a parsed Wikipedia page."""
    soup = BeautifulSoup(html, "lxml")
    return soup.find_all("table", class_=re.compile("wikitable"))


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(SCHEMA)
        w.writerows(rows)
    log.info("Wrote %d rows -> %s", len(rows), path)


def write_gaps(gaps, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["award_show", "year", "category", "reason"])
        w.writerows(gaps)
    log.info("Wrote %d gap entries -> %s", len(gaps), path)
