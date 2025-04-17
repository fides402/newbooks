import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import re

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "books.json")

def sanitize_filename(filename):
    return re.sub(r'[\/*?:"<>|]', "", filename)

def download_image(url, filename):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"[✓] Scaricata: {filename}")
            return True
        print(f"[✗] Errore HTTP {response.status_code} per {url}")
        return False
    except Exception as e:
        print(f"[✗] Errore durante il download: {e}")
        return False

def search_google_image_url(query):
    try:
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            print(f"[⚠️] Google response code: {response.status_code}")
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.find_all('img')
        for img in images[1:]:  # salta il logo di Google
            src = img.get('src')
            if src and not src.startswith('data:'):
                return src
        return None
    except Exception as e:
        print(f"[✗] Errore Google Images: {e}")
        return None

def process_book(book):
    title = book.get("title", "").strip()
    author = book.get("author", "").strip()
    query = f"{title} {author}".strip()
    file_name = f"{sanitize_filename(title)}_{sanitize_filename(author)}.jpg"
    output_folder = os.path.join(os.path.dirname(__file__), "..", "book_covers")
    os.makedirs(output_folder, exist_ok=True)
    path = os.path.join(output_folder, file_name)

    print(f"
🔍 Cerco copertina per: {title} — {author if author else 'Autore non disponibile'}")

    if os.path.exists(path):
        print(f"[✓] Copertina già presente: {file_name}")
        return

    # Forza la ricerca, anche se cover/cover_url è vuoto
    img_url = search_google_image_url(query + " copertina libro")
    if img_url:
        print(f"[→] Copertina trovata da Google: {img_url}")
        download_image(img_url, path)
    else:
        print(f"[✗] Nessuna copertina trovata online per: {query}")

def main():
    print(f"[INFO] Carico JSON da: {BOOKS_PATH}")
    if not os.path.exists(BOOKS_PATH):
        print(f"[✗] File non trovato: {BOOKS_PATH}")
        return

    try:
        with open(BOOKS_PATH, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except Exception as e:
        print(f"[✗] Errore nel caricamento JSON: {e}")
        return

    print(f"[INFO] Trovati {len(books)} libri. Avvio scraping...")

    for book in books:
        process_book(book)
        time.sleep(2)  # per non spammare Google

    print("\n✅ Completato.")

if __name__ == "__main__":
    main()
