import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup

BOOKS_PATH = os.path.join("networks", "data", "books.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def estrai_data_ibs(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, 'html.parser')

        # Cerca la data nella tabella specifiche tecniche
        rows = soup.select(".product-details__tech-specs tr")
        for row in rows:
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td and "Data pubblicazione" in th.text:
                return td.text.strip()

        # Fallback per testo libero con regex
        matches = re.findall(r"(\d{1,2} [a-zA-Z]+ \d{4})", soup.text)
        if matches:
            return matches[0]

    except Exception as e:
        print(f"[!] Errore IBS per {url}: {e}")
    return None


def aggiorna_date():
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        url = book.get("link_acquisto", "")
        if "ibs.it" in url:
            print(f"[🔍] Cerco data per: {book['title']}")
            data = estrai_data_ibs(url)
            if data:
                book["releaseDate"] = data
                print(f"[📅] Data trovata: {data}")
            else:
                print("[⛔] Nessuna data trovata")
            time.sleep(1.5)

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print("\n[✅] books.json aggiornato con date di pubblicazione")


if __name__ == "__main__":
    aggiorna_date()
