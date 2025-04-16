import json
import requests
from datetime import datetime

# Simulazione di chiamata API (puoi usare Google Books o Open Library)
def get_books():
    query = "self-help+psychology+business+philosophy"
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&langRestrict=en&orderBy=newest&maxResults=10"
    r = requests.get(url)
    items = r.json().get("items", [])
    books = []

    for item in items:
        info = item["volumeInfo"]
        books.append({
            "title": info.get("title", "N/A"),
            "author": ", ".join(info.get("authors", [])),
            "releaseDate": info.get("publishedDate", "N/A"),
            "category": ", ".join(info.get("categories", [])) if "categories" in info else "N/A"
        })
    return books

books = get_books()

with open("data/books.json", "w", encoding="utf-8") as f:
    json.dump(books, f, ensure_ascii=False, indent=2)
