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

# ── CONFIG ────────────────────────────────────────────────────────────────────

BASE_URL = "https://www.sephora.fr"

# Pages listing L'Oréal Paris make-up par catégorie
LISTING_PAGES = [
    {
        "url": BASE_URL + "/marques/loreal-paris/maquillage/teint/fonds-de-teint/",
        "category": "fond de teint",
    },
    {
        "url": BASE_URL + "/marques/loreal-paris/maquillage/teint/anti-cernes-et-correcteurs/",
        "category": "correcteur",
    },
    {
        "url": BASE_URL + "/marques/loreal-paris/maquillage/levres/",
        "category": "lèvres",
    },
    {
        "url": BASE_URL + "/marques/loreal-paris/maquillage/yeux/",
        "category": "yeux",
    },
    {
        "url": BASE_URL + "/marques/loreal-paris/maquillage/teint/blush-et-bronzers/",
        "category": "blush & bronzer",
    },
]

# Colonnes CSV — mêmes que Fenty et NARS
CSV_FIELDS = [
    "product_name", "brand", "category", "price", "promo_price",
    "volume_ml", "rating", "review_count", "shade_count",
    "finish_type", "coverage_level", "skin_type",
    "availability", "source_url",
]


# ── FONCTIONS UTILITAIRES ─────────────────────────────────────────────────────

def init_driver():
    """Initialise Chrome en mode normal (non-headless pour éviter le blocage)."""
    print("Lancement de Chrome...")
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    # Masquer la signature WebDriver
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    print("Chrome prêt.\n")
    return driver


def pause(a=2, b=5):
    """Pause aléatoire entre les requêtes."""
    time.sleep(random.uniform(a, b))


def scroll_page(driver, scrolls=8, delay=0.6):
    """Scrolle progressivement pour déclencher le lazy-loading."""
    for _ in range(scrolls):
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(delay)
    time.sleep(1.5)


def accept_cookies(driver):
    """Ferme la bannière cookies si présente."""
    try:
        btn = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "#onetrust-accept-btn-handler, "
                 "button[id*='accept'], "
                 "button[class*='accept']")
            )
        )
        btn.click()
        time.sleep(1)
        print("  Cookies acceptés.")
    except Exception:
        pass


def click_load_more(driver, max_clicks=15):
    """Clique sur 'Voir plus' jusqu'à disparition du bouton."""
    clicks = 0
    while clicks < max_clicks:
        try:
            btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     "button[class*='load-more'], "
                     "button[data-at*='load_more'], "
                     "a[class*='see-more']")
                )
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            btn.click()
            clicks += 1
            print(f"    → Chargement page +{clicks}...")
            scroll_page(driver, scrolls=4, delay=0.5)
        except Exception:
            break
    return clicks


# ── ÉTAPE 1 : RÉCUPÉRER LES LIENS PRODUITS ───────────────────────────────────

def get_product_links(driver, page_info, first_page=False):
    """
    Charge une page listing Séphora et récupère les URLs produit.
    Gère le lazy-loading et le bouton 'Voir plus'.
    """
    url = page_info["url"]
    category = page_info["category"]

    print(f"\nListing : {category}")
    print(f"  URL : {url}")
    driver.get(url)
    time.sleep(4)

    if first_page:
        accept_cookies(driver)

    # Scroll initial pour déclencher le chargement
    scroll_page(driver, scrolls=6)

    # Charger tous les produits disponibles
    more = click_load_more(driver, max_clicks=20)
    if more:
        print(f"  {more} clic(s) 'Voir plus' effectués.")
        scroll_page(driver, scrolls=4)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = []
    seen = set()

    # Sélecteurs produit Séphora.fr (plusieurs variantes selon déploiement)
    selectors = [
        "a[data-at='product_name']",
        "a[class*='product-item-link']",
        "a[class*='ProductCard']",
        "div[class*='product-card'] a[href*='/p/']",
        "article a[href*='/p/']",
    ]

    links_found = []
    for sel in selectors:
        links_found = soup.select(sel)
        if links_found:
            break

    # Fallback : toute balise <a> pointant vers une fiche produit Séphora
    if not links_found:
        links_found = [
            a for a in soup.find_all("a", href=True)
            if re.search(r"/p/[a-z0-9\-]+-P\d+\.html", a.get("href", ""))
        ]

    for a in links_found:
        href = a.get("href", "")
        if not href:
            continue
        if href.startswith("/"):
            full_url = BASE_URL + href
        elif href.startswith("http"):
            full_url = href
        else:
            continue

        # Nettoyer les paramètres d'URL
        full_url = re.sub(r"\?.*", "", full_url)

        if full_url in seen:
            continue
        seen.add(full_url)
        products.append({"url": full_url, "category": category})

    print(f"  {len(products)} produit(s) trouvé(s).")
    return products


