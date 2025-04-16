import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def scrape_ibs_new_books():
    url = "https://www.ibs.it/libri/novita"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    books = []
    today = datetime.today()

    for card in soup.select('.ProductList-item'):
        title = card.select_one('.Product-title')
        author = card.select_one('.Product-author')
        image = card.select_one('img')
        if not title or not image:
            continue
        books.append({
            "title": title.get_text(strip=True),
            "author": author.get_text(strip=True) if author else "Sconosciuto",
            "releaseDate": today.strftime('%Y-%m-%d'),
            "category": "Varie",
            "cover": image.get("data-src") or image.get("src") or "",
            "origin": "IT"
        })
    return books

def scrape_bookdepository_new_books():
    url = "https://www.bookdepository.com/category/2623/New-Releases"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    books = []
    today = datetime.today()

    for item in soup.select('.book-item'):
        title = item.select_one('.title')
        author = item.select_one('.author')
        image = item.select_one('img')
        if not title or not image:
            continue
        books.append({
            "title": title.get_text(strip=True),
            "author": author.get_text(strip=True) if author else "Unknown",
            "releaseDate": today.strftime('%Y-%m-%d'),
            "category": "Various",
            "cover": image.get("data-lazy") or image.get("src") or "",
            "origin": "US"
        })
    return books

def filter_recent_books(books, days=30):
    today = datetime.today()
    cutoff = today - timedelta(days=days)
    return [book for book in books if datetime.strptime(book["releaseDate"], "%Y-%m-%d") >= cutoff]

all_books = scrape_ibs_new_books() + scrape_bookdepository_new_books()
recent_books = filter_recent_books(all_books)

with open("data/books.json", "w", encoding="utf-8") as f:
    json.dump(recent_books, f, ensure_ascii=False, indent=2)
