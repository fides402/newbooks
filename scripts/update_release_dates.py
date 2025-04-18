import json
import os
import time
import requests
from urllib.parse import quote_plus

BOOKS_PATH = os.path.join("data", "books.json")
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes?q="

def get_google_books_date(title, author):
    query = f"intitle:{title} inauthor:{author}"
    url = GOOGLE_BOOKS_API + quote_plus(query)

    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if "items" in data:
            for item in data["items"]:
                info = item.get("volumeInfo", {})
                date = info.get("publishedDate")
                if date:
                    return date  # es: "2024-01-05" o "2023"
    except Exception as e:
        print(f"[!] Errore per {title}: {e}")
    return None

def main():
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if book.get("releaseDate") and book["releaseDate"] != "2025-04-17":
            continue  # Già presente una data vera

        title = book.get("title", "")
        author = book.get("author", "")
        if not title:
            continue

        print(f"[🔍] Cerco data pubblicazione: {title}")
        date = get_google_books_date(title, author)

        if date:
            print(f"[✅] Trovata: {date}")
            book["releaseDate"] = date
        else:
            print("[❌] Nessuna data trovata")
        time.sleep(1)

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print("[🎯] books.json aggiornato con date da Google Books")

if __name__ == "__main__":
    main()
