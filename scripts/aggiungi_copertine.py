import os
import json
import time
import requests
import re
from urllib.parse import quote
from bs4 import BeautifulSoup

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

def get_cover_from_ibs_by_isbn(title, author):
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
            print(f"❌ Nessun risultato per: {title}")
            return ""

        for item in items[:5]:
            a = item.select_one(".description a")
            href = a["href"] if a and a.get("href") else ""
            full_url = href if href.startswith("http") else "https://www.ibs.it" + href

            match = re.search(r"/e/(\d{10,13})", full_url)
            if match:
                isbn = match.group(1)
                cover_url = f"https://www.ibs.it/images/{isbn}_0_0_536_0_75.jpg"
                # Verifica l'esistenza
                if requests.head(cover_url, headers=headers, timeout=10).status_code == 200:
                    print(f"✅ Copertina trovata con ISBN: {cover_url}")
                    return cover_url
                else:
                    print(f"⚠️ Copertina non valida per ISBN: {isbn}")
    except Exception as e:
        print(f"⚠️ Errore IBS: {e}")
    return ""

def enrich_books_with_isbn_cover():
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

        print(f"[{i}] Cerca copertina per: {title}")
        cover = get_cover_from_ibs_by_isbn(title, author)
        if cover:
            book["cover"] = cover
        else:
            print(f"❌ Nessuna copertina trovata per: {title}")

        with open(BOOKS_PATH, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)

        time.sleep(2)

if __name__ == "__main__":
    enrich_books_with_isbn_cover()
