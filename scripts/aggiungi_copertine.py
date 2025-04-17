import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

def get_cover_from_bing(title, author):
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    query = f"{title} {author} copertina libro"
    url = f"https://www.bing.com/images/search?q={quote(query)}&form=HDRSC2"

    try:
        print(f"🔍 Bing search: {query}")
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        images = soup.select("a.iusc")

        for img_tag in images:
            m_json = img_tag.get("m")
            if not m_json:
                continue

            # Estrai URL da JSON in attributo m
            try:
                import json as j
                m_data = j.loads(m_json)
                img_url = m_data.get("murl", "")
                if img_url.lower().endswith(".jpg") and "cover" in img_url.lower():
                    # Verifica dimensione
                    head = requests.head(img_url, timeout=10)
                    if head.status_code == 200 and int(head.headers.get("Content-Length", 0)) > 20_000:
                        print(f"✅ Copertina trovata: {img_url}")
                        return img_url
            except Exception:
                continue

    except Exception as e:
        print(f"⚠️ Errore Bing scraping: {e}")
    return ""

def enrich_books_with_bing_images():
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

        print(f"[{i}] 🔍 Cerca con Bing: {title}")
        cover = get_cover_from_bing(title, author)
        if cover:
            book["cover"] = cover
        else:
            print(f"❌ Nessuna copertina trovata con Bing")

        with open(BOOKS_PATH, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)

        time.sleep(2)

if __name__ == "__main__":
    enrich_books_with_bing_images()
