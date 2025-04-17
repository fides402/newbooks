import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from concurrent.futures import ThreadPoolExecutor
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
            print(f"Downloaded: {filename}")
            return True
        return False
    except Exception as e:
        print(f"Download error: {e}")
        return False

def process_book(book):
    title = book.get('title', '')
    author = book.get('author', '')
    cover_url = book.get('cover') or book.get('cover_url')

    if not cover_url:
        print(f"Nessuna copertina da scaricare per: {title}")
        return

    file_name = f"{sanitize_filename(title)}_{sanitize_filename(author)}.jpg"
    path = os.path.join(os.path.dirname(__file__), "book_covers", file_name)

    if os.path.exists(path):
        print(f"Copertina già esistente per: {title}")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    download_image(cover_url, path)

def main():
    if not os.path.exists(BOOKS_PATH):
        print(f"File non trovato: {BOOKS_PATH}")
        return

    try:
        with open(BOOKS_PATH, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except Exception as e:
        print(f"Errore nel caricamento del file JSON: {e}")
        return

    print(f"Trovati {len(books)} libri. Inizio download copertine...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(process_book, books)

if __name__ == "__main__":
    main()
