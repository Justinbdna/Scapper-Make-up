import pandas as pd

# Noms exacts de tes 4 fichiers sources
fichiers = [
    "fenty_teint.csv", 
    "nars_cosmetics.csv", 
    "sephora_loreal_makeup.csv", 
    "makeupforever_teint.csv"
]

# Lecture et fusion des fichiers
dataframes = []
for fichier in fichiers:
    df = pd.read_csv(fichier)
    dataframes.append(df)

master_df = pd.concat(dataframes, ignore_index=True)

# Sauvegarde du fichier final blindé
master_df.to_csv("MASTER_MAKEUP_FINAL.csv", index=False, encoding="utf-8")
print(f"Fusion terminée avec succès ! Le fichier MASTER_MAKEUP_FINAL.csv contient {len(master_df)} produits.")