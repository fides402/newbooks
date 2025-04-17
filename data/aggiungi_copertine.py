import json
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import re

# Path to your books.json
BOOKS_JSON = "books.json"
# Optionally, folder to download covers
COVERS_DIR = "book_covers"

# Ensure covers directory exists
os.makedirs(COVERS_DIR, exist_ok=True)

# Utility to sanitize filenames
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)

# --- Functions to scrape cover URLs (abbreviated) ---
# You can keep your existing get_cover_from_ibs, search_feltrinelli, etc.
# For brevity, here is a simplified placeholder; replace with your detailed implementations.

def get_cover_from_ibs(url):
    # ... your existing scraping logic ...
    return None

def search_feltrinelli(title, author):
    # ... your existing retailer search logic ...
    return None

def search_mondadori(title, author):
    # ... your existing retailer search logic ...
    return None

def search_google_images(query):
    # ... your existing fallback logic ...
    return None

# Main process

def enrich_covers():
    # Load JSON
    with open(BOOKS_JSON, 'r', encoding='utf-8') as f:
        books = json.load(f)

    for book in books:
        # Skip if already set
        if book.get('cover'):
            continue

        title = book.get('title', '')
        author = book.get('author', '')
        link = book.get('link_acquisto', '')
        cover_url = None

        # Try purchase link
        if 'ibs.it' in link:
            cover_url = get_cover_from_ibs(link)
        # add more conditions if needed

        # Try other sources
        if not cover_url:
            cover_url = search_feltrinelli(title, author)
        if not cover_url:
            cover_url = search_mondadori(title, author)
        if not cover_url:
            cover_url = search_google_images(f"{title} {author}")

        # Update JSON
        if cover_url:
            book['cover'] = cover_url
            print(f"Found cover for '{title}' -> {cover_url}")

            # Optionally, download image
            try:
                resp = requests.get(cover_url, headers={ 'User-Agent': 'Mozilla/5.0' })
                if resp.status_code == 200:
                    fname = sanitize_filename(f"{title}_{author}") + os.path.splitext(cover_url)[-1]
                    path = os.path.join(COVERS_DIR, fname)
                    with open(path, 'wb') as imgf:
                        imgf.write(resp.content)
                    print(f"Downloaded image to {path}")
            except Exception as e:
                print(f"Download failed for {title}: {e}")

        else:
            print(f"No cover found for '{title}'")

        time.sleep(1)  # be polite

    # Write back JSON
    with open(BOOKS_JSON, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print("books.json updated with cover URLs.")

if __name__ == '__main__':
    enrich_covers()
