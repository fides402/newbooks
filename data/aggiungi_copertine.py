import json
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import re
from concurrent.futures import ThreadPoolExecutor
import random
try:
    from PIL import Image
    from io import BytesIO
except ImportError:
    print("AVVISO: PIL non disponibile, il controllo della qualità dell'immagine sarà limitato")

# Configurazione del logging base
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory per le copertine dei libri
COVERS_DIR = os.path.join('data', 'book_covers')

# Crea la directory se non esiste
if not os.path.exists(COVERS_DIR):
    os.makedirs(COVERS_DIR)

# Elenco di User-Agent per rotazione
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

def get_random_user_agent():
    """Restituisce un User-Agent casuale dalla lista"""
    return random.choice(USER_AGENTS)

def sanitize_filename(filename):
    """Rimuove caratteri non validi dai nomi file"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_request_with_retry(url, max_retries=3, delay=2):
    """Effettua una richiesta HTTP con tentativi multipli in caso di errore"""
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            return response
        except Exception as e:
            if attempt < max_retries - 1:
                sleep_time = delay * (attempt + 1)
                print(f"Tentativo {attempt+1} fallito per {url}: {e}. Riprovo tra {sleep_time}s")
                time.sleep(sleep_time)
            else:
                print(f"Tutti i tentativi falliti per {url}: {e}")
                return None

def check_image_quality(image_url):
    """Verifica la qualità dell'immagine tramite dimensioni"""
    try:
        # Verifica se PIL è disponibile
        if 'Image' not in globals():
            # Bypass della verifica di qualità se PIL non è disponibile
            return True, (400, 600)
            
        response = get_request_with_retry(image_url)
        if response and response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            width, height = image.size
            area = width * height
            print(f"Dimensioni immagine: {width}x{height} ({area} px)")
            
            # Restituisci True se l'immagine è abbastanza grande (> 90000 px)
            return area > 90000, (width, height)
        return False, (0, 0)
    except Exception as e:
        print(f"Errore durante il controllo dell'immagine {image_url}: {e}")
        return False, (0, 0)

def download_image(url, filename):
    """Scarica un'immagine dall'URL e la salva nel file specificato"""
    try:
        response = get_request_with_retry(url)
        if response and response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Scaricato: {filename}")
            return True
        else:
            print(f"Impossibile scaricare {url}: HTTP {response.status_code if response else 'No Response'}")
            return False
    except Exception as e:
        print(f"Errore nel download di {url}: {e}")
        return False

