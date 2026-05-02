import requests
from bs4 import BeautifulSoup
import csv
import time

URL = "https://fentybeauty.com/en-fr/collections/makeup-face-foundation/products.json"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

with open("fenty_teint.csv", "w", newline="", encoding="utf-8") as fichier:
    writer = csv.writer(fichier)
    writer.writerow(["product_name", "brand", "category", "price", "promo_price", "volume_ml", "rating", "review_count", "shade_count", "finish_type", "coverage_level", "skin_type", "availability", "source_url"])
    for page in range(1, 6):
        response = requests.get(f"{URL}?page={page}", headers=headers)
        if response.status_code != 200:
            print(f"Erreur bloquante sur la page {page} : Code HTTP {response.status_code}")
            break
            
        data = response.json()
        produits = data.get("products", [])
        if not produits: break
        for product in produits:
            variante = product["variants"][0] if product.get("variants") else {}
            nb_teintes = len(product.get("variants", []))
            dispo = "en stock" if variante.get("available") else "rupture"
            taille = variante.get("title", "")
            url_produit = f"https://fentybeauty.com/en-fr/products/{product['handle']}"
            soup_desc = BeautifulSoup(product.get("body_html", ""), "html.parser")
            description = soup_desc.get_text().strip()
            desc_lower = description.lower()
            
            # Déduction de la couvrance
            if "full coverage" in desc_lower or "full" in desc_lower:
                couvrance = "couvrant"
            elif "medium" in desc_lower:
                couvrance = "moyen"
            elif "light" in desc_lower or "sheer" in desc_lower or "blurring" in desc_lower:
                couvrance = "léger"
            else:
                couvrance = ""
                
            # Déduction du fini
            if "matte" in desc_lower:
                fini = "mat"
            elif "luminous" in desc_lower or "glow" in desc_lower:
                fini = "lumineux"
            else:
                fini = ""
            ligne = [product["title"], product.get("vendor"), product.get("product_type"), variante.get("price"), variante.get("compare_at_price", ""), taille, "", "", nb_teintes, fini, couvrance, "", dispo, url_produit]
            writer.writerow(ligne)
            print(f"Page {page} scrapée avec succès.")
        time.sleep(5)    