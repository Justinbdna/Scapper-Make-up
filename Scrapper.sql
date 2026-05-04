Entité : MARQUE

ID_Marque (PK - Clef Primaire) : Un identifiant unique généré lors du scraping (ex: M001).

Nom_Marque (ex: Maybelline) : Correspond à la colonne brand de l'image.

Entité : CATEGORIE

ID_Categorie (PK) : Un identifiant unique généré (ex: C001).

Nom_Categorie (ex: fond de teint / correcteur) : Correspond à la colonne category.

Entité : PRODUIT (L'entrée centrale scrapée)

Cette entité contient la majorité de tes données scrapées. J'ai ajouté des identifiants (Clefs Étrangères/FK) pour lier le produit à sa marque et sa catégorie, comme le veut un bon MCD.

ID_Produit (PK) : Identifiant unique du produit scrapé (ex: P001).

FK_ID_Marque (FK) : Lien vers la marque.

FK_ID_Categorie (FK) : Lien vers la catégorie.

Nom_Produit (ex: Fit Me Matte + Poreless) : Correspond à product_name.

Source_URL : Correspond à source_url (crucial pour la traçabilité).

Date_Releve : Attribut recommandé : La date précise où tu as effectué le scraping, indispensable pour analyser l'évolution du prix (price) dans le temps.

Les attributs de caractéristiques (CONSIGNE Arken : Garder au Format Texte brut):
Tu dois scraper ces valeurs exactement comme elles apparaissent sur le site (incluant symboles €, espaces, ou textes "en stock").

Volume_Ml (volume_ml)

Prix_Standard (price)

Prix_Promo (promo_price)

Note_Client (rating)

Nb_Avis (review_count)

Nb_Teintes (shade_count)

Type_Fini (finish_type)

Niveau_Couvrance (coverage_level)

Types_Peau (skin_type)

Statut_Disponibilite (availability)

3. Explications des Relations

Relation Fabrique (Marque vers Produit) : Une MARQUE peut fabriquer un ou plusieurs PRODUITS (cardinalité 1,N). Un PRODUIT appartient à une et une seule MARQUE (cardinalité 1,1).

Relation Classe (Catégorie vers Produit) : Une CATEGORIE peut contenir un ou plusieurs PRODUITS (cardinalité 1,N). Un PRODUIT n'appartient qu'à une seule CATEGORIE (cardinalité 1,1).