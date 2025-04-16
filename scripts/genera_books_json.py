import os
import pandas as pd
import json

# Percorsi
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ITALIAN_CSV = os.path.join(SCRIPT_DIR, "libri_italiani_links.csv")
AMERICAN_CSV = os.path.join(SCRIPT_DIR, "libri_americani_links.csv")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "../data/books.json")

# Carica i CSV se esistono
df_list = []

if os.path.exists(ITALIAN_CSV):
    df_italian = pd.read_csv(ITALIAN_CSV)
    df_italian["origin"] = "IT"
    df_italian = df_italian.rename(columns={"titolo": "title", "autore": "author"})
    df_list.append(df_italian[["title", "author", "categoria", "link_acquisto", "origin"]])

if os.path.exists(AMERICAN_CSV):
    df_american = pd.read_csv(AMERICAN_CSV)
    df_american["origin"] = "US"
    df_american = df_american.rename(columns={"titolo": "title", "autore": "author"})
    df_american["categoria"] = df_american.get("categoria", "Various")
    df_list.append(df_american[["title", "author", "categoria", "link_acquisto", "origin"]])

if df_list:
    df_all = pd.concat(df_list, ignore_index=True)
    df_all["releaseDate"] = pd.Timestamp.today().strftime("%Y-%m-%d")
    df_all["cover"] = ""  # Se vuoi aggiungerlo in futuro
    df_all = df_all.fillna("")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(df_all.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

    print(f"[✓] Creato {OUTPUT_JSON}")
else:
    print("[!] Nessun CSV trovato. JSON non creato.")
