import json
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from concurrent.futures import ThreadPoolExecutor
import re

# Create a directory to store the downloaded covers
if not os.path.exists('book_covers'):
    os.makedirs('book_covers')

def sanitize_filename(filename):
    """Remove invalid characters from filenames"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_image(url, filename):
    """Download an image from URL and save it to the specified filename"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded: {filename}")
            return True
        else:
            print(f"Failed to download {url}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def get_cover_from_ibs(url):
    """Extract cover image URL from IBS.it product page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://www.ibs.it/',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple possible selectors for IBS.it
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
                    # Check for src or data-src
                    img_url = img_container.get('src') or img_container.get('data-src')
                    if img_url:
                        if not img_url.startswith('http'):
                            img_url = urljoin('https://www.ibs.it/', img_url)
                        # Replace any size parameters with larger ones
                        img_url = re.sub(r'_\d+x\d+', '_1200x1200', img_url)
                        return img_url
            
            # If no image found with selectors, try to find any large image on the page
            all_images = soup.select('img')
            for img in all_images:
                src = img.get('src') or img.get('data-src')
                if src and ('cover' in src.lower() or 'copertina' in src.lower() or 'product' in src.lower()):
                    if not src.startswith('http'):
                        src = urljoin('https://www.ibs.it/', src)
                    return src
        
        return None
    except Exception as e:
        print(f"Error scraping IBS {url}: {e}")
        return None

def get_cover_from_amazon(url):
    """Extract cover image URL from Amazon product page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.amazon.com/',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple possible selectors for Amazon
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
                    # Try data-a-dynamic-image first (JSON string with URLs)
                    if img_container.get('data-a-dynamic-image'):
                        try:
                            img_urls = json.loads(img_container.get('data-a-dynamic-image'))
                            if img_urls:
                                largest_img_url = sorted(img_urls.keys(), key=lambda x: img_urls[x][0] * img_urls[x][1], reverse=True)[0]
                                return largest_img_url
                        except:
                            pass
                    
                    # Try data-old-hires
                    if img_container.get('data-old-hires'):
                        return img_container.get('data-old-hires')
                    
                    # Try src
                    if img_container.get('src'):
                        img_url = img_container.get('src')
                        # Try to get higher resolution by modifying URL
                        img_url = img_url.replace('._SL500_', '._SL1500_').replace('._SY300_', '._SY1500_')
                        return img_url
        
        return None
    except Exception as e:
        print(f"Error scraping Amazon {url}: {e}")
        return None

def search_google_images(query):
    """Search for book cover on Google Images as a fallback"""
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
                'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
                'Referer': 'https://www.google.com/',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find image URLs in different formats
                # In modern Google Images, some images are stored in JSON data
                scripts = soup.select('script')
                for script in scripts:
                    if script.string and 'AF_initDataCallback' in script.string:
                        raw_data = script.string
                        img_urls = re.findall(r'https?://\S+?\.(?:jpg|jpeg|png|webp)', raw_data)
                        if img_urls:
                            for url in img_urls:
                                if 'books' in url.lower() or 'cover' in url.lower() or 'ibs' in url.lower() or 'feltrinelli' in url.lower() or 'mondadori' in url.lower():
                                    return url
                
                # Fallback to regular image tags
                img_tags = soup.select('img')
                if len(img_tags) > 1:  # Skip the first one as it's usually Google's logo
                    for img in img_tags[1:10]:  # Try more results
                        src = img.get('src') or img.get('data-src')
                        if src and not src.startswith('data:'):
                            return src
        
        return None
    except Exception as e:
        print(f"Error searching Google Images for {query}: {e}")
        return None

def search_librerie_coop(title, author):
    """Search Librerie Coop for book covers"""
    try:
        search_url = f"https://www.librerie.coop/it/libri-search?text={quote_plus(title)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for book items
            book_items = soup.select('.product-item')
            for item in book_items:
                # Check if title and author match
                item_title_elem = item.select_one('.product-item-title')
                item_author_elem = item.select_one('.product-item-brand')
                
                if item_title_elem and item_author_elem:
                    item_title = item_title_elem.text.strip()
                    item_author = item_author_elem.text.strip()
                    
                    # Check if this is the book we're looking for
                    if title.lower() in item_title.lower() and author.lower() in item_author.lower():
                        # Find the cover image
                        img_elem = item.select_one('.product-item-img img')
                        if img_elem:
                            img_url = img_elem.get('src') or img_elem.get('data-src')
                            if img_url:
                                if not img_url.startswith('http'):
                                    img_url = urljoin('https://www.librerie.coop/', img_url)
                                return img_url
        
        return None
    except Exception as e:
        print(f"Error searching Librerie Coop for {title}: {e}")
        return None

def search_feltrinelli(title, author):
    """Search La Feltrinelli for book covers"""
    try:
        search_url = f"https://www.lafeltrinelli.it/ricerca/{quote_plus(title)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for book items
            book_items = soup.select('.product-card')
            for item in book_items:
                # Check title and author
                item_title_elem = item.select_one('.product-card__title')
                item_author_elem = item.select_one('.product-card__author')
                
                if item_title_elem and item_author_elem:
                    item_title = item_title_elem.text.strip()
                    item_author = item_author_elem.text.strip()
                    
                    # Check if this is the book we're looking for
                    if title.lower() in item_title.lower() and author.lower() in item_author.lower():
                        # Find the cover image
                        img_elem = item.select_one('.product-card__image img')
                        if img_elem:
                            img_url = img_elem.get('src') or img_elem.get('data-src')
                            if img_url:
                                if not img_url.startswith('http'):
                                    img_url = urljoin('https://www.lafeltrinelli.it/', img_url)
                                return img_url
        
        return None
    except Exception as e:
        print(f"Error searching Feltrinelli for {title}: {e}")
        return None

def search_mondadori(title, author):
    """Search Mondadori Store for book covers"""
    try:
        search_url = f"https://www.mondadoristore.it/search/?tpr=90&q={quote_plus(title)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for book items
            book_items = soup.select('.product-list-item')
            for item in book_items:
                # Check title and author
                item_title_elem = item.select_one('.item-title')
                item_author_elem = item.select_one('.item-author')
                
                if item_title_elem and item_author_elem:
                    item_title = item_title_elem.text.strip()
                    item_author = item_author_elem.text.strip()
                    
                    # Check if this is the book we're looking for
                    if title.lower() in item_title.lower() and author.lower() in item_author.lower():
                        # Find the cover image
                        img_elem = item.select_one('.item-img img')
                        if img_elem:
                            img_url = img_elem.get('src') or img_elem.get('data-src')
                            if img_url:
                                if not img_url.startswith('http'):
                                    img_url = urljoin('https://www.mondadoristore.it/', img_url)
                                # Try to get higher resolution
                                img_url = img_url.replace('_Small', '_Large').replace('_Medium', '_Large')
                                return img_url
        
        return None
    except Exception as e:
        print(f"Error searching Mondadori for {title}: {e}")
        return None

def process_book(book):
    """Process a single book: scrape and download its cover"""
    title = book.get('title', '')
    author = book.get('author', '')
    book_id = f"{sanitize_filename(title)}_{sanitize_filename(author)}"
    filename = os.path.join('book_covers', f"{book_id}.jpg")
    
    # Skip if we already have this file
    if os.path.exists(filename):
        print(f"Skipping existing cover: {filename}")
        return
    
    # Try to get cover from purchase link
    cover_url = None
    link = book.get('link_acquisto', '')
    
    if link:
        if 'ibs.it' in link:
            cover_url = get_cover_from_ibs(link)
        elif 'amazon.com' in link:
            cover_url = get_cover_from_amazon(link)
    
    # If no cover found, try Italian book retailers
    if not cover_url:
        cover_url = search_librerie_coop(title, author)
    
    if not cover_url:
        cover_url = search_feltrinelli(title, author)
    
    if not cover_url:
        cover_url = search_mondadori(title, author)
    
    # If still no cover, try Google Images as fallback
    if not cover_url:
        search_query = f"{title} {author}"
        cover_url = search_google_images(search_query)
    
    # Download the image if found
    if cover_url:
        success = download_image(cover_url, filename)
        if not success:
            print(f"Failed to download cover for: {title}")
    else:
        print(f"No cover found for: {title}")
    
    # Be nice to the servers and avoid being blocked
    time.sleep(1.5)  # Increased delay to be more respectful to servers

def main():
    # Load the JSON file
    try:
        with open('books.json', 'r', encoding='utf-8') as f:
            books = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return
    
    print(f"Loaded {len(books)} books from JSON file")
    
    # Process books in parallel with a limited number of workers
    with ThreadPoolExecutor(max_workers=3) as executor:  # Reduced workers to be gentler to websites
        executor.map(process_book, books)
    
    print("Finished processing all books")

if __name__ == "__main__":
    main()
