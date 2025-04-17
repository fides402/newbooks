import json
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import re

# Usa sempre percorsi relativi allo script attuale
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_JSON = os.path.join(BASE_DIR, "books.json")
COVERS_DIR = os.path.join(BASE_DIR, "book_covers")

# Assicurati che esista la cartella delle copertine
os.makedirs(COVERS_DIR, exist_ok=True)

# Funzione per sanitizzare i nomi file
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)

# (Implementa o importa le tue funzioni dettagliate qui)
def get_cover_from_ibs(url):
    # Implementa la tua logica...
    return None

def search_feltrinelli(title, author):
    # Implementa la tua logica...
    return None

def search_mondadori(title, author):
    # Implementa la tua logica...
    return None

def search_google_images(query):
    # Implementa la tua logica...
    return None

def enrich_covers():
    with open(BOOKS_JSON, 'r', encoding='utf-8') as f:
        books = json.load(f)

    for book in books:
        if book.get('cover'):
            continue

        title = book.get('title', '')
        author = book.get('author', '')
        link = book.get('link_acquisto', '')
        cover_url = None

        if 'ibs.it' in link:
            cover_url = get_cover_from_ibs(link)

        if not cover_url:
            cover_url = search_feltrinelli(title, author)
        if not cover_url:
            cover_url = search_mondadori(title, author)
        if not cover_url:
            cover_url = search_google_images(f"{title} {author}")

        if cover_url:
            book['cover'] = cover_url
            print(f"Trovata copertina per '{title}': {cover_url}")

            # Scarica la copertina
            try:
                response = requests.get(cover_url, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    fname = sanitize_filename(f"{title}_{author}") + os.path.splitext(cover_url)[-1]
                    path = os.path.join(COVERS_DIR, fname)
                    with open(path, 'wb') as imgf:
                        imgf.write(response.content)
                    print(f"Immagine scaricata in {path}")
            except Exception as e:
                print(f"Errore download per {title}: {e}")
        else:
            print(f"Nessuna copertina trovata per '{title}'")

        time.sleep(1)  # pausa gentile

    with open(BOOKS_JSON, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print("books.json aggiornato con le copertine.")

if __name__ == '__main__':
    enrich_covers()
