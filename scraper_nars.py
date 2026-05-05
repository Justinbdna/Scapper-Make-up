from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup
import json
import time
import random
import csv
import re


# ----- CONFIG -----

BASE_URL = "https://www.narscosmetics.fr"

LISTING_PAGES = [
    {
        "url": BASE_URL + "/fr/teint/fond-de-teint",
        "category": "fond de teint",
        "positive": ["foundation", "tinted"],
    },
    {
        "url": BASE_URL + "/fr/maquillage/teint/concealers",
        "category": "correcteur",
        "positive": ["concealer", "brightener", "corrector"],
    },
]

# Mots dans l'URL qui excluent un produit (accessoires etc.)
NEGATIVE_KEYWORDS = [
    "pump", "pompe", "brush", "pinceau",
    "bundle", "duo", "coffret",
    "lip", "balm",
]

CSV_FIELDS = [
    "product_name", "brand", "category", "price", "promo_price",
    "volume_ml", "rating", "review_count", "shade_count",
    "finish_type", "coverage_level", "skin_type",
    "availability", "source_url",
]


# ----- FONCTIONS UTILES -----

def init_driver():
    """Lance le navigateur Chrome."""
    print("Lancement de Chrome...")

    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )

    print("Chrome pret\n")
    return driver


def pause(a=2, b=4):
    """Pause aleatoire entre les requetes."""
    time.sleep(random.uniform(a, b))


# ----- ETAPE 1 : RECUPERER LES LIENS DEPUIS LE LISTING -----

def get_product_links(driver, page_info):
    """
    Charge une page listing et recupere les liens
    vers les pages produit en filtrant par URL.
    """
    url = page_info["url"]
    category = page_info["category"]
    positives = page_info["positive"]

    print(f"Chargement listing : {category}")
    driver.get(url)
    time.sleep(5)

    # Scroll pour charger les produits
    for _ in range(10):
        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(0.4)
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    products = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if not href.endswith(".html"):
            continue

        # URL complete
        if href.startswith("/"):
            full_url = BASE_URL + href
        elif href.startswith("http"):
            full_url = href
        else:
            continue

        full_url = re.sub(r"\?.*", "", full_url)
        url_lower = full_url.lower()

        # L'URL doit contenir un mot-cle de la categorie
        if not any(kw in url_lower for kw in positives):
            continue

        # L'URL ne doit pas contenir un mot-cle d'accessoire
        if any(kw in url_lower for kw in NEGATIVE_KEYWORDS):
            continue

        # Deduplication par code article
        article = re.search(r"/(999\w+|0\d{9,})\.html", full_url)
        key = article.group(1) if article else full_url

        if key in seen:
            continue
        seen.add(key)

        products.append({
            "url": full_url,
            "category": category,
        })

    print(f"  {len(products)} produits trouves\n")
    return products


# ----- ETAPE 2 : SCRAPER UNE PAGE PRODUIT -----

