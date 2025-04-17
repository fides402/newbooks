import os
import json
import time
import requests
from urllib.parse import quote

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

GOOGLE_API_KEY = "AIzaSyBVtXwnVXilsNqLx6of2HG2jiYwAWs-btg"
CX = "YOUR_CX_CODE_HERE"  # Inserisci qui il codice di Custom Search Engine

def search_cover_with_google(title, author):
    query = f"{title} {author} copertina libro"
    url = f"https://www.googleapis.com/customsearch/v1?q={quote(query)}&key={GOOGLE_API_KEY}&cx={CX}&searchType=image"

    try:
        print(f"🔍 Google Image Search: {query}")
        response = requests.get(url, timeout=15)
        data = response.json()

        if "items" in data:
            for item in data["items"]:
                link = item.get("link")
                mime = item.get("mime", "")
                if link and mime.startswith("image/"):
                    print(f"✅ Copertina trovata: {link}")
                    return link
    except Exception as e:
        print(f"⚠️ Errore nella richiesta Google API: {e}")
    return ""

def enrich_books_with_google_images():
    if not os.path.exists(BOOKS_PATH):
        print("❌ File non trovato:", BOOKS_PATH)
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for i, book in enumerate(books, start=1):
        title = book.get("title", "")
        author = book.get("author", "")
        if not title or book.get("cover"):
            print(f"[{i}] Skip: {title}")
            continue

        print(f"[{i}] 🔍 Cerca con Google: {title}")
        cover = search_cover_with_google(title, author)
        if cover:
            book["cover"] = cover
        else:
            print(f"❌ Nessuna copertina trovata con Google")

        with open(BOOKS_PATH, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)

        time.sleep(1)

if __name__ == "__main__":
    enrich_books_with_google_images()
