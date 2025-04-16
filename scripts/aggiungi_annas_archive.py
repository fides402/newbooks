import json
import os
from urllib.parse import quote

BOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/books.json")

def build_annas_link(title, author):
    query = quote(f"{title} {author}")
    return f"https://annas-archive.org/search?q={query}"

def enrich_books_with_annas_archive():
    if not os.path.exists(BOOKS_PATH):
        print("[!] File books.json non trovato")
        return

    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        annas_url = build_annas_link(book["title"], book["author"])
        book["annas_link"] = annas_url  # Aggiungiamo il link sempre, anche se il risultato può essere vuoto

    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
        print("[✓] books.json aggiornato con link Anna's Archive")

if __name__ == "__main__":
    enrich_books_with_annas_archive()
