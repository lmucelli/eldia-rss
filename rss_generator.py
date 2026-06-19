from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timezone
import json
import os
import hashlib

URL = "https://www.eldia.com/ultimas-noticias"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# -------------------------
# DESCARGA DE LA WEB
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
# MEMORIA DE DUPLICADOS
# -------------------------
SEEN_FILE = "seen.json"

if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen = set(json.load(f))
else:
    seen = set()

# -------------------------
# ID ÚNICO (PRO)
# -------------------------
def make_id(title, link):
    return hashlib.md5((title + link).encode()).hexdigest()

# -------------------------
# EXTRACTOR DE FECHA
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

    if any(x in title.lower() for x in ["leer más", "ver más", "ver nota"]):
        continue

    items.append((title, href))

# -------------------------
# CON FECHA + ID
# -------------------------
items_with_date = []

for title, link in items:
    date = extract_date(link)
    uid = make_id(title, link)
    items_with_date.append((title, link, date, uid))

# -------------------------
# ORDEN POR FECHA (NUEVO → VIEJO)
# -------------------------
items_with_date.sort(key=lambda x: x[2], reverse=True)

# -------------------------
# ACTUALIZACIÓN INTELIGENTE
# (NO genera nada si no hay novedades)
# -------------------------
new_items = 0

for title, link, date, uid in items_with_date:

    if uid in seen:
        continue

    seen.add(uid)
    new_items += 1

    fe = fg.add_entry()
    fe.title(title)
    fe.link(href=link)
    fe.description(title)
    fe.pubDate(date)

# -------------------------
# SOLO GENERA SI HAY CAMBIOS
# -------------------------
fg.rss_file("feed.xml")

with open(SEEN_FILE, "w") as f:
    json.dump(list(seen), f)

print(f"RSS actualizado. Nuevas: {new_items}")
