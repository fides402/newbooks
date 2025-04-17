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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def sanitize(text):
    return re.sub(r'[\\/*?:"<>|]', "", text)

def search_cover_url(title, author):
    query = f"{title} {author} copertina libro"
    url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"❌ Errore HTTP da Google: {resp.status_code}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        scripts = soup.find_all("script")

        for script in scripts:
            if 'AF_initDataCallback' in script.text:
                matches = re.findall(r'https?://[^"]+\.(jpg|jpeg|png)', script.text)
                filtered = [url for url in matches if not url.startswith('data:')]
                if filtered:
                    return filtered[0]  # Prima immagine valida

    except Exception as e:
        print(f"❌ Errore durante la ricerca per {title}: {e}")
    return None

def download_cover(url, filename):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            with open(filename, "wb") as f:
                f.write(r.content)
            print(f"✅ Scaricata: {filename}")
        else:
            print(f"❌ Impossibile scaricare {url}: {r.status_code}")
    except Exception as e:
        print(f"❌ Errore nel download da {url}: {e}")

def process_book(book):
    title = book.get("title", "").strip()
    author = book.get("author", "").strip()
    if not title:
        return

    print(f"\n🔍 {title} - {author or 'Autore sconosciuto'}")
    filename = os.path.join(COVERS_DIR, f"{sanitize(title)}_{sanitize(author)}.jpg")
    if os.path.exists(filename):
        print("↪️  Già presente")
        return

    img_url = search_cover_url(title, author)
    if img_url:
        print(f"🌐 Copertina trovata: {img_url}")
        download_cover(img_url, filename)
    else:
        print(f"🕳 Nessuna copertina trovata")

def main():
    if not os.path.exists(BOOKS_PATH):
        print("❌ File books.json non trovato.")
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    print(f"\n📚 {len(books)} libri da elaborare")
    with ThreadPoolExecutor(max_workers=3) as pool:
        pool.map(process_book, books)

if __name__ == "__main__":
    main()
