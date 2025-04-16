import json
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

API_KEY = "AIzaSyBVtXwnVXilsNqLx6of2HG2jiYwAWs-btg"
BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

def get_cover_from_ibs(link):
    try:
        if "ibs.it" not in link:
            return None
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(link, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img_tag = soup.find("img", {"class": "js-cover"})
            if img_tag and img_tag.get("src"):
                return img_tag["src"]
    except Exception as e:
        print(f"[IBS] Errore per {link}: {e}")
    return None

def get_cover_from_google(title, author):
    query = quote(f"{title} {author}")
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=3&key={API_KEY}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        items = res.json().get("items", [])
        for item in items:
            volume_info = item.get("volumeInfo", {})
            result_title = volume_info.get("title", "").lower()
            result_authors = [a.lower() for a in volume_info.get("authors", [])]
            image_links = volume_info.get("imageLinks", {})
            if title.lower() in result_title and any(author.lower() in a for a in result_authors):
                return image_links.get("thumbnail") or image_links.get("smallThumbnail")
    except Exception as e:
        print(f"[Google] Errore per {title}: {e}")
    return None

def enrich_books_with_covers():
    if not os.path.exists(BOOKS_PATH):
        print("[!] File books.json non trovato")
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if not book.get("cover"):
            cover = None
            if "ibs.it" in book.get("link_acquisto", ""):
                cover = get_cover_from_ibs(book["link_acquisto"])
                time.sleep(1.2)  # rispetto per il sito
            if not cover:
                cover = get_cover_from_google(book["title"], book["author"])
            if cover:
                book["cover"] = cover
            else:
                print(f"[x] Nessuna cover trovata per: {book['title']} - {book['author']}")

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
        print("[✓] books.json aggiornato con copertine da IBS + Google")

if __name__ == "__main__":
    enrich_books_with_covers()
