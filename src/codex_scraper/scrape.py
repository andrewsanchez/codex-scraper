from __future__ import annotations

"""
Minimal standalone scraper scaffold.
Agents must set URL and OUTPUT_FILE and implement extraction/writing.
"""

from playwright.sync_api import sync_playwright
import sys


URL = "REPLACE_ME_URL"
OUTPUT_FILE = "REPLACE_ME_OUTPUT_FILE"


def scrape() -> None:
    if not URL or URL == "REPLACE_ME_URL" or not OUTPUT_FILE or OUTPUT_FILE == "REPLACE_ME_OUTPUT_FILE":
        raise SystemExit("Set URL and OUTPUT_FILE in src/codex_scraper/scrape.py")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=30000)
        # Implement extraction and write to OUTPUT_FILE
        browser.close()


if __name__ == "__main__":
    scrape()

