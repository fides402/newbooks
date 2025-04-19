import subprocess
import sys
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))

scripts = [
    "scraper_libri_italiani_links.py",
    "scraper_libri_americani_links.py",
    "organizza_dati_links.py",
    "genera_books_json.py",
    "aggiungi_copertine.py"
]

# 1. Esecuzione pipeline scraping
for script in scripts:
    print(f"▶️ Eseguo: {script}")
    subprocess.run([sys.executable, os.path.join(current_dir, script)], check=True)

# 2. Percorsi dei file JSON
data_dir = os.path.join(current_dir, "..", "data")
current_path = os.path.join(data_dir, "books.json")
previous_path = os.path.join(data_dir, "books_previous.json")

# 3. Carica books.json attuale
with open(current_path, 'r', encoding='utf-8') as f:
    current_books = json.load(f)

# 4. Carica books_previous.json se esiste
try:
    with open(previous_path, 'r', encoding='utf-8') as f:
        previous_books = json.load(f)
        previous_keys = { (b['title'], b.get('author', '')) for b in previous_books }
except FileNotFoundError:
    previous_keys = set()

# 5. Segna i nuovi libri
for book in current_books:
    key = (book['title'], book.get('author', ''))
    book['addedToday'] = key not in previous_keys

# 6. Sovrascrivi entrambi i file
with open(current_path, 'w', encoding='utf-8') as f:
    json.dump(current_books, f, ensure_ascii=False, indent=2)

with open(previous_path, 'w', encoding='utf-8') as f:
    json.dump(current_books, f, ensure_ascii=False, indent=2)

print("✅ books.json aggiornato e differenze registrate con 'addedToday'")
