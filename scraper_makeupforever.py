"""
Scraper Make Up For Ever - fonds de teint & correcteurs / anti-cernes.

Pattern repris de :
  - scraper_sephora_loreal.py  (branche Quentin)
  - scraper_nars.py            (branche Karen)

Particularite MUF :
  Le site (Salesforce Commerce Cloud / Demandware) rend ses pages cote serveur.
  Pas besoin de Selenium - requests + BeautifulSoup suffisent.

Anti-bot :
  - User-Agent navigateur realiste
  - Headers Accept / Accept-Language / Referer
  - Delais conservateurs (5-10 s entre requetes) + jitter
  - Retry avec backoff sur erreurs HTTP / reseau

Sortie : makeupforever_teint.csv - memes colonnes que Fenty / NARS / Sephora.
"""

import csv
import json
import random
import re
import sys
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup


# ----- CONFIG ----------------------------------------------------------------

BASE_URL = "https://www.makeupforever.com"

LISTING_PAGES = [
    {
        "url": BASE_URL + "/fr/fr/teint/fonds-de-teint",
        "category": "fond de teint",
        "positive": [
            "fond-de-teint", "foundation", "skin-tint",
            "hd-skin", "matte-velvet", "reboot", "watertone",
            "ultra-hd",
        ],
    },
    {
        "url": BASE_URL + "/fr/fr/teint/correcteurs-anti-cernes",
        "category": "correcteur",
        "positive": [
            "concealer", "correcteur", "anti-cernes",
            "underpainting", "full-cover",
        ],
    },
]

# On exclut les accessoires / pinceaux / kits / palettes pures.
NEGATIVE_KEYWORDS = [
    "pinceau", "brush", "eponge", "sponge",
    "kits-maquillage", "/kits-", "+",
    "palettes-teint", "palettes-maquillage",
    "demaquillant", "fixateur",
]

CSV_FIELDS = [
    "product_name", "brand", "category", "price", "promo_price",
    "volume_ml", "rating", "review_count", "shade_count",
    "finish_type", "coverage_level", "skin_type",
    "availability", "source_url",
]

OUTPUT_CSV = "makeupforever_teint.csv"

# Delais conservateurs (en secondes)
DELAY_MIN_LISTING = 4
DELAY_MAX_LISTING = 7
DELAY_MIN_PRODUCT = 6
DELAY_MAX_PRODUCT = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Upgrade-Insecure-Requests": "1",
}


# ----- FONCTIONS UTILITAIRES -------------------------------------------------

def pause(a, b):
    """Pause aleatoire entre les requetes pour eviter les bans anti-bot."""
    time.sleep(random.uniform(a, b))


def fetch(url, session, max_retries=3):
    """
    Recupere le HTML d'une URL avec retries et backoff exponentiel.
    Retourne None si toutes les tentatives echouent.
    """
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code in (403, 429):
                wait = 15 * attempt
                print("    HTTP {} (anti-bot ?) - attente {}s".format(
                    resp.status_code, wait))
                time.sleep(wait)
            else:
                print("    HTTP {} - tentative {}/{}".format(
                    resp.status_code, attempt, max_retries))
                time.sleep(5 * attempt)
        except requests.RequestException as e:
            print("    Erreur reseau : {} - tentative {}/{}".format(
                e, attempt, max_retries))
            time.sleep(5 * attempt)
    return None


def is_relevant_product(url, positives):
    """Filtre les liens : doit contenir un mot-cle positif et aucun negatif."""
    url_lower = url.lower()
    if any(neg in url_lower for neg in NEGATIVE_KEYWORDS):
        return False
    if positives:
        if not any(pos in url_lower for pos in positives):
            # Tolerance : tout produit dont l'URL passe par /teint/
            if "/teint/" not in url_lower:
                return False
    return True


# ----- ETAPE 1 : RECUPERER LES LIENS PRODUITS --------------------------------

