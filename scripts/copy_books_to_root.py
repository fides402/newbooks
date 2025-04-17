import shutil
import os

SOURCE = os.path.join(os.path.dirname(__file__), "data", "books.json")
DEST = os.path.join(os.path.dirname(__file__), "books.json")

try:
    shutil.copy(SOURCE, DEST)
    print(f"✅ Copiato books.json da /data/ alla root.")
except Exception as e:
    print(f"❌ Errore nella copia: {e}")
