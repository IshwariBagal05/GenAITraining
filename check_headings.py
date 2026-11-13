from pathlib import Path
from bs4 import BeautifulSoup
from app.fetch import SOURCES

for slug, url in SOURCES.items():
    print(f"{slug}\n   url: {url}")

print()
for p in sorted(Path("data/raw").glob("*.html")):
    s = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
    print(p.name)
    print("   title:", s.title.get_text(strip=True) if s.title else None)
    print("   h2s  :", [" ".join(h.get_text().split())[:40] for h in s.find_all("h2")])