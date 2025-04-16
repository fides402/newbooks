import json
import os
import requests
from urllib.parse import quote

API_KEY = "AIzaSyBVtXwnVXilsNqLx6of2HG2jiYwAWs-btg"
BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

def get_cover_from_google(title, author):
    query = f"{title} {author}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={quote(query)}&maxResults=1&key={API_KEY}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        items = res.json().get("items", [])
        if items:
            volume_info = items[0].get("volumeInfo", {})
            image_links = volume_info.get("imageLinks", {})
            return image_links.get("thumbnail") or image_links.get("smallThumbnail")
    except Exception as e:
        print(f"[!] Errore per {title}: {e}")
    return ""

def enrich_books_with_covers():
    if not os.path.exists(BOOKS_PATH):
        print("[!] File books.json non trovato")
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if not book.get("cover"):
            cover = get_cover_from_google(book["title"], book["author"])
            book["cover"] = cover or ""

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
        print("[✓] books.json aggiornato con copertine reali")

if __name__ == "__main__":
    enrich_books_with_covers()
