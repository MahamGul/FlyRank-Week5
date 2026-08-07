from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pydantic import BaseModel, HttpUrl
import hashlib
import json
import re
import time


BASE_URL = "https://books.toscrape.com/"
TIMEOUT = 5
MIN_DELAY = 0.5

BASE_DIR = Path(__file__).resolve().parent.parent

CACHE_DIR = BASE_DIR / "cache"
DETAIL_CACHE_DIR = CACHE_DIR / "details"
FETCH_TIMES_FILE = CACHE_DIR / "detail-fetch-times.json"

OUTPUT_DIR = BASE_DIR / "output"
BOOKS_FILE = OUTPUT_DIR / "books.json"
ERRORS_FILE = OUTPUT_DIR / "errors.json"

USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/MahamGul/FlyRank-Week5)"
)


# -----------------------------
# Stage 4 schema
# -----------------------------

class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: str | None
    source_page: HttpUrl
    fetched_at: str


# -----------------------------
# Utility functions
# -----------------------------

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def cache_filename(url):
    url_hash = hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:16]

    return DETAIL_CACHE_DIR / f"{url_hash}.html"


def load_fetch_times():
    if FETCH_TIMES_FILE.exists():
        return json.loads(
            FETCH_TIMES_FILE.read_text(encoding="utf-8")
        )

    return {}


def save_fetch_times(fetch_times):
    FETCH_TIMES_FILE.write_text(
        json.dumps(fetch_times, indent=2),
        encoding="utf-8"
    )


