import requests
from pathlib import Path

RAW_DIR = Path("data/raw")

SOURCES = {
    "free-look-period": "https://policyholder.gov.in/free-look-period",
    "rejection-of-claims": "https://policyholder.gov.in/rejection-of-claims",
    "renewability": "https://policyholder.gov.in/home"
}

HEADERS = {"User-Agent": "Mozilla/5.0 (InsureClear student project)"}


def fetch_one(slug, url):
    """Download one page into data/raw/<slug>.html. Returns the path, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=(5, 15))
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[HTTP ERROR] {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {url}: {e}")
        return None

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{slug}.html"
    path.write_text(resp.text, encoding="utf-8")
    print(f"[OK] {slug} -> {path} ({len(resp.text)} chars)")
    return path


def fetch_all():
    return {slug: fetch_one(slug, url) for slug, url in SOURCES.items()}


if __name__ == "__main__":
    fetch_all()