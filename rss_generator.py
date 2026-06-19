from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup
import requests
from datetime import datetime

URL = "https://www.eldia.com/ultimas-noticias"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

fg = FeedGenerator()
fg.title("El Día - Últimas Noticias")
fg.link(href=URL)
fg.description("RSS generado automáticamente desde El Día")
fg.language("es")

items = []

for a in soup.find_all("a", href=True):
    href = a["href"]
    title = a.get_text(strip=True)

    if not title:
        continue

    if len(title) < 20:
        continue

    if href.startswith("/"):
        href = "https://www.eldia.com" + href

    if "eldia.com" not in href:
        continue

    items.append((title, href))

seen = set()

for title, link in items:
    if link in seen:
        continue

    seen.add(link)

    fe = fg.add_entry()
    fe.title(title)
    fe.link(href=link)
    fe.description(title)
    fe.pubDate(datetime.utcnow())

fg.rss_file("feed.xml")
print("RSS generado correctamente")
