import requests
from bs4 import BeautifulSoup

URL = "https://fentybeauty.com/en-fr/collections/makeup-face-foundation.json"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
response = requests.get(URL, headers=headers)
data = response.json()

print("Nombre de produits trouvés :", len(data["products"]))

for product in data["products"][:5]:
    titre = product["title"]
    url_produit = f"https://fentybeauty.com/en-fr/products/{product['handle']}"
    print(f"{titre} | {url_produit}")