import subprocess
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

scripts = [
    "scraper_libri_italiani_links.py",
    "scraper_libri_americani_links.py",
    "organizza_dati_links.py",
    "genera_books_json.py",
    "aggiungi_copertine.py"
]

for script in scripts:
    subprocess.run([sys.executable, os.path.join(current_dir, script)], check=True)
