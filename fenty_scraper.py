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
        data = response.json()
        produits = data.get("products", [])
        if not produits: break
        for product in produits:
            variante = product["variants"][0] if product.get("variants") else {}
            nb_teintes = len(product.get("variants", []))
            dispo = "en stock" if variante.get("available") else "rupture"
            url_produit = f"https://fentybeauty.com/en-fr/products/{product['handle']}"
            page_produit = requests.get(url_produit, headers=headers)
            soup = BeautifulSoup(page_produit.text, "html.parser")
            desc_bloc = soup.find("div", class_="product-hero__short-description")
            description = desc_bloc.text.strip() if desc_bloc else ""
            ligne = [product["title"], product.get("vendor"), product.get("product_type"), variante.get("price"), variante.get("compare_at_price", ""), "", "", "", nb_teintes, "", "", "", dispo, f"https://fentybeauty.com/en-fr/products/{product['handle']}"]
            writer.writerow(ligne)
        print(f"Page {page} scrapée.")
        time.sleep(1)    