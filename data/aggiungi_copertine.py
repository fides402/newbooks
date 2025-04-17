import os
import json
import re
import time
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

BOOKS_PATH = os.path.join("data", "books.json")
HEADERS = { "User-Agent": "Mozilla/5.0" }

def sanitize_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).replace(" ", "_")

def search_google_image(query):
    url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        img_tags = soup.select("img")
        for img in img_tags:
            src = img.get("src") or img.get("data-src")
            if src and "http" in src and not src.startswith("data:"):
                return src
    except Exception as e:
        print(f"[!] Errore ricerca Google per {query}: {e}")
    return None

def main():
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if book.get("cover"):
            continue

        title = book.get("title", "")
        author = book.get("author", "")
        if not title:
            continue

        query = f"{title} {author} copertina libro"
        print(f"[🔍] Cerco copertina per: {title}")

        img_url = search_google_image(query)
        if img_url:
            book["cover"] = img_url
            print(f"[✅] Trovata: {img_url}")
        else:
            book["cover"] = "https://via.placeholder.com/300x450?text=Nessuna+Copertina"
            print(f"[⛔] Nessuna copertina trovata")

        time.sleep(1.5)

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print("[✅] books.json aggiornato con link delle copertine")

if __name__ == "__main__":
    main()
