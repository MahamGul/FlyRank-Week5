# Books to Scrape — Responsible Scraping Setup

## Target Classification

### Target site

**Books to Scrape**
https://books.toscrape.com/

### Why this site?

Books to Scrape is a sandbox website created specifically for people to practise web scraping. The site explains that it is intended for scraping practice, so it is an appropriate and authorized target for this assignment.

This project is limited to this sandbox site and does not target real-world websites.

### How much will be collected?

The scraper will collect data from **only the first 3 catalogue pages**.

This limited scope keeps the number of requests small and is sufficient for demonstrating the scraping workflow.

### What data will be collected?

For each book, the scraper will collect:

* Book title
* Price
* Availability
* Rating
* Product URL

Only publicly displayed catalogue information relevant to the assignment will be collected.

### Why is this appropriate?

The information is publicly displayed on the Books to Scrape practice website, and the website is specifically designed for learning and testing scraping techniques. The collection is also limited to the first three catalogue pages rather than attempting to crawl the entire site.

## robots.txt Check

I checked the site's robots.txt file at:

`https://books.toscrape.com/robots.txt`

The file was available and was checked before starting the scraper. Its contents were reviewed to understand the site's instructions to automated agents.

## Scraping Principles

* The scraper will remain within the defined three-page scope.
* Requests will be kept limited and reasonable.
* No login-protected, private, or sensitive information will be collected.
* This project is intended only for the Books to Scrape sandbox.

**I will not reuse this code on another site without checking its rules and terms first.**

## Stage 1 — Fetch and Cache

The first catalogue page is fetched from Books to Scrape using an identifying User-Agent and a 5-second timeout.

The script checks the HTTP response status before processing the response and accepts only HTTP 200 as a successful fetch.

On the first run, the HTML response is saved to:

`cache/catalogue-page-1.html`

During development, subsequent runs use this cached copy instead of requesting the website again. The script reports whether it performed a `FETCH` or received a `CACHE HIT`, along with the response size, without printing the full HTML.

## Stage 2 — Discover Three Catalogue Pages

The scraper parses the saved catalogue HTML using Beautiful Soup and discovers the book links on each catalogue page.

Starting from page 1, the scraper follows the catalogue's own `next` link to page 2 and then page 3. It stops after three catalogue pages as required by the assignment.

Relative book links are converted into absolute URLs using Python's `urljoin()` rather than by manually concatenating strings.

The scraper removes duplicate book URLs using a set. A delay of at least 0.5 seconds is used between real requests to the website. Cached pages do not require a delay because they are read locally.

The expected checkpoint is:

`catalogue_pages=3, discovered=60, unique_urls=60`

A second run should produce the same counts while using the cached catalogue pages instead of requesting them again.

## Stage 3 — Extract Raw Book Records

The scraper now visits each of the 60 book detail pages discovered from the first three catalogue pages.

Each detail page is fetched with the same identifying User-Agent, timeout, HTTP status validation, and minimum 0.5-second delay used for real requests in the previous stages. Detail pages are cached locally so subsequent development runs do not repeatedly request the website.

The raw record contains eight fields:

* `title`
* `product_url`
* `price_text`
* `availability_text`
* `rating_text`
* `description`
* `source_page`
* `fetched_at`

Selectors are scoped to the product area of each page rather than relying on the first matching element in the entire document.

If a description is absent, the value is stored as `null` rather than being invented.

The `source_page` field records which catalogue page led to the book, while `fetched_at` records when the detail page was originally fetched. These fields provide provenance for each raw record.

The checkpoint for this stage is:

`detail_pages=60`

The script also prints one complete raw record showing all eight keys.

## Stage 4 — Validate Normalized Records

Raw book records are normalized and validated before being stored.

The `price_text` value is preserved exactly as collected, while a numeric `price_gbp` value is derived from it for sorting and comparison.

A Pydantic schema defines the expected shape and types of each finished record. The canonical `product_url` is used as the record identity, and duplicate URLs are removed.

Every record is validated against the schema before being written to `output/books.json`. Records that fail normalization or validation are written to `output/errors.json` together with the reason for failure.

The description field is optional and may contain `null` when the source page does not provide a description.

The output files are overwritten on each run rather than appended to. This makes the scraper idempotent: running it multiple times produces the same set of records instead of creating duplicates.

The checkpoint for this stage is:

* `books.json` contains exactly 60 records.
* Every `price_gbp` value is numeric.
* Every `product_url` begins with `https://`.
* A second run still produces exactly 60 records.

## Stage 5 — Failure Handling and Run Reporting

Each book detail page is processed independently so that a failed page does not stop the rest of the run.

A timeout or HTTP 5xx server error is retried once after a short delay. HTTP 403 and 404 responses are treated as permanent failures and are not retried.

Failed pages are logged and skipped while successful records continue through normalization and validation.

Every run produces `output/run-report.json` containing:

* `start_time`
* `duration_seconds`
* `pages_fetched`
* `cache_hits`
* `valid_records`
* `invalid_records`
* `failed_pages`

For the failure-handling test, one intentionally nonexistent book URL was added to the discovered URL list. The scraper completed the run without crashing, preserved the 60 valid records, and reported one failed page.

The fake URL was used only for local failure testing and was removed from the normal scraper afterward.
