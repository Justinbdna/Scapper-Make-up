# Data Monitor — Benchmark Concurrentiel : NARS Cosmetics 💄

## 📌 Présentation du Projet
Ce projet a été réalisé dans le cadre du module **Tableurs & Datavisualisation de données (DIA1)** à HETIC. 
L'objectif est de fournir une analyse stratégique à 360° du positionnement de la marque **NARS Cosmetics** face à trois concurrents majeurs du marché des fonds de teint : **Fenty Beauty**, **MAKE UP FOR EVER** et **L'Oréal Paris**.

À partir d'un échantillon final consolidé de **181 produits collectés en temps réel**, nous avons construit un pipeline de données complet pour transformer la data brute en insights business actionnables.

---

## 🛠️ Stack Technique
* **Collecte (Scraping) :** Python 3.x / `BeautifulSoup4` / `Requests`
* **Nettoyage & Traitement (ETL) :** Power Query (Normalisation des types, gestion des séparateurs régionaux).
* **Modélisation & Datavisualisation :** Power BI Desktop (Mesures DAX, filtres croisés, mise en forme conditionnelle).

---

## 📂 Structure du Dépôt
```text
.
├── MASTER_MAKEUP_FINAL.csv          # Base de données finale consolidée (181 produits)
├── MCD.pdf                          # Modèle Conceptuel de Données du projet
├── README.md                        # Documentation complète
├── data_makeup.py                   # Script Python de fusion et centralisation des données
├── data_monitor_dashboard-Groupe09.pbix # Fichier de modélisation Power BI
├── data_monitor_dashboard-Groupe09.pdf  # Export visuel du Dashboard
├── data_monitor_rapport_Groupe09.pdf    # Rapport stratégique écrit (4-6 pages)
├── date_monitor_slides_Groupe09.pdf     # Support de présentation de la soutenance
├── fenty_scraper.py                 # Script de scraping pour Fenty Beauty
├── fenty_teint.csv                  # Données d'extraction brutes Fenty
├── makeupforever_teint.csv          # Données d'extraction brutes MAKE UP FOR EVER
├── nars_cosmetics.csv               # Données d'extraction brutes NARS
├── scraper_makeupforever.py         # Script de scraping pour MAKE UP FOR EVER
├── scraper_nars.py                  # Script de scraping pour NARS
├── scraper_sephora_loreal.py        # Script de scraping pour L'Oréal Paris
└── sephora_loreal_makeup.csv        # Données d'extraction brutes L'Oréal Paris
