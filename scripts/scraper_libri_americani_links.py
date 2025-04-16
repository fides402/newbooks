#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script per lo scraping di libri americani nelle categorie filosofia, psicologia, società, business e self-help.
Raccoglie titoli, autori e link d'acquisto (senza scaricare copertine).
"""

import os
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from datetime import datetime, timedelta
import pandas as pd
from urllib.parse import urljoin
import logging

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper_libri_americani_links.log"),
        logging.StreamHandler()
    ]
)

# Headers per simulare un browser reale
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.amazon.com/',
    'DNT': '1',
}

# Categorie da scrapare
CATEGORIE = {
    'filosofia': 'https://www.amazon.com/gp/new-releases/books/11019',
    'psicologia': 'https://www.amazon.com/gp/new-releases/books/11119',
    'società': 'https://www.amazon.com/gp/new-releases/books/3377866011',  # Social Sciences
    'business': 'https://www.amazon.com/gp/new-releases/books/3',
    'self-help': 'https://www.amazon.com/gp/new-releases/books/4736'
}

def get_page_content(url):
    """Ottiene il contenuto di una pagina web con gestione degli errori e ritardi casuali."""
    try:
        # Aggiungi un ritardo casuale per evitare di sovraccaricare il server
        time.sleep(random.uniform(2, 5))
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante il recupero della pagina {url}: {e}")
        return None

def parse_book_data(html_content, categoria, base_url):
    """Estrae i dati dei libri dalla pagina HTML di Amazon."""
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    books = []
    
    # Trova tutti i libri nella pagina
    # Amazon ha una struttura diversa, quindi adattiamo l'approccio
    
    # Cerchiamo i link ai libri
    book_links = soup.select('a[href*="/dp/"]')
    book_containers = []
    
    # Filtriamo solo quelli che sono link a libri
    for link in book_links:
        # Verifichiamo se è un link a un libro
        if link.find('img') and not any(nav in link.get('href', '') for nav in ['javascript', '#']):
            # Troviamo il contenitore del libro risalendo nella struttura DOM
            container = link.parent
            if container:
                # Risaliamo fino a trovare un contenitore che potrebbe contenere tutte le info del libro
                for _ in range(5):  # Limita la ricerca a 5 livelli
                    if container.find(text=re.compile(r'\$\d+\.\d+')) or container.find(text=re.compile(r'out of 5 stars')):
                        book_containers.append((container, link))
                        break
                    container = container.parent
                    if not container:
                        break
    
    # Rimuovi duplicati (stesso link)
    unique_links = {}
    for container, link in book_containers:
        if link['href'] not in unique_links:
            unique_links[link['href']] = (container, link)
    
    book_containers = list(unique_links.values())
    
    logging.info(f"Trovati {len(book_containers)} possibili contenitori di libri")
    
    # Estrai i dati da ciascun contenitore
    for container, link in book_containers:
        try:
            # Estrai titolo
            title_elem = link.find('img')
            title = title_elem.get('alt', '').strip() if title_elem else None
            
            if not title:
                title_elem = container.select_one('div[class*="title"], span[class*="title"]')
                title = title_elem.text.strip() if title_elem else "Titolo non disponibile"
            
            # Estrai link d'acquisto
            purchase_link = urljoin(base_url, link['href']) if link and 'href' in link.attrs else None
            
            # Estrai autore
            author_elem = container.select_one('a[href*="field-author"], span[class*="author"], div[class*="author"]')
            author = author_elem.text.strip() if author_elem else "Autore non disponibile"
            
            # Estrai prezzo
            price_match = re.search(r'\$(\d+\.\d+)', container.text)
            price = f"${price_match.group(1)}" if price_match else "Prezzo non disponibile"
            
            books.append({
                'titolo': title,
                'autore': author,
                'prezzo': price,
                'categoria': categoria,
                'link_acquisto': purchase_link
            })
            
        except Exception as e:
            logging.error(f"Errore durante l'estrazione dei dati di un libro: {e}")
    
    return books

def scrape_category(categoria, url):
    """Scrapa tutti i libri di una categoria."""
    logging.info(f"Iniziando lo scraping della categoria: {categoria}")
    
    html_content = get_page_content(url)
    if not html_content:
        logging.error(f"Impossibile ottenere il contenuto della pagina per la categoria {categoria}")
        return []
    
    base_url = "https://www.amazon.com"
    books = parse_book_data(html_content, categoria, base_url)
    logging.info(f"Trovati {len(books)} libri nella categoria {categoria}")
    
    return books

def main():
    """Funzione principale che coordina lo scraping di tutte le categorie."""
    logging.info("Iniziando lo scraping dei libri americani...")
    
    all_books = []
    
    for categoria, url in CATEGORIE.items():
        books = scrape_category(categoria, url)
        all_books.extend(books)
        
        # Pausa tra le categorie per evitare di sovraccaricare il server
        time.sleep(random.uniform(3, 7))
    
    # Salva i dati in un file CSV
    if all_books:
        df = pd.DataFrame(all_books)
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libri_americani_links.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logging.info(f"Dati salvati in {csv_path}")
    else:
        logging.warning("Nessun libro trovato durante lo scraping")
    
    logging.info("Scraping dei libri americani completato")

if __name__ == "__main__":
    main()
