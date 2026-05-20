# 💄 Data Monitor — Benchmark Concurrentiel NARS

Ce projet a été réalisé dans le cadre du module **Tableurs & Datavisualisation de données (DIA1)** à HETIC.

---

## 📌 En Bref

* **Objectif :** Analyser le positionnement stratégique des fonds de teint **NARS Cosmetics**.
* **Périmètre :** Étude comparative face à **Fenty Beauty**, **MAKE UP FOR EVER** et **L'Oréal Paris**.
* **Volume :** **181 produits** collectés et analysés en temps réel.

---

## 🛠️ Stack Technique

* **Extraction (Scraping) :** Python 3.x / `BeautifulSoup4` / `Requests`
* **Traitement (ETL) :** Power Query & `Pandas`
* **Datavisualisation :** Power BI Desktop (`Mesures DAX` & `Mises en forme conditionnelles`)

---

## 📂 Architecture du Dépôt

### 📄 Documents Principaux (Racine)
* `MCD.pdf` ➔ Modèle Conceptuel de Données de la base.
* `data_monitor_dashboard-Groupe09.pbix` ➔ Dashboard Power BI interactif.
* `data_monitor_dashboard-Groupe09.pdf` ➔ Export visuel du Dashboard.
* `data_monitor_rapport_Groupe09.pdf` ➔ Rapport stratégique écrit (4-6 pages).

### 📊 Données Extraites (`/data`)
* `MASTER_MAKEUP_ASSEMBLY.csv` ➔ Base finale consolidée (**181 lignes**).
* `nars_cosmetics.csv` | `fenty_teint.csv` | `makeupforever_teint.csv` | `sephora_loreal_makeup.csv` ➔ Données brutes par marque.

### ⚙️ Scripts de Scraping (`/scripts`)
* `data_makeup.py` ➔ Script de nettoyage et fusion.
* `scraper_nars.py` | `fenty_scraper.py` | `scraper_makeupforever.py` | `scraper_sephora_loreal.py` ➔ Robots d'extraction.

---

## 🚀 Installation & Utilisation

1. **Installer les dépendances :**
   ```bash
   pip3 install pandas requests beautifulsoup4 openpyxl

2. Lancer la fusion des données :
   ```Bash
   python3 scripts/data_makeup.py

📈 Insights Clés (Ce que disent les données)

💰 1. Le Positionnement Prix
Observation : NARS affiche le prix moyen le plus élevé du marché (48,00€), loin devant L'Oréal Paris (14,50€). L'analyse DAX au millilitre confirme ce maintien sur le segment Luxe.

🎨 2. Le Défi de l'Inclusivité
Observation : Fenty impose le standard avec 50 teintes, mais NARS résiste avec une moyenne solide de 34 teintes et une domination technique sur les finis Radiant et Satiné.

👁️ 3. Le Paradoxe de la Visibilité
Observation : NARS possède la meilleure note de satisfaction globale (4.6/5), mais le plus faible volume d'avis clients (504 en moyenne). Le produit est excellent mais manque d'exposition numérique.

🎯 Recommandations Stratégiques
Action 1 : Lancer des formats Mini (Travel Size) à ~20€ pour casser la barrière du prix chez les jeunes sans détruire l'image premium.
Action 2 : Investir massivement dans des campagnes de Micro-Influence (UGC) pour générer des avis et combler le déficit de visibilité.
Action 3 : Axer le marketing sur la Luminescence (Radiant) pour distancer les concurrents saturés par le fini mat.

👥 Membres de l'Équipe (Groupe 09) :

Justin BANDIOLA,
Quentin OUDIN,
Karen PROUST,
Douglas QUINTERO,
Juldonnis RAZAFIMANAZATO
