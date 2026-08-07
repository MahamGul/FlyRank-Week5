from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
import time


BASE_URL = "https://books.toscrape.com/"
TIMEOUT = 5
MIN_DELAY = 0.5

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"

USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/MahamGul/FlyRank-Week5)"
)


def fetch_page(page_url, cache_file):
    """
    Return HTML from cache if available.
    Otherwise fetch it from the website and cache it.
    """

    if cache_file.exists():
        html = cache_file.read_bytes()
        print(f"CACHE HIT: {cache_file.name}")
        return html

    request = Request(
        page_url,
        headers={"User-Agent": USER_AGENT}
    )

    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Fetch failed: HTTP {response.status}"
                )

            html = response.read()

    except HTTPError as error:
        raise RuntimeError(
            f"Fetch failed: HTTP {error.code}"
        )

    except URLError as error:
        raise RuntimeError(
            f"Fetch failed: {error.reason}"
        )

    cache_file.write_bytes(html)

    print(f"FETCH: {page_url}")

    return html


def discover_catalogue_pages():
    catalogue_pages = []
    book_urls = set()

    current_url = BASE_URL

    for page_number in range(1, 4):

        cache_file = CACHE_DIR / f"catalogue-page-{page_number}.html"

        # Delay only when making a real request.
        if not cache_file.exists() and page_number > 1:
            time.sleep(MIN_DELAY)

        html = fetch_page(current_url, cache_file)

        soup = BeautifulSoup(html, "html.parser")

        catalogue_pages.append(current_url)

        # Find every book link on this catalogue page.
        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")

            if link and link.get("href"):
                absolute_url = urljoin(current_url, link["href"])
                book_urls.add(absolute_url)

        # Follow the catalogue's own "next" link.
        next_link = soup.select_one("li.next a")

        if next_link and next_link.get("href"):
            current_url = urljoin(current_url, next_link["href"])
        else:
            break

    return catalogue_pages, book_urls


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    catalogue_pages, book_urls = discover_catalogue_pages()

    print()
    print(f"catalogue_pages={len(catalogue_pages)}")
    print(f"discovered={len(book_urls)}")
    print(f"unique_urls={len(book_urls)}")


if __name__ == "__main__":
    main()