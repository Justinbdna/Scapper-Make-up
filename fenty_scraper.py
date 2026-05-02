import requests
from bs4 import BeautifulSoup
import csv

URL = "https://fentybeauty.com/en-fr/collections/makeup-face-foundation/products.json"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
response = requests.get(URL, headers=headers)
data = response.json()

print("Nombre de produits trouvés :", len(data["products"]))

with open("fenty_teint.csv", "w", newline="", encoding="utf-8") as fichier:
    writer = csv.writer(fichier)
    for product in data["products"]:
        writer.writerow([product["title"], f"https://fentybeauty.com/en-fr/products/{product['handle']}"])
        variante = product["variants"][0] if product.get("variants") else {}
        nb_teintes = len(product.get("variants", []))
        dispo = "en stock" if variante.get("available") else "rupture"
        ligne = [product["title"], product.get("vendor"), product.get("product_type"), variante.get("price"), variante.get("compare_at_price", ""), "", "", "", nb_teintes, "", "", "", dispo, f"https://fentybeauty.com/en-fr/products/{product['handle']}"]
        writer.writerow(ligne)