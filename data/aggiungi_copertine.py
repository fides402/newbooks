import os
import json
import re
import time
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

# Percorso assoluto della directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_PATH = os.path.join(BASE_DIR, "data", "books.json")
COVERS_DIR = os.path.join(BASE_DIR, "data")
PLACEHOLDER = "https://via.placeholder.com/300x450?text=Nessuna+Copertina"

# Assicurati che la directory esista
os.makedirs(COVERS_DIR, exist_ok=True)

def sanitize_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).replace(" ", "_")

def search_google_image(query):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        img_tags = soup.select("img")
        for img in img_tags:
            src = img.get("src") or img.get("data-src")
            if src and "http" in src and not src.startswith("data:"):
                return src
    except Exception as e:
        print(f"[!] Errore ricerca Google per {query}: {e}")
    return None

def download_image(url, path):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"[!] Errore download immagine: {e}")
    return False

def main():
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if book.get("cover"):
            continue

        title = book.get("title", "").strip()
        author = book.get("author", "").strip()
        if not title:
            continue

        print(f"[🔍] Cerco copertina per: {title}")

        filename = sanitize_filename(f"{title}_{author}.jpg")
        local_path = os.path.join(COVERS_DIR, filename)
        relative_path = f"data/{filename}"

        if os.path.exists(local_path):
            print(f"[✔️] Copertina già presente")
            book["cover"] = relative_path
            continue

        img_url = search_google_image(f"{title} {author} copertina libro")
        if img_url and download_image(img_url, local_path):
            print(f"[⬇️] Copertina salvata in: {relative_path}")
            book["cover"] = relative_path
        else:
            print(f"[⛔] Nessuna copertina trovata per: {title}")
            book["cover"] = PLACEHOLDER

        time.sleep(1.5)

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print("[✅] books.json aggiornato con copertine")

if __name__ == "__main__":
    main()
