import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_ibs_new_books():
    url = "https://www.ibs.it/libri/novita"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    books = []

    for card in soup.select('.ProductList-item'):
        title = card.select_one('.Product-title').get_text(strip=True)
        author = card.select_one('.Product-author').get_text(strip=True) if card.select_one('.Product-author') else "Sconosciuto"
        image = card.select_one('img')['src'] if card.select_one('img') else ""
        books.append({
            "title": title,
            "author": author,
            "releaseDate": datetime.now().strftime('%Y-%m-%d'),
            "category": "Varie",
            "cover": image,
            "origin": "IT"
        })
    return books

def scrape_bookdepository_new_books():
    url = "https://www.bookdepository.com/category/2623/New-Releases"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    books = []

    for item in soup.select('.book-item'):
        title = item.select_one('.title').get_text(strip=True)
        author = item.select_one('.author').get_text(strip=True) if item.select_one('.author') else "Unknown"
        image = item.select_one('img')['data-lazy'] if item.select_one('img') and 'data-lazy' in item.select_one('img').attrs else ""
        books.append({
            "title": title,
            "author": author,
            "releaseDate": datetime.now().strftime('%Y-%m-%d'),
            "category": "Various",
            "cover": image,
            "origin": "US"
        })
    return books

all_books = scrape_ibs_new_books() + scrape_bookdepository_new_books()

with open("data/books.json", "w", encoding="utf-8") as f:
    json.dump(all_books, f, ensure_ascii=False, indent=2)
