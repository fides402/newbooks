import json
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

def get_cover_from_bing(title, author):
    query = f"{title} {author} copertina libro"
    url = f"https://www.bing.com/images/search?q={quote(query)}&form=HDRSC2"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        img_tags = soup.find_all("img")
        for img in img_tags:
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http") and any(ext in src for ext in [".jpg", ".jpeg", ".png"]):
                return src
    except Exception as e:
        print(f"[Bing] Errore per '{title}': {e}")
    return ""

def enrich_books_with_bing_only():
    if not os.path.exists(BOOKS_PATH):
        print("[!] File books.json non trovato")
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if not book.get("cover"):
            cover = get_cover_from_bing(book["title"], book["author"])
            if cover:
                book["cover"] = cover
                print(f"[✓] Copertina trovata per: {book['title']}")
            else:
                print(f"[x] Nessuna copertina trovata per: {book['title']}")
            time.sleep(1.5)

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
        print("[✓] books.json aggiornato con copertine da Bing Images")

if __name__ == "__main__":
    enrich_books_with_bing_only()
