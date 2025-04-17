import os
import json
import time
import requests
import re
from lxml import html

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

# XPath fornito dall'utente per la copertina nel carosello
COVER_XPATH = '//*[@id="slick-slide10"]/div/img'

def extract_cover_with_xpath(page_url, headers):
    try:
        res = requests.get(page_url, headers=headers, timeout=15)
        tree = html.fromstring(res.content)

        # Cerca l'immagine con XPath
        img_elements = tree.xpath(COVER_XPATH)
        for img in img_elements:
            src = img.get("src")
            if src and ".jpg" in src:
                if not src.startswith("http"):
                    src = "https://www.ibs.it" + src
                return src
    except Exception as e:
        print(f"Errore nell'estrazione via XPath: {e}")
    return ""

def enrich_books_using_xpath():
    if not os.path.exists(BOOKS_PATH):
        print("❌ File non trovato:", BOOKS_PATH)
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "it-IT,it;q=0.9"
    }

    for i, book in enumerate(books, start=1):
        title = book.get("title", "")
        ibs_url = book.get("ibs_url", "")
        if not title or not ibs_url or book.get("cover"):
            print(f"[{i}] Skip: {title}")
            continue

        print(f"[{i}] Estrazione copertina da XPath per: {title}")
        cover = extract_cover_with_xpath(ibs_url, headers)
        if cover:
            book["cover"] = cover
            print(f"✅ Copertina trovata: {cover}")
        else:
            print(f"❌ Copertina non trovata via XPath per: {title}")

        with open(BOOKS_PATH, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)
        time.sleep(2)

if __name__ == "__main__":
    enrich_books_using_xpath()