def get_product_links(html, page_info):
    """
    Parse une page listing MUF et extrait les URLs produit.
    Les fiches produit MUF ont des slugs finissant par
    `-MI000XXXXXX.html` ou `-I000XXXXXX.html`.
    """
    soup = BeautifulSoup(html, "html.parser")
    category = page_info["category"]
    positives = page_info["positive"]

    products = []
    seen = set()

    product_re = re.compile(r"-M?I\d{5,}\.html(?:\?|$)")

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue

        if href.startswith("/"):
            full_url = BASE_URL + href
        elif href.startswith("http"):
            full_url = href
        else:
            continue

        if "makeupforever.com/fr/fr/" not in full_url:
            continue

        if not product_re.search(full_url):
            continue

        full_url = re.sub(r"\?.*", "", full_url)

        if full_url in seen:
            continue

        if not is_relevant_product(full_url, positives):
            continue

        seen.add(full_url)
        products.append({"url": full_url, "category": category})

    return products


# ----- ETAPE 2 : SCRAPER UNE FICHE PRODUIT -----------------------------------

def _extract_json_ld(soup):
    """Recupere tous les blocs JSON-LD (Product, BreadcrumbList, etc.)."""
    blocks = []
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            blocks.extend(d for d in data if isinstance(d, dict))
        elif isinstance(data, dict):
            blocks.append(data)
    return blocks


