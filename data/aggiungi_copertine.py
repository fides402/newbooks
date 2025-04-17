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
                                is_good_quality, _ = check_image_quality(img_url)
                                if is_good_quality:
                                    return img_url
            
            except Exception as e:
                logger.error(f"Errore durante la ricerca su Google Images per {search_term} (tentativo {attempt+1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
    
    return None

def search_duckduckgo_images(query):
    """Cerca la copertina del libro su DuckDuckGo come alternativa a Google Images"""
    try:
        search_url = f"https://duckduckgo.com/?q={quote_plus(query + ' libro copertina')}&t=h_&iax=images&ia=images"
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Cerca le immagini
            scripts = soup.select('script')
            for script in scripts:
                if script.string and 'vqd' in script.string:
                    vqd_match = re.search(r'vqd=\'(.*?)\'', script.string)
                    if vqd_match:
                        vqd = vqd_match.group(1)
                        # Ora possiamo fare la richiesta API
                        api_url = f"https://duckduckgo.com/i.js?q={quote_plus(query + ' libro copertina')}&vqd={vqd}"
                        
                        api_response = requests.get(api_url, headers=headers, timeout=15)
                        if api_response.status_code == 200:
                            try:
                                data = api_response.json()
                                if 'results' in data and len(data['results']) > 0:
                                    # Filtra per immagini rilevanti
                                    relevant_images = []
                                    for result in data['results']:
                                        if 'image' in result:
                                            image_url = result['image']
                                            if ('books' in image_url.lower() or 'cover' in image_url.lower() 
                                                or 'libro' in image_url.lower() or 'copertina' in image_url.lower()):
                                                
                                                is_good_quality, dimensions = check_image_quality(image_url)
                                                if is_good_quality:
                                                    return image_url
                                                else:
                                                    relevant_images.append((image_url, dimensions[0] * dimensions[1]))
                                    
                                    # Usa la migliore disponibile
                                    if relevant_images:
                                        relevant_images.sort(key=lambda x: x[1], reverse=True)
                                        return relevant_images[0][0]
                            except:
                                pass
            
            # Fallback: cerca direttamente nelle immagini della pagina
            img_tags = soup.select('img.tile--img__img')
            for img in img_tags[:5]:
                src = img.get('src') or img.get('data-src')
                if src and not src.startswith('data:'):
                    return src
        
        return None
    except Exception as e:
        logger.error(f"Errore durante la ricerca su DuckDuckGo Images per {query}: {e}")
        return None

def search_open_library(title, author):
    """Cerca copertine su Open Library"""
    try:
        # Cerca prima per ISBN se disponibile
        query = f"{title} {author}"
        search_url = f"https://openlibrary.org/search.json?q={quote_plus(query)}"
        
        response = get_request_with_retry(search_url)
        if response and response.status_code == 200:
            data = response.json()
            if 'docs' in data and len(data['docs']) > 0:
                # Filtra per corrispondenza di titolo e autore
                for doc in data['docs']:
                    if 'title' in doc and 'author_name' in doc:
                        doc_title = doc['title'].lower()
                        doc_authors = [a.lower() for a in doc['author_name']]
                        
                        # Verifica flessibile
                        if any(word.lower() in doc_title for word in title.split() if len(word) > 3):
                            if any(author_word.lower() in ' '.join(doc_authors) for author_word in author.split() if len(author_word) > 3):
                                # Controlla se ha un ISBN
                                if 'isbn' in doc and len(doc['isbn']) > 0:
                                    isbn = doc['isbn'][0]
                                    cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
                                    
                                    # Verifica se la copertina esiste ed è valida
                                    is_good_quality, _ = check_image_quality(cover_url)
                                    if is_good_quality:
                                        return cover_url
                                
                                # Se non ha ISBN, prova con OLID
                                if 'key' in doc:
                                    olid = doc['key'].split('/')[-1]
                                    cover_url = f"https://covers.openlibrary.org/b/olid/{olid}-L.jpg"
                                    
                                    is_good_quality, _ = check_image_quality(cover_url)
                                    if is_good_quality:
                                        return cover_url
        
        return None
    except Exception as e:
        logger.error(f"Errore durante la ricerca su Open Library per {title}: {e}")
        return None

def get_default_cover():
    """Restituisce un URL di copertina di default nel caso in cui nessuna ricerca abbia successo"""
    return "https://www.fillmurray.com/800/1200"  # Esempio di immagine placeholder

def process_book(book):
    """Elabora un singolo libro: recupera e scarica la copertina"""
    title = book.get('title', '')
    author = book.get('author', '')
    book_id = f"{sanitize_filename(title)}_{sanitize_filename(author)}"
    filename = os.path.join(COVERS_DIR, f"{book_id}.jpg")
    
    logger.info(f"Elaborazione copertina per: {title} di {author}")
    
    # Salta se abbiamo già questo file
    if os.path.exists(filename):
        logger.info(f"Saltando copertina esistente: {filename}")
        # Aggiorna il campo cover
        book['cover'] = f"data/book_covers/{book_id}.jpg"
        return book
    
    # Lista per tenere traccia delle fonti tentate
    attempted_sources = []
    cover_url = None
    
    # Prova a ottenere la copertina dal link di acquisto
    link = book.get('link_acquisto', '')
    
    if link and 'ibs.it' in link:
        logger.info(f"Tentativo copertina da IBS.it: {link}")
        attempted_sources.append('IBS.it')
        cover_url = get_cover_from_ibs(link)
    
    if not cover_url and link and 'amazon' in link:
        logger.info(f"Tentativo copertina da Amazon: {link}")
        attempted_sources.append('Amazon')
        cover_url = get_cover_from_amazon(link)
    
    # Se non ha trovato copertina, prova i vari siti di librerie italiane
    if not cover_url:
        logger.info(f"Tentativo copertina da Mondadori")
        attempted_sources.append('Mondadori')
        cover_url = search_mondadori(title, author)
    
    if not cover_url:
        logger.info(f"Tentativo copertina da Feltrinelli")
        attempted_sources.append('Feltrinelli')
        cover_url = search_feltrinelli(title, author)
    
    if not cover_url:
        logger.info(f"Tentativo copertina da Librerie Coop")
        attempted_sources.append('Librerie Coop')
        cover_url = search_librerie_coop(title, author)
    
    if not cover_url:
        logger.info(f"Tentativo copertina da Hoepli")
        attempted_sources.append('Hoepli')
        cover_url = search_hoepli(title, author)
    
    if not cover_url:
        logger.info(f"Tentativo copertina da BOL")
        attempted_sources.append('BOL')
        cover_url = search_bol(title, author)
    
    # Prova siti internazionali
    if not cover_url:
        logger.info(f"Tentativo copertina da Goodreads")
        attempted_sources.append('Goodreads')
        cover_url = search_goodreads(title, author)
    
    if not cover_url:
        logger.info(f"Tentativo copertina da Open Library")
        attempted_sources.append('Open Library')
        cover_url = search_open_library(title, author)
    
    # Se ancora non ha trovato copertina, prova i motori di ricerca
    if not cover_url:
        search_query = f"{title} {author}"
        logger.info(f"Tentativo copertina da Google Images: {search_query}")
        attempted_sources.append('Google Images')
        cover_url = search_google_images(search_query)
    
    if not cover_url:
        logger.info(f"Tentativo copertina da DuckDuckGo: {search_query}")
        attempted_sources.append('DuckDuckGo')
        cover_url = search_duckduckgo_images(search_query)
    
    # Ultima spiaggia: usa una copertina di default
    if not cover_url:
        logger.warning(f"Nessuna copertina trovata per: {title} dopo aver tentato: {', '.join(attempted_sources)}")
        cover_url = get_default_cover()
    
    # Scarica l'immagine
    if cover_url:
        logger.info(f"Copertina trovata da {attempted_sources[-1]}: {cover_url}")
        success = download_image(cover_url, filename)
        if success:
            # Aggiorna il campo cover nel libro
            book['cover'] = f"data/book_covers/{book_id}.jpg"
            logger.info(f"Copertina scaricata con successo per: {title}")
        else:
            logger.error(f"Impossibile scaricare la copertina per: {title}")
    
    # Attendi per essere gentile con i server
    time.sleep(1)
    
    return book

def main():
    # Carica il file JSON
    try:
        books_path = os.path.join('data', 'books.json')
        with open(books_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except Exception as e:
        logger.error(f"Errore nel caricamento del file JSON: {e}")
        return
    
    logger.info(f"Caricati {len(books)} libri dal file JSON")
    
    # Elabora i libri in parallelo con un numero limitato di worker
    updated_books = []
    
    # Usa ThreadPoolExecutor per elaborare in parallelo
    with ThreadPoolExecutor(max_workers=3) as executor:
        updated_books = list(executor.map(process_book, books))
    
    # Conta quanti libri hanno copertine
    books_with_covers = sum(1 for book in updated_books if 'cover' in book)
    logger.info(f"Trovate copertine per {books_with_covers} libri su {len(updated_books)} totali ({books_with_covers/len(updated_books)*100:.1f}%)")
    
    # Salva il file JSON aggiornato
    try:
        with open(books_path, 'w', encoding='utf-8') as f:
            json.dump(updated_books, f, ensure_ascii=False, indent=2)
        logger.info("File JSON aggiornato con i percorsi delle copertine")
    except Exception as e:
        logger.error(f"Errore nel salvataggio del file JSON: {e}")
    
    logger.info("Elaborazione di tutti i libri completata")

if __name__ == "__main__":
    main()
