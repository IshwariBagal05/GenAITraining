import hashlib
from pathlib import Path
from bs4 import BeautifulSoup

for p in sorted(Path("data/raw").glob("*.html")):
    html = p.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    print(p.name, hashlib.md5(html.encode()).hexdigest()[:8],
          h1.get_text(strip=True) if h1 else None)