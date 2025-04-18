import json
import os
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

BOOKS_PATH = os.path.join("data", "books.json")
HEADERS = { "User-Agent": "Mozilla/5.0" }

def search_goodreads_link(title, author):
    query = f"{title} {author} site:goodreads.com/book/show"
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.select("a"):
            href = a.get("href")
            if href and "goodreads.com/book/show" in href:
                match = re.search(r"https://www\.goodreads\.com/book/show/\d+", href)
                if match:
                    return match.group(0)
    except Exception as e:
        print(f"[!] Errore ricerca Goodreads: {e}")
    return None

def extract_date_from_goodreads(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        details = soup.select_one("#details")
        if details:
            text = details.get_text(separator=" ").strip()
            match = re.search(r'Published\s+([A-Za-z]+\s+\d{1,2}[a-z]{0,2},?\s+\d{4})', text)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"[!] Errore parsing Goodreads: {e}")
    return None

def main():
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if book.get("releaseDate") and not book["releaseDate"].startswith("2025"):
            continue

        title = book.get("title", "")
        author = book.get("author", "")
        if not title:
            continue

        print(f"[🔍] Cerco: {title} di {author}")
        gr_link = search_goodreads_link(title, author)
        if not gr_link:
            print("[❌] Goodreads link non trovato")
            continue

        date = extract_date_from_goodreads(gr_link)
        if date:
            print(f"[✅] Data trovata: {date}")
            book["releaseDate"] = date
        else:
            print("[❌] Nessuna data trovata")

        time.sleep(1.5)

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print("[🎯] books.json aggiornato con date da Goodreads")

if __name__ == "__main__":
    main()
