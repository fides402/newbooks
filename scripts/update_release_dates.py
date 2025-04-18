import json
import os
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

BOOKS_PATH = os.path.join("data", "books.json")
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEARCH_SOURCES = [
    "https://www.ibs.it/libri/search/?query=",
    "https://www.lafeltrinelli.it/ricerca/"
]

def sanitize_query(text):
    return quote_plus(text.replace("\n", " ").strip())

def extract_date_from_text(text):
    match = re.search(r'(\d{1,2} \w+ \d{4}|\w+ \d{4}|\d{4})', text)
    return match.group(1) if match else None

def search_release_date(title, author):
    query = sanitize_query(f"{title} {author}")
    for base_url in SEARCH_SOURCES:
        try:
            url = base_url + query
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                snippets = soup.find_all(text=re.compile(r'\b\d{4}\b'))
                for snippet in snippets:
                    date = extract_date_from_text(snippet)
                    if date:
                        return date
        except Exception as e:
            print(f"[!] Errore cercando {title}: {e}")
    return None

def main():
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if book.get("releaseDate") and not book["releaseDate"].startswith("202"):
            continue

        title = book.get("title", "")
        author = book.get("author", "")
        print(f"[📅] Cerco data di uscita per: {title}")
        release_date = search_release_date(title, author)

        if release_date:
            print(f"[✅] Trovata: {release_date}")
            book["releaseDate"] = release_date
        else:
            print(f"[❌] Nessuna data trovata")

        time.sleep(1.5)

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print("[🎯] Aggiornamento completato.")

if __name__ == "__main__":
    main()
