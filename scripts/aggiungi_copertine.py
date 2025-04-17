import os
import json
import time
import requests
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def clean_title(title):
    title = re.sub(r'[.,:;]\s.*$', '', title)
    title = re.sub(r'\([^)]*\)', '', title)
    title = re.sub(r'[^\w\s\']', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def extract_cover_from_page(book_url, headers):
    try:
        res = requests.get(book_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        # Tentativo 1: img.cc-img con src
        img = soup.select_one('img.cc-img[src$=".jpg"]')
        if img and img.get("src"):
            src = img["src"]
            if not src.startswith("http"):
                src = "https://www.ibs.it" + src
            return src

        # Tentativo 2: meta og:image
        og = soup.select_one('meta[property="og:image"]')
        if og and og.get("content", "").endswith(".jpg"):
            return og["content"]

        # Tentativo 3: regex su HTML
        img_match = re.search(r'<img[^>]*src="([^"]+/images/[^"]+\.jpg)"', res.text)
        if img_match:
            src = img_match.group(1)
            if not src.startswith("http"):
                src = "https://www.ibs.it" + src
            return src

    except Exception as e:
        print(f"Errore nel parsing HTML pagina: {e}")
    return ""

def get_cover_from_ibs(title, author):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "it-IT,it;q=0.9"
    }

    query = f"{title} {author}".strip()
    search_url = f"https://www.ibs.it/search/?ts=as&query={quote(query)}"

    try:
        res = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select(".search-item-book")

        if not items:
            print(f"Nessun risultato per: {title}")
            return ""

        for item in items[:3]:
            a = item.select_one(".description a")
            link = a["href"] if a and a.get("href") else ""
            if not link:
                continue
            full_url = link if link.startswith("http") else "https://www.ibs.it" + link
            cover = extract_cover_from_page(full_url, headers)
            if cover:
                print(f"✅ Copertina trovata: {cover}")
                return cover
    except Exception as e:
        print(f"Errore richiesta IBS: {e}")
    return ""

def enrich_books_with_ibs_covers():
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

        print(f"[{i}] Cerca: {title}")
        cover = get_cover_from_ibs(title, author)
        if cover:
            book["cover"] = cover
        else:
            print(f"❌ Copertina non trovata per: {title}")

        with open(BOOKS_PATH, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)
        time.sleep(2)

if __name__ == "__main__":
    enrich_books_with_ibs_covers()
