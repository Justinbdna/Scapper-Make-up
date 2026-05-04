from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import time

# 1. Configuration du navigateur
options = webdriver.ChromeOptions()
# options.add_argument('--headless') # Décommente pour que la fenêtre ne s'ouvre pas
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 2. Le site à scraper (on prend l'exemple Sephora du tableau)
url = "https://www.nocibe.fr/"
driver.get(url)
time.sleep(5) # On laisse le temps au site de charger

# 3. Liste pour stocker nos données
data_list = []

# 4. Extraction des produits (Exemple sur les premiers éléments trouvés)
products = driver.find_elements(By.CLASS_NAME, "product-tile") # À adapter selon le site

for product in products[:10]: # On teste sur les 10 premiers
    try:
        # Extraction brute SANS conversion de type (Consigne Arken)
        item = {
            "product_name": product.find_element(By.CLASS_NAME, "product-name").text,
            "brand": product.find_element(By.CLASS_NAME, "brand-name").text,
            "price": product.find_element(By.CLASS_NAME, "price-sales-standard").text, # On garde le "€"
            "source_url": driver.current_url,
            "availability": "En stock" # Valeur par défaut pour le test
        }
        data_list.append(item)
    except:
        continue

# 5. Sauvegarde en CSV
df = pd.DataFrame(data_list)
df.to_csv("donnees_brutes.csv", index=False, encoding='utf-8')

print("Scraping terminé ! Fichier donnees_brutes.csv créé.")
driver.quit()