def scrape_product(driver, info):
    """
    Charge la page produit avec Selenium,
    attend le chargement des avis Bazaarvoice,
    puis extrait toutes les donnees.
    """
    url = info["url"]
    category = info["category"]

    print(f"  Scraping : {url.split('/fr/')[-1][:50]}")

    driver.get(url)
    time.sleep(3)

    # Scroll pour declencher le chargement des avis
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(1)

    # Attendre que Bazaarvoice charge les avis (max 8 sec)
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".bv_avgRating_component_container, .bv_numReviews_text")
            )
        )
        time.sleep(1)
    except Exception:
        pass

    # Recuperer le HTML complet (avec le JS execute)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    text = soup.get_text(" ", strip=True)
    text_lower = text.lower()

    # --- NOM ---
    name = ""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get("@type") == "BreadcrumbList":
                items = data.get("itemListElement", [])
                if items:
                    name = items[-1].get("item", {}).get("name", "")
        except Exception:
            pass

    if not name:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            name = re.sub(r"\s*\|.*", "", og["content"]).strip()

    # --- PRIX + PROMO ---
    # On cherche tous les prix dans la zone produit
    # Le plus haut = prix original, le plus bas = prix promo
    product_info = soup.find(class_="product-info-content")
    if product_info:
        prices_text = product_info.get_text(" ", strip=True)
    else:
        prices_text = text[:2000]

    prices_found = re.findall(r"(\d+[.,]\d{2})\s*€", prices_text)
    prices_float = []
    for p in prices_found:
        try:
            prices_float.append(float(p.replace(",", ".")))
        except ValueError:
            pass

    # Supprimer les doublons
    prices_float = sorted(set(prices_float), reverse=True)

    price = ""
    promo_price = ""

    if len(prices_float) >= 2:
        # Le plus haut = prix original, le plus bas = promo
        price = str(prices_float[0])
        promo_price = str(prices_float[-1])
    elif len(prices_float) == 1:
        price = str(prices_float[0])
    else:
        # Fallback : meta og:price
        og_price = soup.find("meta", property="og:price:amount")
        if og_price and og_price.get("content"):
            price = og_price["content"]

    # --- VOLUME ---
    volume = ""
    volume_text = prices_text if product_info else text[:500]
    v = re.search(r"(\d+(?:[.,]\d+)?)\s*ml", volume_text)
    if v:
        volume = v.group(1).replace(",", ".")
    else:
        g = re.search(r"(\d+(?:[.,]\d+)?)\s*g(?:\s|$)", volume_text)
        if g:
            volume = g.group(1).replace(",", ".")

    # --- DISPONIBILITE ---
    availability = "en stock"
    og_avail = soup.find("meta", property="og:availability")
    if og_avail and og_avail.get("content"):
        if "out" in og_avail["content"].lower():
            availability = "rupture"

    # --- FINI ---
    finish = ""
    f = re.search(r"Fini\s+([A-ZÀ-Ÿ][a-zà-ÿ\s,]+?)(?:\s+Couvrance|\s{2,})", text)
    if f:
        finish = f.group(1).strip().rstrip(",")

    # --- COUVRANCE ---
    coverage = ""
    c = re.search(
        r"Couvrance\s+([A-ZÀ-Ÿ][a-zà-ÿ\s,à]+?)"
        r"(?:\s+Bénéfice|\s+Teinte|\s+Ajouter|\s+Livraison|\s{2,})",
        text,
    )
    if c:
        coverage = c.group(1).strip().rstrip(",")

    # --- NOMBRE DE TEINTES ---
    shade_count = ""
    t = re.search(r"Teintes\s*:\s*(\d+)", text)
    if t:
        shade_count = t.group(1)
    if not shade_count:
        shades = re.findall(r"[A-Z][a-zà-ÿ ]+\s+[LMD]\d", text)
        if len(shades) > 3:
            shade_count = str(len(set(shades)))

    # --- RATING (depuis Bazaarvoice) ---
    rating = ""
    bv_rating = soup.find("div", class_="bv_avgRating_component_container")
    if bv_rating:
        m = re.search(r"(\d+[.,]\d+)", bv_rating.get_text(strip=True))
        if m:
            rating = m.group(1).replace(",", ".")

    # --- NOMBRE D'AVIS (depuis Bazaarvoice) ---
    reviews = ""
    bv_reviews = soup.find("div", class_="bv_numReviews_text")
    if bv_reviews:
        m = re.search(r"(\d+)", bv_reviews.get_text(strip=True))
        if m:
            reviews = m.group(1)

    # --- TYPE DE PEAU ---
    skin_types = []
    if any(x in text_lower for x in ["peau grasse", "contrôle du sébum", "anti-brillance", "sans huile"]):
        skin_types.append("grasse")
    if any(x in text_lower for x in ["peau sèche", "hydratant", "hydrate"]):
        skin_types.append("sèche")
    if "mixte" in text_lower:
        skin_types.append("mixte")
    if any(x in text_lower for x in ["tous types", "tous les types"]):
        skin_types.append("tous types")
    if "sensible" in text_lower:
        skin_types.append("sensible")

    return {
        "product_name": name,
        "brand": "NARS",
        "category": category,
        "price": price,
        "promo_price": promo_price,
        "volume_ml": volume,
        "rating": rating,
        "review_count": reviews,
        "shade_count": shade_count,
        "finish_type": finish,
        "coverage_level": coverage,
        "skin_type": " / ".join(skin_types),
        "availability": availability,
        "source_url": url,
    }


# ----- MAIN -----

def main():
    print("Scraper NARS Cosmetics")
    print("Fond de teint + Anti-cernes\n")

    driver = init_driver()

    try:
        # Etape 1 : recuperer les liens depuis les pages listing
        all_products = []
        seen_urls = set()

        for page in LISTING_PAGES:
            links = get_product_links(driver, page)

            for p in links:
                if p["url"] not in seen_urls:
                    seen_urls.add(p["url"])
                    all_products.append(p)

            pause(2, 3)

        print(f"Total : {len(all_products)} produits a scraper\n")

        if not all_products:
            print("Aucun produit trouve.")
            return

        # Etape 2 : scraper chaque page produit
        results = []

        for i, p in enumerate(all_products):
            print(f"[{i+1}/{len(all_products)}]")

            data = scrape_product(driver, p)

            if data:
                results.append(data)
                print(f"    {data['product_name']} - {data['price']}E" f" - {data['rating']}/5 ({data['review_count']} avis)")

            pause(2, 4)

        # Etape 3 : export CSV
        csv_file = "nars_cosmetics.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(results)

        fdt = [r for r in results if r["category"] == "fond de teint"]
        cor = [r for r in results if r["category"] == "correcteur"]

        print(f"\n{len(results)} produits sauvegardes dans {csv_file}")
        print(f"  {len(fdt)} fonds de teint")
        print(f"  {len(cor)} correcteurs")

    finally:
        driver.quit()
        print("Chrome ferme")


if __name__ == "__main__":
    main()