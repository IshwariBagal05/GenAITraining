from bs4 import BeautifulSoup

with open("data/raw/free-look-period.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

seen = set()
for a in soup.find_all("a", href=True):
    href = a["href"]
    text = " ".join(a.get_text().split())
    if text and href not in seen:
        seen.add(href)
        print(f"{text:45} -> {href}")