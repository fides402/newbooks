import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

BOOKS_PATH = os.path.join("data", "books.json")
HEADERS = {"User-Agent": "Mozilla/5.0"}

def search_ibs(title, author):
    query = quote_plus(f"{title} {author}")
    url = f"https://www.ibs.it/search/?ts=as&query={query}&filterGenre=libri"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        product_links = soup.select("div.product-info a[href*='/libro/']")
        if not product_links:
            return None

        first_link = product_links[0]["href"]
        full_url = "https://www.ibs.it" + first_link
        return extract_date_from_ibs(full_url)
    except:
        return None

def extract_date_from_ibs(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None
        soup = BeautifulSoup(res.text, "html.parser")
        info = soup.find("ul", class_="product-main-info-list")
        if info:
            text = info.get_text(separator=" ")
            match = re.search(r'(\d{1,2} \w+ \d{4}|\w+ \d{4}|\d{4})', text)
            return match.group(1) if match else None
    except:
        return None

def main():
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if book.get("releaseDate") and re.match(r"^\d{4}", book["releaseDate"]):
            continue

        title = book.get("title", "")
        author = book.get("author", "")
        print(f"🔎 Cerco data per: {title}")

        date = search_ibs(title, author)

        if date:
            print(f"✅ Trovata: {date}")
            book["releaseDate"] = date
        else:
            print("❌ Nessuna data trovata")

        time.sleep(1.2)

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print("🎯 books.json aggiornato con le date di uscita.")

if __name__ == "__main__":
    main()
