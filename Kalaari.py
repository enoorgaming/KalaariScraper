"""
Kalaari Capital Portfolio Scraper
----------------------------------
Scrapes kalaari.com/portfolio for the list of portfolio companies,
then visits each company's page to pull:
  - Company name
  - Sector (B2B / ConsumerTech / DeepTech / AI-SaaS)
  - Stage & year invested
  - Founding year
  - Status (Active / Partial Exit / Exit)
  - One-line description
  - "Why Did Kalaari Invest" text

Usage:
    pip install requests beautifulsoup4 --break-system-packages
    python kalaari_scraper.py

Output:
    kalaari_portfolio.csv  (one row per company)
    kalaari_portfolio.json (same data, nested)
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import re

BASE_URL = "https://kalaari.com"
PORTFOLIO_URL = f"{BASE_URL}/portfolio"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def get_portfolio_links():
    """Scrape the main portfolio page for all individual company page URLs."""
    resp = requests.get(PORTFOLIO_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")

    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/portfolio/" in href and href.rstrip("/") != "/portfolio":
            # Normalize to absolute URL
            if href.startswith("http"):
                links.add(href)
            else:
                links.add(BASE_URL + href)

    return sorted(links)


def scrape_company_page(url):
    """Extract structured data from a single company's portfolio page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding  # avoid garbled smart-quotes/apostrophes
    except requests.RequestException as e:
        print(f"  [!] Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")

    data = {
        "url": url,
        "name": None,
        "description": None,
        "sector": None,
        "stage_year": None,
        "founding_year": None,
        "status": None,
        "why_invested": None,
    }

    # Company name: derive from the URL slug. The page's first <h1> is a
    # newsletter signup header, not the company name.
    data["name"] = url.rstrip("/").split("/")[-1].replace("-", " ").title()

    # One-line description: often an H2 right after leadership/founding info
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]
    if h2s:
        # Filter out generic headers like "Leadership" or "Related"
        candidates = [h for h in h2s if h.lower() not in ("leadership", "related")]
        if candidates:
            data["description"] = candidates[0]

    # "Why Did Kalaari Invest" section
    why_header = soup.find(
        lambda tag: tag.name in ("h2", "h3")
        and "why did kalaari invest" in tag.get_text(strip=True).lower()
    )
    if why_header:
        # Grab the next sibling paragraph(s) until the next header
        paras = []
        for sib in why_header.find_all_next():
            if sib.name in ("h1", "h2", "h3"):
                break
            if sib.name == "p":
                paras.append(sib.get_text(strip=True))
        data["why_invested"] = " ".join(paras).strip() or None

    # Founding Year / Status / Stage — these appear as label-value pairs in the DOM.
    # We do a simple regex pass over the raw text as a fallback since Webflow's
    # markup for these varies.
    m = re.search(r"Founding Year\s*\n?\s*(\d{4})", text)
    if m:
        data["founding_year"] = m.group(1)

    m = re.search(r"Status\s*\n?\s*([A-Za-z ]+)\n", text)
    if m:
        data["status"] = m.group(1).strip()

    m = re.search(r"Investing Stage & Year\s*\n?\s*([A-Za-z0-9, ]+)\n", text)
    if m:
        data["stage_year"] = m.group(1).strip()

    # Sector tags: Webflow often repeats these near the top; grab known sector words
    for sector in ("B2B", "ConsumerTech", "DeepTech", "AI/SaaS", "Enterprise AI", "Gaming"):
        if sector in text:
            data["sector"] = sector
            break

    return data


def main():
    print("Fetching portfolio company list...")
    links = get_portfolio_links()
    print(f"Found {len(links)} portfolio company pages.\n")

    results = []
    for i, url in enumerate(links, 1):
        print(f"[{i}/{len(links)}] Scraping {url}")
        data = scrape_company_page(url)
        if data:
            results.append(data)
        time.sleep(0.5)  # be polite to their server

    # Write CSV
    with open("kalaari_portfolio.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name", "sector", "stage_year", "founding_year",
                "status", "description", "why_invested", "url",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    # Write JSON
    with open("kalaari_portfolio.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Wrote {len(results)} companies to kalaari_portfolio.csv and kalaari_portfolio.json")


if __name__ == "__main__":
    main()