import os
import json
import re
import time
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

# Percorso assoluto del file books.json
BOOKS_PATH = os.path.join("networks", "data", "books.json")

# User-Agent per evitare blocchi da Google
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def sanitize_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text)

def search_google_image(query):
    """Cerca una copertina su Google Images e restituisce il primo link utile."""
    search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        img_tags = soup.select("img")
        for img in img_tags:
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http") and not src.startswith("data:"):
                return src
    except Exception as e:
        print(f"[!] Errore ricerca immagine per '{query}': {e}")
    return None

def main():
    if not os.path.exists(BOOKS_PATH):
        print(f"[ERRORE] Impossibile trovare {BOOKS_PATH}")
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if book.get("cover"):
            continue

        title = book.get("title", "")
        author = book.get("author", "")
        if not title:
            continue

        query = f"{title} {author} copertina libro"
        print(f"[🔍] Cerco copertina per: {title}")

        image_url = search_google_image(query)
        if image_url:
            book["cover"] = image_url
            print(f"[✅] Copertina trovata: {image_url}")
        else:
            book["cover"] = "https://via.placeholder.com/300x450?text=Nessuna+Copertina"
            print(f"[⛔] Nessuna copertina trovata per: {title}")

        time.sleep(1.5)  # Rispetta i limiti di Google

    # Salva direttamente nello stesso file
    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print("[✅] books.json aggiornato con i link delle copertine.")

if __name__ == "__main__":
    main()