def scrape_product(html, info):
    """Extrait toutes les metriques d'une fiche produit MUF."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    text_lower = text.lower()
    url = info["url"]
    category = info["category"]

    json_ld = _extract_json_ld(soup)
    product_jsonld = next(
        (b for b in json_ld if b.get("@type") == "Product"), {}
    )

    # ----- NOM ---------------------------------------------------------------
    name = ""
    if product_jsonld:
        name = (product_jsonld.get("name") or "").strip()

    if not name:
        h1 = soup.find("h1")
        if h1:
            name = h1.get_text(" ", strip=True)

    if not name:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            name = re.sub(r"\s*[-|].*", "", og["content"]).strip()

    name = re.sub(r"\s+", " ", name).strip()

    # ----- MARQUE ------------------------------------------------------------
    brand = "MAKE UP FOR EVER"
    if product_jsonld:
        b = product_jsonld.get("brand")
        if isinstance(b, dict):
            brand = b.get("name", brand) or brand
        elif isinstance(b, str) and b:
            brand = b

    # ----- CATEGORIE (breadcrumb) --------------------------------------------
    cat_scraped = category
    bc_jsonld = next(
        (b for b in json_ld if b.get("@type") == "BreadcrumbList"), None
    )
    if bc_jsonld:
        items = bc_jsonld.get("itemListElement", [])
        if items and len(items) >= 2:
            it = items[-2].get("item", {})
            if isinstance(it, dict):
                cat_name = (it.get("name") or "").strip()
                if cat_name:
                    cat_scraped = cat_name.lower()

    if cat_scraped == category:
        bc_links = soup.select(
            "ol.breadcrumb a, nav.breadcrumb a, "
            ".breadcrumb a, ol[class*='breadcrumb'] a"
        )
        if bc_links and len(bc_links) >= 2:
            cat_scraped = bc_links[-1].get_text(strip=True).lower() or category

    # ----- PRIX --------------------------------------------------------------
    price = ""
    promo_price = ""

    if product_jsonld:
        offers = product_jsonld.get("offers", {})
        if isinstance(offers, dict):
            p = offers.get("price") or offers.get("lowPrice")
            if p:
                price = str(p)
        elif isinstance(offers, list) and offers:
            p = offers[0].get("price")
            if p:
                price = str(p)

    # Detection promo : on cherche tous les prix dans la zone .price.
    price_zone = soup.select_one(
        ".price, .product-price, [class*='price-wrapper'], "
        "[class*='product-tile-price']"
    )
    zone_text = price_zone.get_text(" ", strip=True) if price_zone else text[:2000]
    prices_found = re.findall(r"(\d+(?:[.,]\d{1,2})?)\s*€", zone_text)
    prices_float = sorted({
        float(p.replace(",", "."))
        for p in prices_found
        if 1 < float(p.replace(",", ".")) < 500
    }, reverse=True)

    if len(prices_float) >= 2:
        price = str(prices_float[0])
        promo_price = str(prices_float[-1])
    elif len(prices_float) == 1 and not price:
        price = str(prices_float[0])

    # ----- VOLUME ------------------------------------------------------------
    volume = ""
    vol_text = "{} {}".format(name, text[:1500])
    v = re.search(r"(\d+(?:[.,]\d+)?)\s*ml\b", vol_text, re.IGNORECASE)
    if v:
        volume = v.group(1).replace(",", ".")
    else:
        g = re.search(r"(\d+(?:[.,]\d+)?)\s*g\b", vol_text)
        if g:
            volume = g.group(1).replace(",", ".")

    # ----- DISPONIBILITE ----------------------------------------------------
    availability = "En stock"

    if product_jsonld:
        offers = product_jsonld.get("offers", {})
        if isinstance(offers, dict):
            av = (offers.get("availability") or "").lower()
            if "outofstock" in av or "sold" in av:
                availability = "Rupture"

    out_signals = [
        "ce produit n'est plus disponible",
        "m'informer du retour en stock",
        "rupture de stock",
        "indisponible",
    ]
    if availability == "En stock" and any(s in text_lower for s in out_signals):
        add_btn = soup.find(string=re.compile(r"\bAjouter\b", re.IGNORECASE))
        if not add_btn:
            availability = "Rupture"

    # ----- NOTE (rating) - Bazaarvoice --------------------------------------
    rating = ""
    if product_jsonld:
        ar = product_jsonld.get("aggregateRating", {})
        if isinstance(ar, dict):
            rv = ar.get("ratingValue") or ar.get("bestRating")
            if rv:
                rating = str(rv)

    if not rating:
        m = re.search(r"(\d[.,]\d)\s*(?:sur|/)\s*5", text)
        if m:
            rating = m.group(1).replace(",", ".")

    # ----- NOMBRE D'AVIS ----------------------------------------------------
    reviews = ""
    if product_jsonld:
        ar = product_jsonld.get("aggregateRating", {})
        if isinstance(ar, dict):
            rc = ar.get("reviewCount") or ar.get("ratingCount")
            if rc:
                reviews = str(rc)

    if not reviews:
        m = re.search(r"(\d+)\s*(?:avis|reviews?|commentaires?)", text_lower)
        if m:
            reviews = m.group(1)

    # ----- NOMBRE DE TEINTES ------------------------------------------------
    shade_count = ""
    m = re.search(r"(\d+)\s*teinte", text_lower)
    if m:
        shade_count = m.group(1)
    else:
        swatches = soup.select(
            "[class*='swatch']:not([class*='size']), "
            "[data-attr*='color'] button, "
            "ul[class*='color'] li"
        )
        if 1 < len(swatches) < 100:
            shade_count = str(len(swatches))

    # ----- FINI / FINISH ----------------------------------------------------
    finish = ""
    finish_map = [
        ("semi-mat",   "satine"),
        ("semi mat",   "satine"),
        ("matifiant",  "mat"),
        ("fini mat",   "mat"),
        ("matte",      "mat"),
        (" mat ",      "mat"),
        ("satine",     "satine"),
        ("satin",      "satine"),
        ("irise",      "irise"),
        ("lumineux",   "lumineux"),
        ("radieux",    "lumineux"),
        ("glow",       "lumineux"),
        ("eclat",      "lumineux"),
        ("naturel",    "naturel"),
    ]
    haystack = text_lower[:3000]
    for kw, val in finish_map:
        if kw in haystack:
            finish = val
            break

    # ----- COUVRANCE --------------------------------------------------------
    coverage = ""
    cov_map = [
        ("couvrance totale",   "totale"),
        ("couvrance complete", "totale"),
        ("haute couvrance",    "totale"),
        ("couvrance haute",    "totale"),
        ("moyenne a haute",    "moyenne a haute"),
        ("moyenne à haute",    "moyenne a haute"),
        ("couvrance moyenne",  "moyenne"),
        ("couvrance modulable", "modulable"),
        ("couvrance legere",   "legere"),
        ("couvrance naturelle", "legere"),
    ]
    for kw, val in cov_map:
        if kw in haystack:
            coverage = val
            break

    # ----- TYPE DE PEAU -----------------------------------------------------
    # On gere a la fois "peau grasse" isole ET "peaux normales, mixtes et grasses".
    skin_types = []
    enum_zone = text_lower  # cherche dans tout le texte

    def has_enum(word):
        # match "peau(x) ... <word>" sans point entre les deux (<=120 chars)
        return bool(re.search(
            r"\b(?:peau|peaux)[^.]{0,120}\b" + word, enum_zone
        ))

    if has_enum("grasse") or any(x in enum_zone for x in [
            "anti-brillance", "matifiant", "controle du sebum",
            "et grasses", "et grasse"]):
        skin_types.append("grasse")
    if has_enum("seche") or has_enum("sèche") or any(x in enum_zone for x in [
            "hydratant", "deshydrate", "et seches", "et sèches"]):
        skin_types.append("seche")
    if has_enum("mixte") or "et mixtes" in enum_zone or "et mixte" in enum_zone:
        skin_types.append("mixte")
    if has_enum("normale") or "et normales" in enum_zone:
        skin_types.append("normale")
    if "sensible" in enum_zone:
        skin_types.append("sensible")
    if "mature" in enum_zone:
        skin_types.append("mature")
    if any(x in enum_zone for x in ["tous types", "tous les types"]):
        skin_types.append("tous types")

    # Deduplication en preservant l'ordre
    seen_skin = []
    for st in skin_types:
        if st not in seen_skin:
            seen_skin.append(st)

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
        "skin_type":      " / ".join(seen_skin),
        "availability":   availability,
        "source_url":     url,
    }


# ----- MAIN ------------------------------------------------------------------

def main(limit=None):
    print("=" * 60)
    print("  Scraper makeupforever.com - Fonds de teint & Correcteurs")
    print("=" * 60)

    session = requests.Session()

    print("\nPre-chargement de la home (cookies)...")
    home_html = fetch(BASE_URL + "/fr/fr", session)
    if not home_html:
        print("Impossible de joindre la home - abandon.")
        sys.exit(1)
    pause(3, 5)

    # ----- ETAPE 1 : collecte des liens produit -----------------------------
    all_products = []
    seen_urls = set()

    for page in LISTING_PAGES:
        print("\nListing : {}".format(page["category"]))
        print("  URL : {}".format(page["url"]))
        html = fetch(page["url"], session)
        if not html:
            print("  Echec du chargement - page sautee.")
            continue

        links = get_product_links(html, page)
        for p in links:
            if p["url"] not in seen_urls:
                seen_urls.add(p["url"])
                all_products.append(p)

        print("  {} produit(s) candidat(s) trouve(s).".format(len(links)))
        pause(DELAY_MIN_LISTING, DELAY_MAX_LISTING)

    print("\nTotal : {} produits a scraper".format(len(all_products)))

    if not all_products:
        print("Aucun produit trouve. Verifie les URLs de listing.")
        return

    if limit:
        print("(Mode test : limite a {} produits)".format(limit))
        all_products = all_products[:limit]

    # ----- ETAPE 2 : scrape de chaque fiche ---------------------------------
    results = []
    for i, p in enumerate(all_products, 1):
        slug = p["url"].split("/")[-1][:60]
        print("\n[{}/{}] {}".format(i, len(all_products), slug))

        html = fetch(p["url"], session)
        if not html:
            print("  Echec - produit saute.")
            pause(DELAY_MIN_PRODUCT, DELAY_MAX_PRODUCT)
            continue

        try:
            data = scrape_product(html, p)
        except Exception as e:
            print("  Erreur de parsing : {}".format(e))
            pause(DELAY_MIN_PRODUCT, DELAY_MAX_PRODUCT)
            continue

        if data and data["product_name"]:
            results.append(data)
            print("  OK  {} | {} EUR | {}/5 ({} avis) | {} teintes".format(
                data["product_name"][:60],
                data["price"] or "-",
                data["rating"] or "-",
                data["review_count"] or "0",
                data["shade_count"] or "0",
            ))
        else:
            print("  Donnees insuffisantes - ignore")

        pause(DELAY_MIN_PRODUCT, DELAY_MAX_PRODUCT)

    # ----- ETAPE 3 : export CSV ---------------------------------------------
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    by_cat = {}
    for r in results:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1

    print("\n" + "=" * 60)
    print("  {} produits sauvegardes -> {}".format(len(results), OUTPUT_CSV))
    for cat, nb in sorted(by_cat.items()):
        print("    {} : {} produit(s)".format(cat, nb))
    print("=" * 60)


if __name__ == "__main__":
    limit_arg = None
    if len(sys.argv) > 1 and sys.argv[1] == "--limit" and len(sys.argv) > 2:
        try:
            limit_arg = int(sys.argv[2])
        except ValueError:
            pass

    main(limit=limit_arg)
