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
