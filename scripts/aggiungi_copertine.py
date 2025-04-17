import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from concurrent.futures import ThreadPoolExecutor
import re

# Percorso corretto per cercare il JSON nella cartella "data/"
BOOKS_PATH = os.path.join(os.path.dirname(__file__), "data", "books.json")

# Qui devi incollare tutte le funzioni dello script originale per:
# - sanitize_filename
# - download_image
# - get_cover_from_ibs
# - get_cover_from_amazon
# - search_google_images
# - search_librerie_coop
# - search_feltrinelli
# - search_mondadori
# - process_book

# E infine il main aggiornato:
def main():
    try:
        with open(BOOKS_PATH, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except Exception as e:
        print(f"Errore nel caricamento del file JSON: {e}")
        return

    print(f"Caricati {len(books)} libri da books.json")
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(process_book, books)
    print("Completato il download delle copertine.")

if __name__ == "__main__":
    main()
