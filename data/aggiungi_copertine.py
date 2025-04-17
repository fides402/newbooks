import json
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import re
from concurrent.futures import ThreadPoolExecutor

# Directory per le copertine dei libri
COVERS_DIR = os.path.join('data', 'book_covers')

# Crea la directory se non esiste
if not os.path.exists(COVERS_DIR):
    os.makedirs(COVERS_DIR)

def sanitize_filename(filename):
    """Rimuove caratteri non validi dai nomi file"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_image(url, filename):
    """Scarica un'immagine dall'URL e la salva nel file specificato"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Scaricato: {filename}")
            return True
        else:
            print(f"Impossibile scaricare {url}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Errore nel download di {url}: {e}")
        return False

def get_cover_from_ibs(url):
    """Estrae l'URL dell'immagine di copertina dalla pagina del prodotto su IBS.it"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Prova diversi selettori possibili per IBS.it
            selectors = [
                '.product-gallery__featured-image img',
                '.product-gallery__item img',
                '.carousel-container img',
                'img.photo',
                '.img-wrapper img',
                'img[data-src*="cover"]',
                'img[src*="cover"]',
                '.cover-image img',
                'img[alt*="copertina"]'
            ]
            
            for selector in selectors:
                img_container = soup.select_one(selector)
                if img_container:
                    img_url = img_container.get('src') or img_container.get('data-src')
                    if img_url:
                        if not img_url.startswith('http'):
                            img_url = urljoin('https://www.ibs.it/', img_url)
                        img_url = re.sub(r'_\d+x\d+', '_1200x1200', img_url)
                        return img_url
            
            # Se non trova con i selettori, cerca qualsiasi immagine grande sulla pagina
            all_images = soup.select('img')
            for img in all_images:
                src = img.get('src') or img.get('data-src')
                if src and ('cover' in src.lower() or 'copertina' in src.lower() or 'product' in src.lower()):
                    if not src.startswith('http'):
                        src = urljoin('https://www.ibs.it/', src)
                    return src
        
        return None
    except Exception as e:
        print(f"Errore durante lo scraping di IBS {url}: {e}")
        return None

def get_cover_from_amazon(url):
    """Estrae l'URL dell'immagine di copertina dalla pagina del prodotto su Amazon"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Prova diversi selettori possibili per Amazon
            selectors = [
                '#imgBlkFront',
                '#landingImage',
                '#main-image',
                '#ebooksImgBlkFront',
                'img.a-dynamic-image',
                'img[data-a-dynamic-image]',
                'img[data-old-hires]',
                'img.frontImage'
            ]
            
            for selector in selectors:
                img_container = soup.select_one(selector)
                if img_container:
                    if img_container.get('data-a-dynamic-image'):
                        try:
                            img_urls = json.loads(img_container.get('data-a-dynamic-image'))
                            if img_urls:
                                largest_img_url = sorted(img_urls.keys(), key=lambda x: img_urls[x][0] * img_urls[x][1], reverse=True)[0]
                                return largest_img_url
                        except:
                            pass
                    
                    if img_container.get('data-old-hires'):
                        return img_container.get('data-old-hires')
                    
                    if img_container.get('src'):
                        img_url = img_container.get('src')
                        img_url = img_url.replace('._SL500_', '._SL1500_').replace('._SY300_', '._SY1500_')
                        return img_url
        
        return None
    except Exception as e:
        print(f"Errore durante lo scraping di Amazon {url}: {e}")
        return None

def search_google_images(query):
    """Cerca la copertina del libro su Google Images come fallback"""
    try:
        search_terms = [
            f"{query} copertina libro",
            f"{query} book cover",
            f"{query} libro IBS",
            f"{query} libro Feltrinelli",
            f"{query} libro Mondadori"
        ]
        
        for search_term in search_terms:
            search_url = f"https://www.google.com/search?q={quote_plus(search_term)}&tbm=isch"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Cerca nei dati JSON
                scripts = soup.select('script')
                for script in scripts:
                    if script.string and 'AF_initDataCallback' in script.string:
                        raw_data = script.string
                        img_urls = re.findall(r'https?://\S+?\.(?:jpg|jpeg|png|webp)', raw_data)
                        if img_urls:
                            for url in img_urls:
                                if 'books' in url.lower() or 'cover' in url.lower() or 'ibs' in url.lower() or 'feltrinelli' in url.lower() or 'mondadori' in url.lower():
                                    return url
                
                # Fallback ai tag immagine
                img_tags = soup.select('img')
                if len(img_tags) > 1:  # Salta il primo (logo di Google)
                    for img in img_tags[1:10]:  # Prova più risultati
                        src = img.get('src') or img.get('data-src')
                        if src and not src.startswith('data:'):
                            return src
        
        return None
    except Exception as e:
        print(f"Errore durante la ricerca su Google Images per {query}: {e}")
        return None

