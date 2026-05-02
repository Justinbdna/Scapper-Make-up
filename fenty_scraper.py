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
    writer.writerow(["Titre", "URL"])
    for product in data["products"]:
        writer.writerow([product["title"], f"https://fentybeauty.com/en-fr/products/{product['handle']}"])