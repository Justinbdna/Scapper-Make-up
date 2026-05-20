# Data Monitor — Benchmark Concurrentiel : NARS Cosmetics 💄

## 📌 Présentation du Projet
Dans un marché des cosmétiques ultra-compétitif et en constante évolution sur les réseaux sociaux, le projet **Data Monitor** propose une analyse stratégique à 360° du positionnement de **NARS Cosmetics**. L'objectif principal est d'évaluer la compétitivité de ses gammes de fonds de teint face à trois acteurs majeurs du secteur : **Fenty Beauty**, **MAKE UP FOR EVER** et **L'Oréal Paris**.

À partir d'un échantillon global de **181 produits collectés en temps réel**, notre équipe a mis en place un pipeline de données complet (ETL). Ce processus va de l'extraction automatisée des données publiques jusqu'à la modélisation d'insights business actionnables, visant à résoudre un double défi : optimiser les volumes de ventes de NARS tout en préservant son positionnement de marque "Prestige".

---

## 🛠️ Stack Technique & Pipeline de Données
Le projet s'articule autour d'une architecture de données moderne et rigoureuse, divisée en trois grandes étapes :

1. **Collecte (Scraping) :** Extraction ciblée des catalogues et des métriques utilisateurs via des scripts Python s'appuyant sur les bibliothèques `BeautifulSoup4` et `Requests`.
2. **Traitement & Nettoyage (ETL) :** Centralisation des données brutes, normalisation des types (gestion des séparateurs régionaux, conversion des devises) et traitement des valeurs manquantes au sein de **Power Query**.
3. **Modélisation & Datavisualisation :** Création d'indicateurs personnalisés en **DAX** (calcul du prix au millilitre) et conception d'un tableau de bord interactif sur **Power BI Desktop** intégrant des filtres croisés et des segmentations dynamiques.

---

## 📂 Architecture du Dépôt
Le projet est structuré de manière claire afin de séparer la logique d'extraction, les datasets de stockage et les rapports d'analyse finaux :

```text
.
├── MCD.pdf                          # Modèle Conceptuel de Données de la base
├── README.md                        # Documentation principale du projet
├── data_monitor_dashboard-Groupe09.pbix # Fichier de modélisation Power BI principal
├── data_monitor_dashboard-Groupe09.pdf  # Export visuel complet du tableau de bord
├── data_monitor_rapport_Groupe09.pdf    # Rapport stratégique écrit (4-6 pages)
├── data/                            # Répertoire des données d'extraction (CSV)
│   ├── MASTER_MAKEUP_ASSEMBLY.csv   # Base de données finale consolidée (181 produits)
│   ├── fenty_teint.csv              # Données brutes : Fenty Beauty
│   ├── makeupforever_teint.csv      # Données brutes : MAKE UP FOR EVER
│   ├── nars_cosmetics.csv           # Données brutes : NARS Cosmetics
│   └── sephora_loreal_makeup.csv    # Données brutes : L'Oréal Paris
└── scripts/                         # Répertoire des scripts d'automatisation Python
    ├── data_makeup.py               # Script de nettoyage et de fusion des datasets
    ├── fenty_scraper.py             # Robot d'extraction dédié à Fenty Beauty
    ├── scraper_makeupforever.py     # Robot d'extraction dédié à MAKE UP FOR EVER
    ├── scraper_nars.py              # Robot d'extraction dédié à NARS Cosmetics
    └── scraper_sephora_loreal.py    # Robot d'extraction dédié à L'Oréal Paris

🚀 Installation et Utilisation
Prérequis
Pour exécuter les scripts de scraping et de centralisation des données sur votre machine, vous devez installer l'environnement Python 3 et les dépendances associées :
Bash
pip3 install pandas requests beautifulsoup4 openpyxl
Exécution du pipeline
Pour régénérer la base consolidée finale après une mise à jour des scrapers, activez votre environnement virtuel et lancez le script d'assemblage :
Bash
python3 scripts/data_makeup.py
📈 Insights Cliniques & Recommandations Business
L'exploitation de notre tableau de bord Power BI a permis de mettre en lumière trois grands axes stratégiques pour le développement commercial de NARS Cosmetics :
1. Le positionnement "Prestige" face au "Mass-Market"
L'analyse descriptive des prix montre que NARS maintient l'indice de prix le plus élevé de notre panel avec une moyenne de 48,00€ par produit, se détachant de manière drastique de L'Oréal Paris (14,50€). L'analyse fine calculée en DAX confirme que cet écart se maintient lorsque le prix est ramené au millilitre, ce qui valide une stratégie de valeur perçue supérieure basée sur une formulation professionnelle.
2. Le défi de l'inclusivité du catalogue
Si Fenty Beauty dicte le rythme du marché avec des gammes de teintes allant jusqu'à 50 déclinaisons, NARS s'aligne très convenablement avec une profondeur moyenne de 34 teintes. La force majeure de NARS réside dans sa spécialisation et sa domination technique sur les finis de type Radiant (lumineux) et Satiné, sur un marché concurrentiel fortement saturé par le fini mat.
3. Le paradoxe de la visibilité numérique
Le croisement des notes moyennes et des volumes d'avis révèle le véritable point noir de la marque. NARS affiche la meilleure satisfaction globale du panel (4.6/5), mais accuse un immense déficit de visibilité avec seulement 504 avis en moyenne par produit, là où ses concurrents cumulent plusieurs milliers de retours. La qualité du produit est reconnue par les acheteurs, mais la marque manque d'exposition organique.
Recommandations prioritaires :
Introduction de formats Mini (Travel Size) : Déployer des contenants réduits (10-15ml) à un prix d'entrée psychologique d'environ 20€. Cette offre crée une passerelle d'accessibilité pour la clientèle plus jeune des réseaux sociaux, sans dégrader l'image premium des formats standards.
Campagnes de Micro-Influence et UGC : Investir massivement dans le contenu généré par les utilisateurs (User Generated Content) pour stimuler les algorithmes d'Instagram et TikTok, tout en incitant aux dépôts d'avis certifiés pour combler le déficit de visibilité numérique.
Marketing de la Luminescence : Axer le discours de marque sur l'expertise historique du teint lumineux et l'aspect soin des produits afin de distancer la concurrence sur son propre terrain.
👥 Membres de l'Équipe (Groupe 09)
Justin BANDIOLA
Quentin OUDIN
Karen PROUST
Douglas QUINTERO
Juldonnis RAZAFIMANAZATO
