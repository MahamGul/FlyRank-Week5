from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


URL = "https://books.toscrape.com/"
TIMEOUT = 5

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_FILE = CACHE_DIR / "catalogue-page-1.html"

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/MahamGul/FlyRank-Week5)"


def fetch_and_cache():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if CACHE_FILE.exists():
        html = CACHE_FILE.read_bytes()
        print("CACHE HIT")
        print(f"Response size: {len(html)} bytes")
        return

    request = Request(
        URL,
        headers={"User-Agent": USER_AGENT}
    )

    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            status_code = response.status

            if status_code != 200:
                print(f"FETCH FAILED: HTTP {status_code}")
                return

            html = response.read()

    except HTTPError as error:
        print(f"FETCH FAILED: HTTP {error.code}")
        return

    except URLError as error:
        print(f"FETCH FAILED: {error.reason}")
        return

    CACHE_FILE.write_bytes(html)

    print("FETCH")
    print(f"Response size: {len(html)} bytes")
    print(f"Saved to: {CACHE_FILE}")


if __name__ == "__main__":
    fetch_and_cache()