def search_librerie_coop(title, author):
    """Cerca copertine su Librerie Coop"""
    try:
        search_url = f"https://www.librerie.coop/it/libri-search?text={quote_plus(title)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Cerca elementi libro
            book_items = soup.select('.product-item')
            for item in book_items:
                # Controlla titolo e autore
                item_title_elem = item.select_one('.product-item-title')
                item_author_elem = item.select_one('.product-item-brand')
                
                if item_title_elem and item_author_elem:
                    item_title = item_title_elem.text.strip()
                    item_author = item_author_elem.text.strip()
                    
                    # Controlla se è il libro che stiamo cercando
                    if title.lower() in item_title.lower() and author.lower() in item_author.lower():
                        # Trova l'immagine della copertina
                        img_elem = item.select_one('.product-item-img img')
                        if img_elem:
                            img_url = img_elem.get('src') or img_elem.get('data-src')
                            if img_url:
                                if not img_url.startswith('http'):
                                    img_url = urljoin('https://www.librerie.coop/', img_url)
                                return img_url
        
        return None
    except Exception as e:
        print(f"Errore durante la ricerca su Librerie Coop per {title}: {e}")
        return None

def search_feltrinelli(title, author):
    """Cerca copertine su La Feltrinelli"""
    try:
        search_url = f"https://www.lafeltrinelli.it/ricerca/{quote_plus(title)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Cerca elementi libro
            book_items = soup.select('.product-card')
            for item in book_items:
                # Controlla titolo e autore
                item_title_elem = item.select_one('.product-card__title')
                item_author_elem = item.select_one('.product-card__author')
                
                if item_title_elem and item_author_elem:
                    item_title = item_title_elem.text.strip()
                    item_author = item_author_elem.text.strip()
                    
                    # Controlla se è il libro che stiamo cercando
                    if title.lower() in item_title.lower() and author.lower() in item_author.lower():
                        # Trova l'immagine della copertina
                        img_elem = item.select_one('.product-card__image img')
                        if img_elem:
                            img_url = img_elem.get('src') or img_elem.get('data-src')
                            if img_url:
                                if not img_url.startswith('http'):
                                    img_url = urljoin('https://www.lafeltrinelli.it/', img_url)
                                return img_url
        
        return None
    except Exception as e:
        print(f"Errore durante la ricerca su Feltrinelli per {title}: {e}")
        return None

def process_book(book):
    """Elabora un singolo libro: recupera e scarica la copertina"""
    title = book.get('title', '')
    author = book.get('author', '')
    book_id = f"{sanitize_filename(title)}_{sanitize_filename(author)}"
    filename = os.path.join(COVERS_DIR, f"{book_id}.jpg")
    
    # Salta se abbiamo già questo file
    if os.path.exists(filename):
        print(f"Saltando copertina esistente: {filename}")
        # Aggiorna il campo cover
        book['cover'] = f"data/book_covers/{book_id}.jpg"
        return book
    
    # Prova a ottenere la copertina dal link di acquisto
    cover_url = None
    link = book.get('link_acquisto', '')
    
    if 'ibs.it' in link:
        cover_url = get_cover_from_ibs(link)
    elif 'amazon.com' in link:
        cover_url = get_cover_from_amazon(link)
    
    # Se non ha trovato copertina, prova siti italiani
    if not cover_url:
        cover_url = search_librerie_coop(title, author)
    
    if not cover_url:
        cover_url = search_feltrinelli(title, author)
    
    # Se ancora non ha trovato copertina, prova Google Images
    if not cover_url:
        search_query = f"{title} {author}"
        cover_url = search_google_images(search_query)
    
    # Scarica l'immagine se trovata
    if cover_url:
        success = download_image(cover_url, filename)
        if success:
            # Aggiorna il campo cover nel libro
            book['cover'] = f"data/book_covers/{book_id}.jpg"
        else:
            print(f"Impossibile scaricare la copertina per: {title}")
    else:
        print(f"Nessuna copertina trovata per: {title}")
    
    # Attendi per essere gentile con i server
    time.sleep(1.5)
    
    return book

def main():
    # Carica il file JSON
    try:
        books_path = os.path.join('data', 'books.json')
        with open(books_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except Exception as e:
        print(f"Errore nel caricamento del file JSON: {e}")
        return
    
    print(f"Caricati {len(books)} libri dal file JSON")
    
    # Elabora i libri in parallelo con un numero limitato di worker
    updated_books = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        updated_books = list(executor.map(process_book, books))
    
    # Salva il file JSON aggiornato
    try:
        with open(books_path, 'w', encoding='utf-8') as f:
            json.dump(updated_books, f, ensure_ascii=False, indent=2)
        print("File JSON aggiornato con i percorsi delle copertine")
    except Exception as e:
        print(f"Errore nel salvataggio del file JSON: {e}")
    
    print("Elaborazione di tutti i libri completata")

if __name__ == "__main__":
    main()
