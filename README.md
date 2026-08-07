# Books to Scrape — Responsible Web Scraper

A small, polite web-scraping pipeline built for the FlyRank internship.

The scraper discovers the first three catalogue pages of Books to Scrape, collects the 60 book detail pages, extracts raw data, normalizes and validates the records, handles individual page failures, and produces a final JSON dataset and run report.

## Target Classification

### Target

**Books to Scrape**
https://books.toscrape.com/

Books to Scrape is a sandbox website specifically created for people to practise web scraping. This makes it an appropriate target for this assignment.

### Scope

The scraper processes **only the first three catalogue pages** and the book pages discovered from those pages.

The expected dataset contains 60 unique books.

### Data collected

Each final record contains:

* `title`
* `product_url`
* `price_text`
* `price_gbp`
* `availability_text`
* `rating_text`
* `description`
* `source_page`
* `fetched_at`

Only the publicly displayed book information needed for the assignment is collected.

### robots.txt

Before building the scraper, the site's robots.txt was checked at:

`https://books.toscrape.com/robots.txt`

The result was reviewed before making requests to the site.

**I will not reuse this code on another site without checking its rules and terms first.**

## Project Structure

```text
scraper/
├── README.md
├── .gitignore
├── requirements.txt
├── output/
│   ├── books.json
│   ├── errors.json
│   └── run-report.json
└── src/
    └── main.py
```

The request cache is intentionally not committed to the repository.

## Installation

Python 3.11+ is recommended.

From the `scraper` directory:

```bash
pip install -r requirements.txt
```

## Run

From the `scraper` directory:

```bash
python src/main.py
```

The scraper writes:

```text
output/books.json
output/errors.json
output/run-report.json
```

A stranger can clone this repository, install the two dependencies, run the command above, and reproduce the output without needing any API keys or external credentials.

## Record Schema

The final record has this shape:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "...",
  "source_page": "https://books.toscrape.com/",
  "fetched_at": "2026-08-08T00:00:00Z"
}
```

The schema is defined with Pydantic.

`price_text` preserves the original value from the page while `price_gbp` stores the normalized numeric value.

`description` is optional and is stored as `null` when the source page does not provide one.

The canonical `product_url` is used as the record identity, preventing duplicate records.

Records that fail validation are written to `output/errors.json` with the reason for failure instead of being added to `books.json`.

## Politeness Rules

This scraper follows several simple rules:

* **User-Agent:** identifies the scraper and links to this public repository.
* **Timeout:** requests have a 5-second timeout so they never wait indefinitely.
* **Status checking:** only HTTP 200 responses are accepted as successful pages.
* **Delay:** real requests are separated by at least 0.5 seconds.
* **Caching:** downloaded catalogue and detail pages are cached locally during development so repeated runs do not repeatedly request the site.
* **Limited scope:** only the first three catalogue pages are processed.

Timeouts and server errors are retried once. HTTP 403 and 404 responses are not retried.

## Idempotency

The output files are overwritten rather than appended to.

The canonical product URL is used to remove duplicate records.

Therefore, running the scraper multiple times produces the same 60-book dataset rather than adding another copy of the records.

## Failure Handling

Each book page is processed independently.

If one page fails, the scraper records the failure and continues processing the remaining pages.

The run report records:

* `start_time`
* `duration_seconds`
* `pages_fetched`
* `cache_hits`
* `valid_records`
* `invalid_records`
* `failed_pages`

A local failure test using a deliberately nonexistent book URL confirmed that one failed page does not prevent the 60 valid records from being produced.

## Sample Run Report

The following is a real run-report produced by the scraper:

```json
{
  "start_time": "PASTE YOUR REAL RUN REPORT HERE",
  "duration_seconds": 0,
  "pages_fetched": 0,
  "cache_hits": 0,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

## Why No Browser?

A browser is not needed because the required book data is already present in the HTML sent by the server. Using a browser would only add unnecessary cost and complexity.

## Ethics Note

This scraper is intentionally limited to a sandbox designed for scraping practice.

When scraping other websites, use an official API when one exists. Never bypass logins, paywalls, access controls, or blocks, and collect only the information that is actually needed.

## Limitation

This scraper is intentionally designed for the Books to Scrape sandbox and a fixed three-page scope. Its selectors and assumptions may not work unchanged on a different website or on a substantially different page structure.

## Evidence

The repository contains the final normalized `books.json`, the run report, the validation/error output, and the source code needed to reproduce them.

The development history is divided into meaningful commits for each stage of the assignment.
