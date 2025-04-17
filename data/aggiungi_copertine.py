import os
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")
COVERS_DIR = os.path.join(os.path.dirname(__file__), "../docs/book_covers")
os.makedirs(COVERS_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def sanitize(text):
    return re.sub(r'[\\/*?:"<>|]', "", text)

def search_cover_url(title, author):
    query = f"{title} {author} copertina libro"
    url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        images = soup.select("img")
        for img in images:
            src = img.get("src")
            if src and src.startswith("http"):
                return src
    except Exception as e:
        print(f"[!] Errore durante la ricerca per {title}: {e}")
    return None

def download_cover(url, filename):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            with open(filename, "wb") as f:
                f.write(r.content)
            print(f"✅ Scaricata: {filename}")
        else:
            print(f"❌ Errore nel download {url}: {r.status_code}")
    except Exception as e:
        print(f"❌ Download fallito per {url}: {e}")

def process_book(book):
    title = book.get("title", "").strip()
    author = book.get("author", "").strip()
    if not title:
        return

    print(f"[🔍] Titolo: {title}")
    filename = os.path.join(COVERS_DIR, f"{sanitize(title)}_{sanitize(author)}.jpg")
    if os.path.exists(filename):
        print("↪️  Copertina già presente")
        return

    cover_url = search_cover_url(title, author)
    if cover_url:
        download_cover(cover_url, filename)
    else:
        print(f"[⏭] Nessuna copertina trovata per: {title}")

def main():
    if not os.path.exists(BOOKS_PATH):
        print("❌ File books.json non trovato.")
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    print(f"📚 Trovati {len(books)} libri. Inizio scraping copertine...")
    with ThreadPoolExecutor(max_workers=3) as pool:
        pool.map(process_book, books)

if __name__ == "__main__":
    main()
