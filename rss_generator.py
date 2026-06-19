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

# -------------------------
# DESCARGA HTML
# -------------------------
response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# -------------------------
# FEED RSS
# -------------------------
fg = FeedGenerator()
fg.title("El Día - Últimas Noticias")
fg.link(href=URL)
fg.description("RSS generado automáticamente desde El Día")
fg.language("es")

# -------------------------
# MEMORIA (seen.json)
# -------------------------
SEEN_FILE = "seen.json"

def normalize_link(link):
    return link.split("?")[0].rstrip("/")

if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen = set(normalize_link(x) for x in json.load(f))
else:
    seen = set()

# -------------------------
# FECHA (opcional)
# -------------------------
def extract_date(article_url):
    try:
        r = requests.get(article_url, timeout=10, headers=headers)
        soup2 = BeautifulSoup(r.text, "html.parser")

        meta = soup2.find("meta", {"property": "article:published_time"})
        if meta and meta.get("content"):
            return datetime.fromisoformat(meta["content"].replace("Z", "+00:00"))

        time_tag = soup2.find("time")
        if time_tag and time_tag.get("datetime"):
            return datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))

    except:
        pass

    return datetime.now(timezone.utc)

# -------------------------
# SCRAPING
# -------------------------
items = []

for a in soup.find_all("a", href=True):
    href = a["href"]
    title = a.get_text(strip=True)

    if not title:
        continue

    if len(title) < 25:
        continue

    if href.startswith("/"):
        href = "https://www.eldia.com" + href

    if "eldia.com" not in href:
        continue

    # filtro anti-menú / basura
    if any(x in title.lower() for x in ["leer más", "ver más", "ver nota"]):
        continue

    # filtro nuevo (artículos reales)
    if "/202" not in href:
        continue

    items.append((title, href))

# -------------------------
# AGREGAR FECHAS
# -------------------------
items_with_date = []

for title, link in items:
    date = extract_date(link)
    items_with_date.append((title, link, date))

# ordenar por fecha
items_with_date.sort(key=lambda x: x[2], reverse=True)

# -------------------------
# GENERAR RSS + DEDUP
# -------------------------
new_items = 0

for title, link, date in items_with_date:

    clean_link = normalize_link(link)

    if clean_link in seen:
        continue

    seen.add(clean_link)
    new_items += 1

    fe = fg.add_entry()
    fe.title(title)
    fe.link(href=link)
    fe.description(title)
    fe.pubDate(date)

# -------------------------
# GUARDAR SALIDA
# -------------------------
fg.rss_file("feed.xml")

with open(SEEN_FILE, "w") as f:
    json.dump(list(seen), f)

print(f"RSS actualizado. Nuevas: {new_items}")