def get_cover_from_ibs(url):
    """Estrae l'URL dell'immagine di copertina dalla pagina del prodotto su IBS.it"""
    try:
        response = get_request_with_retry(url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Selettori aggiornati per IBS.it
            selectors = [
                '.product-gallery__featured-image img',
                '.product-gallery__item img',
                '.carousel-container img',
                'img.photo',
                '.img-wrapper img',
                'img[data-src*="cover"]',
                'img[src*="cover"]',
                '.cover-image img',
                'img[alt*="copertina"]',
                '.detail-img img',
                'img[data-testid="product-image"]',
                '.item-img img',
                'img[data-a-image-name="landingImage"]',
                '.product-main-detail-img img'
            ]
            
            # Cerca usando selettori
            for selector in selectors:
                img_containers = soup.select(selector)
                for img_container in img_containers:
                    img_url = img_container.get('src') or img_container.get('data-src')
                    if img_url:
                        if not img_url.startswith('http'):
                            img_url = urljoin('https://www.ibs.it/', img_url)
                        # Migliora la risoluzione dell'immagine
                        img_url = re.sub(r'_\d+x\d+', '_1500x1500', img_url)
                        return img_url
            
            # Ricerca tramite JSON nei dati della pagina
            scripts = soup.select('script[type="application/ld+json"]')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'image' in data:
                        if isinstance(data['image'], str):
                            return data['image']
                        elif isinstance(data['image'], list) and len(data['image']) > 0:
                            return data['image'][0]
                except:
                    pass
            
            # Ricerca generica di immagini sulla pagina
            all_images = soup.select('img')
            for img in all_images:
                src = img.get('src') or img.get('data-src')
                if src and ('cover' in src.lower() or 'copertina' in src.lower() or 'product' in src.lower()):
                    if not src.startswith('http'):
                        src = urljoin('https://www.ibs.it/', src)
                    # Migliora la risoluzione
                    src = re.sub(r'(\/\w+)_\d+x\d+(\.jpg|\.png|\.jpeg)', r'\1_1500x1500\2', src)
                    return src
        
        return None
    except Exception as e:
        print(f"Errore durante lo scraping di IBS {url}: {e}")
        return None

def get_cover_from_amazon(url):
    """Estrae l'URL dell'immagine di copertina dalla pagina del prodotto su Amazon"""
    try:
        response = get_request_with_retry(url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Selettori aggiornati per Amazon
            selectors = [
                '#imgBlkFront',
                '#landingImage',
                '#main-image',
                '#ebooksImgBlkFront',
                'img.a-dynamic-image',
                'img[data-a-dynamic-image]',
                'img[data-old-hires]',
                'img.frontImage',
                '#imageBlock img',
                '#img-canvas img',
                'img[data-zoom-hires]',
                'img.image'
            ]
            
            # Cerca usando selettori
            for selector in selectors:
                img_container = soup.select_one(selector)
                if img_container:
                    # Prova a ottenere da data-a-dynamic-image (JSON con più risoluzioni)
                    if img_container.get('data-a-dynamic-image'):
                        try:
                            img_urls = json.loads(img_container.get('data-a-dynamic-image'))
                            if img_urls:
                                largest_img_url = sorted(img_urls.keys(), key=lambda x: img_urls[x][0] * img_urls[x][1], reverse=True)[0]
                                return largest_img_url
                        except:
                            pass
                    
                    # Altri attributi di immagine in ordine di preferenza
                    for attr in ['data-old-hires', 'data-zoom-hires', 'data-large-image', 'data-a-image-name']:
                        if img_container.get(attr):
                            return img_container.get(attr)
                    
                    # URL di base con miglioramento della risoluzione
                    if img_container.get('src'):
                        img_url = img_container.get('src')
                        # Migliora la risoluzione
                        img_url = img_url.replace('._SL500_', '._SL1500_').replace('._SY300_', '._SY1500_')
                        return img_url
            
            # Cerca nei JSON della pagina
            scripts = soup.select('script[type="text/javascript"]')
            for script in scripts:
                if script.string and ("'colorImages'" in script.string or "'imageGalleryData'" in script.string or "'imageBlock'" in script.string):
                    matches = re.search(r'(https://[^"\']+?\.jpg)', script.string)
                    if matches:
                        img_url = matches.group(1)
                        # Migliora la risoluzione
                        img_url = img_url.replace('._SL500_', '._SL1500_').replace('._SY300_', '._SY1500_')
                        return img_url
        
        return None
    except Exception as e:
        print(f"Errore durante lo scraping di Amazon {url}: {e}")
        return None

def search_librerie_coop(title, author):
    """Cerca copertine su Librerie Coop"""
    try:
        search_url = f"https://www.librerie.coop/it/libri-search?text={quote_plus(title + ' ' + author)}"
        response = get_request_with_retry(search_url)
        
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Selettori aggiornati
            book_items = soup.select('.product-item, .product-card, .book-item')
            for item in book_items:
                # Selettori più generici per titolo e autore
                title_selectors = ['.product-item-title', '.product-card-title', '.book-title', 'h3.title', '.book-name']
                author_selectors = ['.product-item-brand', '.product-card-author', '.book-author', '.author', '.book-creator']
                
                item_title = None
                for selector in title_selectors:
                    elem = item.select_one(selector)
                    if elem:
                        item_title = elem.text.strip()
                        break
                
                item_author = None
                for selector in author_selectors:
                    elem = item.select_one(selector)
                    if elem:
                        item_author = elem.text.strip()
                        break
                
                if item_title and item_author:
                    # Verifica se è il libro cercato (controllo meno stringente)
                    title_words = set(title.lower().split())
                    author_words = set(author.lower().split())
                    item_title_words = set(item_title.lower().split())
                    item_author_words = set(item_author.lower().split())
                    
                    # Calcola l'intersezione delle parole
                    if len(title_words) > 0 and len(author_words) > 0:
                        title_match = len(title_words.intersection(item_title_words)) / len(title_words) > 0.5
                        author_match = len(author_words.intersection(item_author_words)) / len(author_words) > 0.3
                        
                        if title_match and author_match:
                            # Selettori immagine più completi
                            img_selectors = [
                                '.product-item-img img', 
                                '.product-card-image img', 
                                '.book-cover img', 
                                '.cover img', 
                                '.card-img img'
                            ]
                            
                            for selector in img_selectors:
                                img_elem = item.select_one(selector)
                                if img_elem:
                                    img_url = img_elem.get('src') or img_elem.get('data-src')
                                    if img_url:
                                        if not img_url.startswith('http'):
                                            img_url = urljoin('https://www.librerie.coop/', img_url)
                                        
                                        # Migliora la risoluzione
                                        img_url = re.sub(r'(\w+)_\d+x\d+(\.jpg|\.png|\.jpeg)', r'\1_1500x1500\2', img_url)
                                        return img_url
        
        return None
    except Exception as e:
        print(f"Errore durante la ricerca su Librerie Coop per {title}: {e}")
        return None

def search_feltrinelli(title, author):
    """Cerca copertine su La Feltrinelli"""
    try:
        search_url = f"https://www.lafeltrinelli.it/ricerca/{quote_plus(title + ' ' + author)}"
        response = get_request_with_retry(search_url)
        
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Selettori aggiornati
            book_items = soup.select('.product-card, .product-item, .book-card')
            for item in book_items:
                title_selectors = ['.product-card__title', '.product-title', '.book-title', 'h3.title']
                author_selectors = ['.product-card__author', '.product-author', '.book-author', '.author']
                
                item_title = None
                for selector in title_selectors:
                    elem = item.select_one(selector)
                    if elem:
                        item_title = elem.text.strip()
                        break
                
                item_author = None
                for selector in author_selectors:
                    elem = item.select_one(selector)
                    if elem:
                        item_author = elem.text.strip()
                        break
                
                if item_title and item_author:
                    # Verifica se è il libro cercato (controllo meno stringente)
                    if (title.lower() in item_title.lower() or item_title.lower() in title.lower()) and \
                       (author.lower() in item_author.lower() or item_author.lower() in author.lower()):
                        
                        img_selectors = [
                            '.product-card__image img', 
                            '.product-image img', 
                            '.book-cover img', 
                            '.cover img',
                            'img.cover-image'
                        ]
                        
                        for selector in img_selectors:
                            img_elem = item.select_one(selector)
                            if img_elem:
                                img_url = img_elem.get('src') or img_elem.get('data-src')
                                if img_url:
                                    if not img_url.startswith('http'):
                                        img_url = urljoin('https://www.lafeltrinelli.it/', img_url)
                                    
                                    # Migliora la risoluzione
                                    img_url = re.sub(r'(\w+)_\d+x\d+(\.jpg|\.png|\.jpeg)', r'\1_1500x1500\2', img_url)
                                    return img_url
        
        return None
    except Exception as e:
        print(f"Errore durante la ricerca su Feltrinelli per {title}: {e}")
        return None

def search_mondadori(title, author):
    """Cerca copertine su Mondadori Store"""
    try:
        search_url = f"https://www.mondadoristore.it/search/?tpr=100&g={quote_plus(title + ' ' + author)}"
        response = get_request_with_retry(search_url)
        
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Selettori per Mondadori
            book_items = soup.select('.item, .prod-item, .product-item')
            for item in book_items:
                title_selectors = ['.titolo', '.title', '.prod-title', '.item-title']
                author_selectors = ['.autore', '.author', '.prod-author', '.item-author']
                
                item_title = None
                for selector in title_selectors:
                    elem = item.select_one(selector)
                    if elem:
                        item_title = elem.text.strip()
                        break
                
                item_author = None
                for selector in author_selectors:
                    elem = item.select_one(selector)
                    if elem:
                        item_author = elem.text.strip()
                        break
                
                if item_title and item_author:
                    # Verifica con controllo flessibile
                    title_words = [w.lower() for w in title.split() if len(w) > 3]
                    author_words = [w.lower() for w in author.split() if len(w) > 3]
                    
                    if not title_words:  # Se non ci sono parole lunghe, usa tutte le parole
                        title_words = [w.lower() for w in title.split()]
                    
                    if not author_words:
                        author_words = [w.lower() for w in author.split()]
                    
                    title_match = any(w in item_title.lower() for w in title_words)
                    author_match = any(w in item_author.lower() for w in author_words)
                    
                    if title_match and author_match:
                        img_selectors = [
                            '.libro-img img', 
                            '.prod-img img', 
                            '.item-img img',
                            '.item img',
                            'img.img-prod',
                            'img.cover'
                        ]
                        
                        for selector in img_selectors:
                            img_elem = item.select_one(selector)
                            if img_elem:
                                img_url = img_elem.get('src') or img_elem.get('data-src')
                                if img_url:
                                    if not img_url.startswith('http'):
                                        img_url = urljoin('https://www.mondadoristore.it/', img_url)
                                    
                                    # Migliora la risoluzione
                                    img_url = re.sub(r'(\w+)_\d+x\d+(\.jpg|\.png|\.jpeg)', r'\1_1000x1000\2', img_url)
                                    return img_url
        
        return None
    except Exception as e:
        print(f"Errore durante la ricerca su Mondadori per {title}: {e}")
        return None

def search_hoepli(title, author):
    """Cerca copertine su Hoepli"""
    try:
        search_url = f"https://www.hoepli.it/cerca/libri.aspx?query={quote_plus(title + ' ' + author)}"
        response = get_request_with_retry(search_url)
        
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Selettori per Hoepli
            book_items = soup.select('.book-item, .prodotto, .product')
            for item in book_items:
                # Cerca titolo e autore
                title_elem = item.select_one('.title, .titolo, h3')
                author_elem = item.select_one('.author, .autore, .authors')
                
                if title_elem and author_elem:
                    item_title = title_elem.text.strip()
                    item_author = author_elem.text.strip()
                    
                    # Controllo più flessibile
                    title_words = [w.lower() for w in title.split() if len(w) > 3]
                    author_words = [w.lower() for w in author.split() if len(w) > 3]
                    
                    if not title_words:  # Se non ci sono parole lunghe, usa tutte le parole
                        title_words = [w.lower() for w in title.split()]
                    
                    if not author_words:
                        author_words = [w.lower() for w in author.split()]
                    
                    title_match = any(w in item_title.lower() for w in title_words)
                    author_match = any(w in item_author.lower() for w in author_words)
                    
                    if title_match and author_match:
                        img_elem = item.select_one('img.cover, img.book-cover, img.product-image')
                        if img_elem:
                            img_url = img_elem.get('src') or img_elem.get('data-src')
                            if img_url:
                                if not img_url.startswith('http'):
                                    img_url = urljoin('https://www.hoepli.it/', img_url)
                                
                                # Migliora la risoluzione
                                img_url = img_url.replace('small', 'large').replace('medium', 'large')
                                return img_url
        
        return None
    except Exception as e:
        print(f"Errore durante la ricerca su Hoepli per {title}: {e}")
        return None

def search_google_images(query, max_attempts=3):
    """Cerca la copertina del libro su Google Images con tentativi multipli e query migliorate"""
    search_terms = [
        f"{query} copertina libro alta risoluzione",
        f"{query} book cover high resolution",
        f"{query} libro IBS copertina",
        f"{query} libro Feltrinelli copertina alta qualità",
        f"{query} libro Mondadori copertina hd",
        f"{query} libro goodreads cover",
        f"{query} copertina libro edizione italiana"
    ]
    
    for search_term in search_terms:
        for attempt in range(max_attempts):
            try:
                search_url = f"https://www.google.com/search?q={quote_plus(search_term)}&tbm=isch"
                headers = {
                    'User-Agent': get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3'
                }
                
                response = requests.get(search_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Cerca nei dati JSON all'interno degli script
                    scripts = soup.select('script')
                    for script in scripts:
                        if script.string and 'AF_initDataCallback' in script.string:
                            raw_data = script.string
                            img_urls = re.findall(r'(https?://\S+?\.(?:jpg|jpeg|png|webp))', raw_data)
                            
                            if img_urls:
                                # Filtra per immagini potenzialmente di copertine
                                relevant_images = []
                                for url in img_urls:
                                    if ('books' in url.lower() or 'cover' in url.lower() 
                                        or 'ibs' in url.lower() or 'feltrinelli' in url.lower() 
                                        or 'mondadori' in url.lower() or 'libreria' in url.lower()
                                        or 'bol' in url.lower() or 'hoepli' in url.lower()
                                        or 'goodreads' in url.lower()):
                                        
                                        # Controlla qualità immagine
                                        is_good_quality, dimensions = check_image_quality(url)
                                        if is_good_quality:
                                            return url
                                        else:
                                            relevant_images.append((url, dimensions[0] * dimensions[1]))
                                
                                # Se non abbiamo trovato immagini di alta qualità, usa la migliore disponibile
                                if relevant_images:
                                    # Ordina per dimensione (area) più grande
                                    relevant_images.sort(key=lambda x: x[1], reverse=True)
                                    return relevant_images[0][0]
                    
                    # Fallback ai tag immagine
                    img_tags = soup.select('img.rg_i, img.Q4LuWd')
                    for img in img_tags[:15]:  # Prova i primi 15 risultati
                        img_url = img.get('src') or img.get('data-src') or img.get('data-iurl')
                        if img_url and not img_url.startswith('data:'):
                            if len(img_url) > 10:  # Filtra URL troppo corti
                                return img_url
            
            except Exception as e:
                print(f"Errore durante la ricerca su Google Images per {search_term} (tentativo {attempt+1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
    
    return None

def get_default_cover():
    """Restituisce un URL di copertina di default nel caso in cui nessuna ricerca abbia successo"""
    return "https://via.placeholder.com/800x1200?text=Copertina+Non+Disponibile"

def process_book(book):
    """Elabora un singolo libro: recupera e scarica la copertina"""
    title = book.get('title', '')
    author = book.get('author', '')
    book_id = f"{sanitize_filename(title)}_{sanitize_filename(author)}"
    filename = os.path.join(COVERS_DIR, f"{book_id}.jpg")
    
    print(f"Elaborazione copertina per: {title} di {author}")
    
    # Salta se abbiamo già questo file
    if os.path.exists(filename):
        print(f"Saltando copertina esistente: {filename}")
        # Aggiorna il campo cover
        book['cover'] = f"data/book_covers/{book_id}.jpg"
        return book
    
    # Lista per tenere traccia delle fonti tentate
    attempted_sources = []
    cover_url = None
    
    # Prova a ottenere la copertina dal link di acquisto
    link = book.get('link_acquisto', '')
    
    if link and 'ibs.it' in link:
        print(f"Tentativo copertina da IBS.it: {link}")
        attempted_sources.append('IBS.it')
        cover_url = get_cover_from_ibs(link)
    
    if not cover_url and link and 'amazon' in link:
        print(f"Tentativo copertina da Amazon: {link}")
        attempted_sources.append('Amazon')
        cover_url = get_cover_from_amazon(link)
    
    # Se non ha trovato copertina, prova i vari siti di librerie italiane
    if not cover_url:
        print(f"Tentativo copertina da Mondadori")
        attempted_sources.append('Mondadori')
        cover_url = search_mondadori(title, author)
    
    if not cover_url:
        print(f"Tentativo copertina da Feltrinelli")
        attempted_sources.append('Feltrinelli')
        cover_url = search_feltrinelli(title, author)
    
    if not cover_url:
        print(f"Tentativo copertina da Librerie Coop")
        attempted_sources.append('Librerie Coop')
        cover_url = search_librerie_coop(title, author)
    
    if not cover_url:
        print(f"Tentativo copertina da Hoepli")
        attempted_sources.append('Hoepli')
        cover_url = search_hoepli(title, author)
    
    # Se ancora non ha trovato copertina, prova i motori di ricerca
    if not cover_url:
        search_query = f"{title} {author}"
        print(f"Tentativo copertina da Google Images: {search_query}")
        attempted_sources.append('Google Images')
        cover_url = search_google_images(search_query)
    
    # Ultima spiaggia: usa una copertina di default
    if not cover_url:
        print(f"Nessuna copertina trovata per: {title} dopo aver tentato: {', '.join(attempted_sources)}")
        cover_url = get_default_cover()
        attempted_sources.append('Default')
    
    # Scarica l'immagine
    if cover_url:
        print(f"Copertina trovata da {attempted_sources
