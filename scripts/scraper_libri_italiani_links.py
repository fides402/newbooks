#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script per lo scraping di libri italiani nelle categorie filosofia, psicologia, società, business e self-help.
Raccoglie titoli, autori e link d'acquisto (senza scaricare copertine).
Versione aggiornata con selettori CSS corretti.
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
        logging.FileHandler("scraper_libri_italiani_links.log"),
        logging.StreamHandler()
    ]
)

# Headers per simulare un browser reale
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.ibs.it/',
    'DNT': '1',
}

# Categorie da scrapare
CATEGORIE = {
    'filosofia': 'https://www.ibs.it/libri/filosofia/ultimi-90-giorni',
    'psicologia': 'https://www.ibs.it/libri/psicologia/ultimi-90-giorni',
    'società': 'https://www.ibs.it/libri/societa-politica-comunicazione/ultimi-90-giorni',
    'business': 'https://www.ibs.it/libri/economia-e-management/ultimi-90-giorni',
    'self-help': 'https://www.ibs.it/libri/self-help-e-valorizzazione-personale/ultimi-90-giorni'
}

def get_page_content(url):
    """Ottiene il contenuto di una pagina web con gestione degli errori e ritardi casuali."""
    try:
        # Aggiungi un ritardo casuale per evitare di sovraccaricare il server
        time.sleep(random.uniform(1, 3))
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante il recupero della pagina {url}: {e}")
        return None

def parse_book_data(html_content, categoria, base_url):
    """Estrae i dati dei libri dalla pagina HTML."""
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    books = []
    
    # Trova tutti i contenitori di libri usando i selettori corretti
    book_containers = soup.select('.cc-product-list-item, div[class*="product-list-item"]')
    
    # Se non troviamo contenitori con il selettore precedente, proviamo un approccio alternativo
    if not book_containers:
        # Cerchiamo i titoli dei libri
        title_links = soup.select('a.cc-title, a[data-tracking-item-click="link"]')
        
        # Per ogni titolo, troviamo il contenitore del libro
        for title_link in title_links:
            container = title_link.parent
            # Risaliamo fino a trovare il contenitore principale
            for _ in range(5):  # Limita la ricerca a 5 livelli
                if container and (container.get('class') and any('product' in c for c in container.get('class', []))):
                    book_containers.append(container)
                    break
                container = container.parent if container else None
    
    # Se ancora non troviamo contenitori, proviamo un altro approccio
    if not book_containers:
        # Cerchiamo tutti i link ai libri
        book_links = soup.select('a[href*="/e/"]')
        
        # Filtriamo solo quelli che sembrano link a libri
        for link in book_links:
            if link.find('img') or (link.text and len(link.text.strip()) > 10):
                container = link.parent
                # Risaliamo fino a trovare un contenitore che potrebbe contenere tutte le info del libro
                for _ in range(5):  # Limita la ricerca a 5 livelli
                    if container and container.text and '€' in container.text:
                        book_containers.append(container)
                        break
                    container = container.parent if container else None
    
    logging.info(f"Trovati {len(book_containers)} possibili contenitori di libri")
    
    # Estrai i dati da ciascun contenitore
    for container in book_containers:
        try:
            # Estrai titolo e link d'acquisto
            title_link = container.select_one('a.cc-title, a[data-tracking-item-click="link"], a[href*="/e/"]')
            
            if not title_link:
                continue
                
            title = title_link.text.strip() if title_link else "Titolo non disponibile"
            
            # Estrai link d'acquisto
            purchase_link = urljoin(base_url, title_link['href']) if title_link and 'href' in title_link.attrs else None
            
            # Estrai autore
            author_elem = container.select_one('a[href*="contributor"], a.cc-author')
            if not author_elem:
                # Cerca altri elementi che potrebbero contenere l'autore
                for a in container.select('a'):
                    if a != title_link and a.text.strip() and not any(x in a.get('href', '') for x in ['/e/', 'offerte']):
                        author_elem = a
                        break
            
            author = author_elem.text.strip() if author_elem else "Autore non disponibile"
            
            # Estrai editore e anno
            publisher_elem = None
            publisher_elems = container.select('a[href*="editore"], a.cc-publisher')
            if publisher_elems:
                publisher_elem = publisher_elems[0]
            
            publisher_text = publisher_elem.text.strip() if publisher_elem else ""
            publisher = publisher_text.replace(',', '').strip()
            
            year_match = re.search(r'(\d{4})', container.text)
            year = year_match.group(1) if year_match else "Anno non disponibile"
            
            # Estrai prezzo
            price_match = re.search(r'(\d+[,.]\d+)\s*€', container.text)
            price = price_match.group(0) if price_match else "Prezzo non disponibile"
            
            books.append({
                'titolo': title,
                'autore': author,
                'editore': publisher,
                'anno': year,
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
    
    base_url = "https://www.ibs.it"
    books = parse_book_data(html_content, categoria, base_url)
    logging.info(f"Trovati {len(books)} libri nella categoria {categoria}")
    
    return books

def main():
    """Funzione principale che coordina lo scraping di tutte le categorie."""
    logging.info("Iniziando lo scraping dei libri italiani...")
    
    all_books = []
    
    for categoria, url in CATEGORIE.items():
        books = scrape_category(categoria, url)
        all_books.extend(books)
        
        # Pausa tra le categorie per evitare di sovraccaricare il server
        time.sleep(random.uniform(2, 5))
    
    # Salva i dati in un file CSV
    if all_books:
        df = pd.DataFrame(all_books)
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libri_italiani_links.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logging.info(f"Dati salvati in {csv_path}")
    else:
        logging.warning("Nessun libro trovato durante lo scraping")
    
    logging.info("Scraping dei libri italiani completato")

if __name__ == "__main__":
    main()
