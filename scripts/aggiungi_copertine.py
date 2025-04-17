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

def get_cover_from_ibs(title, author):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    search_strategies = [
        {"query": f"{title} {author}", "desc": "titolo e autore completi"},
        {"query": title, "desc": "solo titolo"},
        {"query": clean_title(title), "desc": "titolo pulito"},
        {"query": f"{clean_title(title)} {author.split()[0]}", "desc": "titolo pulito e primo nome"}
    ]

    if " " in author:
        search_strategies.append(
            {"query": f"{clean_title(title)} {author.split()[-1]}", "desc": "titolo e cognome"}
        )

    if len(title.split()) > 3:
        short_title = " ".join(title.split()[:3])
        search_strategies.append(
            {"query": f"{short_title} {author}", "desc": "prime parole del titolo"}
        )

    for strategy in search_strategies:
        encoded_query = quote(strategy["query"])
        search_url = f"https://www.ibs.it/search/?ts=as&query={encoded_query}"

        try:
            print(f"🔍 Strategia '{strategy['desc']}': {strategy['query']}")
            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            book_items = soup.select(".search-item-book")

            if not book_items:
                continue

            for book in book_items[:3]:
                title_elem = book.select_one(".description a")
                author_elem = book.select_one(".name a")
                result_title = title_elem.text.strip() if title_elem else ""
                result_author = author_elem.text.strip() if author_elem else ""

                if similar(title, result_title) < 0.6:
                    continue

                if author and result_author and similar(author, result_author) < 0.4:
                    continue

                link = title_elem.get("href")
                link = "https://www.ibs.it" + link if link and not link.startswith("http") else link

                if "/e/" in link:
                    match = re.search(r'/e/(\d{10,13})', link)
                    if match:
                        isbn = match.group(1)
                        url = f"https://www.ibs.it/images/{isbn}_0_536_0_75.jpg"
                        if requests.head(url, headers=headers, timeout=10).status_code == 200:
                            print(f"✅ Copertina da ISBN: {url}")
                            return url

                page = requests.get(link, headers=headers, timeout=15)
                book_soup = BeautifulSoup(page.text, "html.parser")

                # 1. cerca direttamente img.cc-img
                img = book_soup.select_one('img.cc-img[src$=".jpg"]')
                if img:
                    src = img.get("src")
                    if not src.startswith("http"):
                        src = "https://www.ibs.it" + src
                    print(f"✅ Copertina da .cc-img: {src}")
                    return src

                # 2. og:image fallback
                og = book_soup.select_one('meta[property="og:image"]')
                if og and og.get("content", "").endswith(".jpg"):
                    print(f"✅ Copertina da og:image")
                    return og["content"]

        except Exception as e:
            print(f"⚠️ Errore strategia '{strategy['desc']}': {e}")

    print(f"❌ Nessuna copertina trovata per '{title}'")
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
            print(f"[{i}] Skipping: {title}")
            continue

        print(f"[{i}] 🖼️ Ricerca copertina per '{title}'")
        cover = get_cover_from_ibs(title, author)
        if cover:
            book["cover"] = cover
            print(f"✅ Salvata copertina: {cover}")
        else:
            print(f"❌ Nessuna copertina per: {title}")

        with open(BOOKS_PATH, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)

        time.sleep(2)

if __name__ == "__main__":
    enrich_books_with_ibs_covers()