# ── ÉTAPE 2 : SCRAPER UNE PAGE PRODUIT ───────────────────────────────────────

def scrape_product(driver, info):
    """
    Scrape les données d'une fiche produit Séphora.
    Extrait toutes les métriques au format standard (identique Fenty/NARS).
    """
    url = info["url"]
    category = info["category"]
    slug = url.split("/p/")[-1][:50] if "/p/" in url else url[-40:]

    print(f"  Scraping : {slug}")

    driver.get(url)
    time.sleep(3)

    # Scroll pour déclencher le chargement des avis
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(0.8)

    # Attendre les avis (Bazaarvoice ou Séphora natif)
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "[class*='rating'], [class*='review'], "
                 "[class*='stars'], [data-at='reviews_count']")
            )
        )
        time.sleep(0.8)
    except Exception:
        pass

    soup = BeautifulSoup(driver.page_source, "html.parser")
    text = soup.get_text(" ", strip=True)
    text_lower = text.lower()

    # ── NOM ──────────────────────────────────────────────────────────────────
    name = ""

    # Priorité 1 : JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                if data.get("@type") in ["Product", "BreadcrumbList"]:
                    if data.get("@type") == "Product":
                        name = data.get("name", "")
                    elif data.get("@type") == "BreadcrumbList":
                        items = data.get("itemListElement", [])
                        if items:
                            name = items[-1].get("item", {}).get("name", "")
        except Exception:
            pass
        if name:
            break

    # Priorité 2 : balises HTML
    if not name:
        for sel in ["h1[data-at='product_name']", "h1[class*='product-name']",
                    "h1[class*='ProductName']", "h1"]:
            tag = soup.select_one(sel)
            if tag:
                name = tag.get_text(strip=True)
                break

    # Priorité 3 : meta og:title
    if not name:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            name = re.sub(r"\s*[-|].*", "", og["content"]).strip()

    # ── MARQUE ────────────────────────────────────────────────────────────────
    brand = "L'Oréal Paris"
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict) and data.get("@type") == "Product":
                b = data.get("brand", {})
                if isinstance(b, dict):
                    brand = b.get("name", brand)
                elif isinstance(b, str):
                    brand = b
        except Exception:
            pass

    # ── CATÉGORIE (breadcrumb) ────────────────────────────────────────────────
    cat_scraped = category  # fallback avec la catégorie de listing
    bc_items = soup.select("ol[class*='breadcrumb'] li, nav[aria-label*='breadcrumb'] li")
    if bc_items and len(bc_items) >= 2:
        cat_scraped = bc_items[-2].get_text(strip=True) or category

    # ── PRIX ──────────────────────────────────────────────────────────────────
    price = ""
    promo_price = ""

    # JSON-LD price
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict) and data.get("@type") == "Product":
                offers = data.get("offers", {})
                if isinstance(offers, dict):
                    p = offers.get("price", "") or offers.get("lowPrice", "")
                    if p:
                        price = str(p)
                elif isinstance(offers, list) and offers:
                    price = str(offers[0].get("price", ""))
        except Exception:
            pass
        if price:
            break

    # Fallback HTML
    if not price:
        zone = soup.select_one("[class*='product-price'], [class*='Price'], "
                               "[data-at='price'], [class*='price-box']")
        zone_text = zone.get_text(" ", strip=True) if zone else text[:1000]
        prices_found = re.findall(r"(\d+[.,]\d{2})\s*€", zone_text)
        prices_float = sorted(set(
            float(p.replace(",", ".")) for p in prices_found
            if 1 < float(p.replace(",", ".")) < 500
        ), reverse=True)
        if len(prices_float) >= 2:
            price = str(prices_float[0])
            promo_price = str(prices_float[-1])
        elif len(prices_float) == 1:
            price = str(prices_float[0])

    # ── VOLUME ────────────────────────────────────────────────────────────────
    volume = ""
    vol_zone = soup.select_one("[class*='product-format'], [class*='size'], "
                               "[data-at='product_format']")
    vol_text = vol_zone.get_text(" ", strip=True) if vol_zone else name + " " + text[:300]
    v = re.search(r"(\d+(?:[.,]\d+)?)\s*ml", vol_text, re.IGNORECASE)
    if v:
        volume = v.group(1).replace(",", ".")
    else:
        g = re.search(r"(\d+(?:[.,]\d+)?)\s*g(?:\b)", vol_text)
        if g:
            volume = g.group(1).replace(",", ".")

    # ── DISPONIBILITÉ ─────────────────────────────────────────────────────────
    availability = "En stock"
    out_signals = ["rupture", "out of stock", "indisponible", "sold out"]
    if any(s in text_lower[:2000] for s in out_signals):
        availability = "Rupture"
    add_btn = soup.select_one("button[data-at='btn_add_to_basket'], "
                              "button[class*='add-to-cart']")
    if add_btn and add_btn.get("disabled"):
        availability = "Rupture"

    # ── NOTE (rating) ─────────────────────────────────────────────────────────
    rating = ""

    # JSON-LD aggregateRating
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict) and data.get("@type") == "Product":
                ar = data.get("aggregateRating", {})
                if ar:
                    rv = ar.get("ratingValue") or ar.get("bestRating")
                    if rv:
                        rating = str(rv)
        except Exception:
            pass
        if rating:
            break

    # Fallback HTML (aria-label="4.5 étoiles sur 5")
    if not rating:
        for sel in ["[aria-label*='toile'], [class*='rating-value'], "
                    "[data-at='rating_value']"]:
            tag = soup.select_one(sel)
            if tag:
                m = re.search(r"(\d+[.,]\d+)", tag.get("aria-label", "") + tag.get_text())
                if m:
                    rating = m.group(1).replace(",", ".")
                    break

    # ── NOMBRE D'AVIS ─────────────────────────────────────────────────────────
    reviews = ""

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict) and data.get("@type") == "Product":
                ar = data.get("aggregateRating", {})
                if ar:
                    rc = ar.get("reviewCount") or ar.get("ratingCount")
                    if rc:
                        reviews = str(rc)
        except Exception:
            pass
        if reviews:
            break

    if not reviews:
        for sel in ["[data-at='reviews_count'], [class*='review-count'], "
                    "[class*='reviews-nb']"]:
            tag = soup.select_one(sel)
            if tag:
                m = re.search(r"(\d+)", tag.get_text())
                if m:
                    reviews = m.group(1)
                    break

    if not reviews:
        m = re.search(r"(\d+)\s*avis", text_lower)
        if m:
            reviews = m.group(1)

    # ── NOMBRE DE TEINTES ─────────────────────────────────────────────────────
    shade_count = ""
    shade_btns = soup.select(
        "[data-at='color_swatch'], [class*='shade-swatch'], "
        "[class*='color-option'], button[aria-label*='teinte'], "
        "[class*='Swatch']"
    )
    if len(shade_btns) > 1:
        shade_count = str(len(shade_btns))
    else:
        m = re.search(r"(\d+)\s*teinte", text_lower)
        if m:
            shade_count = m.group(1)

    # ── FINI / FINISH ─────────────────────────────────────────────────────────
    finish = ""
    fini_map = {
        "mat": "mat", "matte": "mat", "satiné": "satiné", "satin": "satiné",
        "lumineux": "lumineux", "radieux": "lumineux", "glow": "lumineux",
        "naturel": "naturel", "transparent": "transparent",
    }
    for kw, val in fini_map.items():
        if kw in text_lower[:1500]:
            finish = val
            break

    # ── COUVRANCE ─────────────────────────────────────────────────────────────
    coverage = ""
    cov_map = {
        "couvrance totale": "totale", "couvrance complète": "totale",
        "couvrance forte": "totale",
        "couvrance moyenne": "moyenne", "couvrance modulable": "modulable",
        "couvrance légère": "légère", "couvrance naturelle": "légère",
        "bonne couvrance": "forte",
    }
    for kw, val in cov_map.items():
        if kw in text_lower[:2000]:
            coverage = val
            break

    # ── TYPE DE PEAU ─────────────────────────────────────────────────────────
    skin_types = []
    if any(x in text_lower for x in ["peau grasse", "anti-brillance", "contrôle du sébum"]):
        skin_types.append("grasse")
    if any(x in text_lower for x in ["peau sèche", "hydratant", "nourri"]):
        skin_types.append("sèche")
    if "mixte" in text_lower:
        skin_types.append("mixte")
    if any(x in text_lower for x in ["tous types", "tous les types", "peau normale"]):
        skin_types.append("tous types")
    if "sensible" in text_lower:
        skin_types.append("sensible")

    return {
        "product_name":   name,
        "brand":          brand,
        "category":       cat_scraped,
        "price":          price,
        "promo_price":    promo_price,
        "volume_ml":      volume,
        "rating":         rating,
        "review_count":   reviews,
        "shade_count":    shade_count,
        "finish_type":    finish,
        "coverage_level": coverage,
        "skin_type":      " / ".join(skin_types) if skin_types else "",
        "availability":   availability,
        "source_url":     url,
    }


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Scraper Séphora.fr — L'Oréal Paris Make-up")
    print("=" * 60)

    driver = init_driver()

    try:
        all_products = []
        seen_urls = set()

        # Étape 1 : collecter tous les liens produit
        for i, page in enumerate(LISTING_PAGES):
            links = get_product_links(driver, page, first_page=(i == 0))
            for p in links:
                if p["url"] not in seen_urls:
                    seen_urls.add(p["url"])
                    all_products.append(p)
            pause(2, 4)

        print(f"\nTotal : {len(all_products)} produits à scraper\n")
        if not all_products:
            print("Aucun produit trouvé. Vérifiez les URLs de listing.")
            return

        # Étape 2 : scraper chaque fiche produit
        results = []
        for i, p in enumerate(all_products):
            print(f"[{i+1}/{len(all_products)}]", end=" ")
            try:
                data = scrape_product(driver, p)
                if data and data["product_name"]:
                    results.append(data)
                    print(f"  ✓ {data['product_name'][:50]} "
                          f"— {data['price']}€ "
                          f"— {data['rating'] or '—'}/5 "
                          f"({data['review_count'] or '0'} avis)")
                else:
                    print("  ✗ Données insuffisantes — ignoré")
            except Exception as e:
                print(f"  ✗ Erreur : {e}")
            pause(2, 5)

        # Étape 3 : export CSV
        csv_file = "sephora_loreal_makeup.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(results)

        # Résumé par catégorie
        cats = {}
        for r in results:
            c = r["category"]
            cats[c] = cats.get(c, 0) + 1

        print(f"\n{'=' * 60}")
        print(f"  {len(results)} produits sauvegardés → {csv_file}")
        for cat, nb in sorted(cats.items()):
            print(f"    {cat} : {nb} produit(s)")
        print("=" * 60)

    finally:
        driver.quit()
        print("Chrome fermé.")


if __name__ == "__main__":
    main()

