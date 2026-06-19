from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timezone
import json
import os

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

SEEN_FILE = "seen.json"

if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen_links = set(json.load(f))
else:
    seen_links = set()

items = []

items = []

for a in soup.find_all("a", href=True):
    href = a["href"]
    title = a.get_text(strip=True)

    # limpieza básica
    if not title:
        continue

    # filtra basura tipo menú o botones
    if len(title) < 25:
        continue

    if href.startswith("/"):
        href = "https://www.eldia.com" + href

    if "eldia.com" not in href:
        continue

    # elimina cosas típicas que no son noticias reales
    if any(x in title.lower() for x in ["leer más", "ver más", "ver nota"]):
        continue

    items.append((title, href))

for title, link in items:
    if link in seen_links:
        continue

    seen_links.add(link)

    fe = fg.add_entry()
    fe.title(title)
    fe.link(href=link)
    fe.description(title)
    fe.pubDate(datetime.now(timezone.utc))

fg.rss_file("feed.xml")

with open(SEEN_FILE, "w") as f:
    json.dump(list(seen_links), f)
    
print("RSS generado correctamente")
