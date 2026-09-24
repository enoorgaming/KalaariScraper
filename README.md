# Kalaari Scraper

A Python scraper for [Kalaari Capital](https://kalaari.com)'s portfolio page. It
collects the list of portfolio companies and visits each company's page to pull
structured data about the investment.

## What it collects

For every portfolio company:

- **Name**
- **Sector** (B2B / ConsumerTech / DeepTech / AI-SaaS / etc.)
- **Investing stage & year**
- **Founding year**
- **Status** (Active / Partial Exit / Exit)
- **One-line description**
- **"Why Did Kalaari Invest" text**

## Setup

Requires Python 3. Install the dependencies:

```bash
pip install requests beautifulsoup4
```

## Usage

```bash
python Kalaari.py
```

The scraper is polite — it waits 0.5 seconds between requests.

## Output

Two files are written to the current folder:

| File | Description |
|------|-------------|
| `kalaari_portfolio.csv` | One row per company |
| `kalaari_portfolio.json` | Same data, nested JSON |

Sample output from a previous run is included in this repo.

## How it works

1. `get_portfolio_links()` — scrapes the main portfolio page for every company URL.
2. `scrape_company_page(url)` — visits a company page and extracts the fields above
   using a mix of HTML parsing (BeautifulSoup) and regex fallbacks, since the site's
   Webflow markup varies.
3. `main()` — loops through all companies and writes the CSV and JSON.

## Note

This scraper depends on the current structure of kalaari.com. If the site's layout
changes, the parsing logic may need updating.
