import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re

# Percorso file JSON e cartella destinazione immagini
BOOKS_JSON = "networks/data/books.json"
COVERS_DIR = "networks/data"

# Crea la cartella se non esiste
os.makedirs(COVERS_DIR, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def search_google_images(query):
    try:
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
        response = requests.get(search_url, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for img in soup.select('img'):
                src = img.get('src') or img.get('data-src')
                if src and src.startswith('http') and not src.startswith('data:'):
                    return src
    except Exception as e:
        print(f"[⚠️] Errore Google Images: {e}")
    return None

def download_image(url, path):
    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"[⚠️] Errore download immagine: {e}")
    return False

def enrich_books():
    if not os.path.exists(BOOKS_JSON):
        print(f"[❌] File non trovato: {BOOKS_JSON}")
        return

    with open(BOOKS_JSON, 'r', encoding='utf-8') as f:
        books = json.load(f)

    for book in books:
        title = book.get('title', '')
        author = book.get('author', '')
        filename = sanitize_filename(f"{title}_{author}") + ".jpg"
        image_path = os.path.join(COVERS_DIR, filename)

        if book.get('cover') and os.path.exists(image_path):
            continue

        print(f"[🔍] {title} - {author}")
        query = f"{title} {author} copertina libro"
        cover_url = search_google_images(query)

        if cover_url:
            if download_image(cover_url, image_path):
                book['cover'] = f"data/{filename}"
                print(f"[✅] Salvata in: {image_path}")
            else:
                print(f"[⛔️] Download fallito per {title}")
        else:
            print(f"[⏭] Nessuna copertina trovata per: {title}")

        time.sleep(1.5)

    with open(BOOKS_JSON, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print("✅ books.json aggiornato.")

if __name__ == "__main__":
    enrich_books()
