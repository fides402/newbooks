import os
import json
import time
import requests
import re
from urllib.parse import quote_plus

# Percorso alla cartella dei dati
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COVERS_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
BOOKS_JSON = os.path.join(COVERS_DIR, 'books.json')

# Crea la directory se non esiste
os.makedirs(COVERS_DIR, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name).replace(' ', '_')

def search_google_images(query):
    try:
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            image_urls = re.findall(r'(https?://[^"\']+\.(?:jpg|png|jpeg))', response.text)
            return image_urls[0] if image_urls else None
    except Exception as e:
        print(f"[❌] Errore ricerca Google Images per '{query}': {e}")
    return None

def download_image(url, path):
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"[⚠️] Errore download immagine {url}: {e}")
    return False

def main():
    with open(BOOKS_JSON, 'r', encoding='utf-8') as f:
        books = json.load(f)

    for book in books:
        title = book.get('title', '')
        author = book.get('author', '')
        if not title or not author:
            continue

        filename = sanitize_filename(f"{title}_{author}") + '.jpg'
        filepath = os.path.join(COVERS_DIR, filename)

        if os.path.exists(filepath):
            print(f"[✅] Copertina esiste: {filename}")
            book['cover'] = f"data/{filename}"
            continue

        print(f"[🔍] Cerco copertina per: {title}")
        query = f"{title} {author} copertina libro"
        url = search_google_images(query)
        if url and download_image(url, filepath):
            print(f"[⬇️] Scaricata copertina: {filename}")
            book['cover'] = f"data/{filename}"
        else:
            print(f"[⛔] Nessuna copertina trovata per: {title}")

        time.sleep(1)  # Rispetta i limiti

    # Salva il file aggiornato
    with open(BOOKS_JSON, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print("[💾] File books.json aggiornato con le copertine.")

if __name__ == '__main__':
    main()
