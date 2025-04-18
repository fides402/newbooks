import os
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

BOOKS_PATH = os.path.join("data", "books.json")
HEADERS = {"User-Agent": "Mozilla/5.0"}

DATE_LABELS = [
    "Originally published",
    "First published",
    "Publication date",
    "Published on",
    "Pubblicato il",
    "Prima pubblicazione"
]

def search_google_info_box(title, author):
    query = quote_plus(f"{title} {author}")
    url = f"https://www.google.com/search?q={query}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Cerca in tutti i div visibili
        for label in DATE_LABELS:
            elements = soup.find_all(text=re.compile(label, re.IGNORECASE))
            for el in elements:
                parent = el.find_parent()
                if parent and parent.find_next_sibling():
                    date_text = parent.find_next_sibling().get_text(strip=True)
                    if re.search(r'\d{4}', date_text):
                        return date_text

        # Fallback: cerca righe con etichetta + data
        full_text = soup.get_text(separator="\n")
        for label in DATE_LABELS:
            match = re.search(fr"{label}.{{0,40}}(\d{{1,2}} \w+ \d{{4}}|\w+ \d{{4}}|\d{{4}})", full_text, re.IGNORECASE)
            if match:
                return match.group(1)

    except Exception as e:
        print(f"[!] Errore per {title}: {e}")

    return None

def main():
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        title = book.get("title", "")
        author = book.get("author", "")
        release_date = book.get("releaseDate", "")

        if release_date and not release_date.startswith("202"):
            continue

        print(f"[🔍] Cerco data per: {title} di {author}")
        date_found = search_google_info_box(title, author)

        if date_found:
            print(f"[📅] Trovata: {date_found}")
            book["releaseDate"] = date_found
        else:
            print(f"[❌] Nessuna data trovata")

        time.sleep(1.5)

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print("[✅] books.json aggiornato con le date trovate da Google.")

if __name__ == "__main__":
    main()