# -----------------------------
# Fetch + cache
# -----------------------------
def fetch_page(page_url, cache_file, stats):

    fetch_times = load_fetch_times()

    # -------------------------
    # Use cache if available
    # -------------------------
    if cache_file.exists():

        html = cache_file.read_bytes()

        fetched_at = fetch_times.get(
            str(cache_file)
        )

        stats["cache_hits"] += 1

        print(f"CACHE HIT: {cache_file.name}")

        return html, fetched_at

    # -------------------------
    # Real request
    # -------------------------
    request = Request(
        page_url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    max_attempts = 2
    attempt = 1

    while attempt <= max_attempts:

        try:

            with urlopen(
                request,
                timeout=TIMEOUT
            ) as response:

                status = response.status

                # Only 200 is accepted.
                if status != 200:

                    if 500 <= status <= 599 and attempt == 1:

                        print(
                            f"HTTP {status} — retrying once"
                        )

                        time.sleep(1)
                        attempt += 1
                        continue

                    raise RuntimeError(
                        f"HTTP {status}"
                    )

                html = response.read()

                fetched_at = utc_now()

                cache_file.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                cache_file.write_bytes(html)

                fetch_times[str(cache_file)] = fetched_at

                save_fetch_times(fetch_times)

                stats["pages_fetched"] += 1

                print(f"FETCH: {page_url}")

                return html, fetched_at

        except HTTPError as error:

            # 403 and 404 are permanent failures.
            if error.code in (403, 404):

                raise RuntimeError(
                    f"HTTP {error.code}"
                )

            # Retry a 5xx once.
            if (
                500 <= error.code <= 599
                and attempt == 1
            ):

                print(
                    f"HTTP {error.code} — retrying once"
                )

                time.sleep(1)

                attempt += 1
                continue

            raise RuntimeError(
                f"HTTP {error.code}"
            )

        except (TimeoutError, URLError) as error:

            # Retry once for timeout/network failure.
            if attempt == 1:

                print(
                    "Request failed — retrying once"
                )

                time.sleep(1)

                attempt += 1
                continue

            raise RuntimeError(
                f"Request failed: {error}"
            )

    raise RuntimeError(
        "Request failed after retry"
    )


# -----------------------------
# Discover catalogue pages
# -----------------------------

def discover_catalogue_pages(stats):

    catalogue_pages = []

    # URL → source catalogue page
    book_urls = {}

    current_url = BASE_URL

    for page_number in range(1, 4):

        cache_file = (
            CACHE_DIR
            / f"catalogue-page-{page_number}.html"
        )

        if (
            not cache_file.exists()
            and page_number > 1
        ):
            time.sleep(MIN_DELAY)

        html, _ = fetch_page(
            current_url,
            cache_file,
            stats
        )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        catalogue_pages.append(
            current_url
        )

        for article in soup.select(
            "article.product_pod"
        ):

            link = article.select_one(
                "h3 a"
            )

            if link and link.get("href"):

                absolute_url = urljoin(
                    current_url,
                    link["href"]
                )

                if absolute_url not in book_urls:

                    book_urls[
                        absolute_url
                    ] = current_url

        next_link = soup.select_one(
            "li.next a"
        )

        if (
            next_link
            and next_link.get("href")
        ):

            current_url = urljoin(
                current_url,
                next_link["href"]
            )

        else:
            break

    return catalogue_pages, book_urls


# -----------------------------
# Extract raw detail record
# -----------------------------

def extract_rating(product_main):

    rating_element = product_main.select_one(
        "p.star-rating"
    )

    if not rating_element:
        return None

    classes = rating_element.get(
        "class",
        []
    )

    for rating in [
        "One",
        "Two",
        "Three",
        "Four",
        "Five"
    ]:

        if rating in classes:
            return rating

    return None


def extract_raw_record(
    product_url,
    source_page,
    html,
    fetched_at
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    product_main = soup.select_one(
        "div.product_main"
    )

    if not product_main:

        raise RuntimeError(
            f"Product area not found: {product_url}"
        )

    title_element = product_main.select_one(
        "h1"
    )

    price_element = product_main.select_one(
        "p.price_color"
    )

    availability_element = product_main.select_one(
        "p.availability"
    )

    description_element = soup.select_one(
        "#product_description + p"
    )

    title = (
        title_element.get_text(
            strip=True
        )
        if title_element
        else None
    )

    price_text = (
        price_element.get_text(
            " ",
            strip=True
        )
        if price_element
        else None
    )

    availability_text = (
        availability_element.get_text(
            " ",
            strip=True
        )
        if availability_element
        else None
    )

    rating_text = extract_rating(
        product_main
    )

    description = (
        description_element.get_text(
            " ",
            strip=True
        )
        if description_element
        else None
    )

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


# -----------------------------
# Extract all books
# -----------------------------

def extract_all_books(book_urls, stats):

    records = []
    failed_pages = []

    for index, (
        product_url,
        source_page
    ) in enumerate(
        book_urls.items(),
        start=1
    ):

        cache_file = cache_filename(
            product_url
        )

        try:

            # Delay only before a real request.
            if (
                not cache_file.exists()
                and index > 1
            ):
                time.sleep(MIN_DELAY)

            html, fetched_at = fetch_page(
                product_url,
                cache_file,
                stats
            )

            record = extract_raw_record(
                product_url,
                source_page,
                html,
                fetched_at
            )

            records.append(record)

        except Exception as error:

            stats["failed_pages"] += 1

            failed_pages.append({
                "product_url": product_url,
                "source_page": source_page,
                "reason": str(error)
            })

            print(
                f"FAILED: {product_url}"
            )

            print(
                f"Reason: {error}"
            )

            # Continue with the next book.
            continue

    return records, failed_pages


# -----------------------------
# Normalize price
# -----------------------------

def normalize_price(price_text):

    if not price_text:
        raise ValueError(
            "Missing price_text"
        )

    match = re.search(
        r"([0-9]+(?:\.[0-9]+)?)",
        price_text
    )

    if not match:
        raise ValueError(
            f"Could not parse price: {price_text}"
        )

    return float(match.group(1))


# -----------------------------
# Validate + store
# -----------------------------

def validate_records(raw_records):

    valid_records = []

    errors = []

    seen_urls = set()

    for index, raw_record in enumerate(
        raw_records,
        start=1
    ):

        try:

            product_url = raw_record.get(
                "product_url"
            )

            # Canonical URL is the record identity.
            if product_url in seen_urls:
                continue

            seen_urls.add(product_url)

            normalized_record = {
                **raw_record,
                "price_gbp": normalize_price(
                    raw_record.get(
                        "price_text"
                    )
                )
            }

            validated = BookRecord.model_validate(
                normalized_record
            )

            valid_records.append(
                validated.model_dump(
                    mode="json"
                )
            )

        except Exception as error:

            errors.append({
                "record": raw_record,
                "reason": str(error)
            })

    return valid_records, errors


def save_outputs(
    valid_records,
    errors
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Overwrite instead of append.
    # This makes the run idempotent.
    BOOKS_FILE.write_text(
        json.dumps(
            valid_records,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    ERRORS_FILE.write_text(
        json.dumps(
            errors,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# -----------------------------
# Run report
# -----------------------------

def save_run_report(
    start_time,
    stats,
    valid_records,
    errors,
    failed_pages
):

    start = datetime.fromisoformat(
        start_time.replace("Z", "+00:00")
    )

    end = datetime.now(timezone.utc)

    duration = (
        end - start
    ).total_seconds()

    report = {
        "start_time": start_time,
        "duration_seconds": duration,
        "pages_fetched": stats["pages_fetched"],
        "cache_hits": stats["cache_hits"],
        "valid_records": len(valid_records),
        "invalid_records": len(errors),
        "failed_pages": len(failed_pages)
    }

    report_file = (
        OUTPUT_DIR / "run-report.json"
    )

    report_file.write_text(
        json.dumps(
            report,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("Run report:")
    print(
        json.dumps(
            report,
            indent=2
        )
    )


# -----------------------------
# Main
# -----------------------------

def main():

    start_time = utc_now()

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DETAIL_CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    stats = {
        "pages_fetched": 0,
        "cache_hits": 0,
        "failed_pages": 0,
    }

    # Discover the three catalogue pages.
    catalogue_pages, book_urls = (
        discover_catalogue_pages(stats)
    )

    # ---------------------------------
    # TEMPORARY Stage 5 failure test
    # Remove these two lines after the
    # checkpoint is confirmed, then run
    # once more before the final commit.
    # ---------------------------------

    

    # ---------------------------------

    raw_records, failed_pages = (
        extract_all_books(
            book_urls,
            stats
        )
    )

    valid_records, errors = (
        validate_records(
            raw_records
        )
    )

    save_outputs(
        valid_records,
        errors
    )

    save_run_report(
        start_time,
        stats,
        valid_records,
        errors,
        failed_pages
    )

    print()

    print(
        f"catalogue_pages={len(catalogue_pages)}"
    )

    print(
        f"detail_pages={len(raw_records)}"
    )

    print(
        f"valid_records={len(valid_records)}"
    )

    print(
        f"errors={len(errors)}"
    )

    print(
        f"failed_pages={len(failed_pages)}"
    )


if __name__ == "__main__":
    main()