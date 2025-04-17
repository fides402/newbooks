import os
import json
import time
import requests
from urllib.parse import quote

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

# Chiave e CX forniti
GOOGLE_API_KEY = "AIzaSyBVtXwnVXilsNqLx6of2HG2jiYwAWs-btg"
CX = "75b2abca03df54610"

def is_valid_image(url):
    try:
        head = requests.head(url, timeout=10)
        if head.status_code == 200:
            content_type = head.headers.get("Content-Type", "")
            content_length = int(head.headers.get("Content-Length", 0))
            return content_type.startswith("image/") and content_length > 25000
    except:
        pass
    return False

def search_cover_with_google(title, author):
    query = f"{title} {author} copertina libro"
    url = f"https://www.googleapis.com/customsearch/v1?q={quote(query)}&key={GOOGLE_API_KEY}&cx={CX}&searchType=image"

    try:
        print(f"🔍 Google Search: {query}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "items" in data:
            for item in data["items"]:
                link = item.get("link")
                if link and is_valid_image(link):
                    print(f"✅ Copertina valida: {link}")
                    return link
    except Exception as e:
        print(f"⚠️ Errore nella Google API: {e}")
    return ""

def enrich_books_with_google_images():
    if not os.path.exists(BOOKS_PATH):
        print("❌ File JSON non trovato:", BOOKS_PATH)
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for i, book in enumerate(books, start=1):
        title = book.get("title", "")
        author = book.get("author", "")
        if not title or book.get("cover"):
            print(f"[{i}] Skip: {title}")
            continue

        print(f"[{i}] Cerca copertina per: {title}")
        cover = search_cover_with_google(title, author)
        if cover:
            book["cover"] = cover
        else:
            print(f"❌ Nessuna copertina trovata per: {title}")

        with open(BOOKS_PATH, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)

        time.sleep(1.5)

if __name__ == "__main__":
    enrich_books_with_google_images()
