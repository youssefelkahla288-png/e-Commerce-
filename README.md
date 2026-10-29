# e-Commerce-

## Catalogue SQLite

Le schéma du catalogue est défini dans `scripts/create_database.py` : `categories`,
`brands` et `products`. `schema.json` est un instantané utilisé par le pipeline
Text-to-SQL ; il est actuellement vide (`{}`). La base `ecommerce.db` du projet
est un fichier vide tant qu'elle n'a pas été initialisée.

### Essayer la recherche sans toucher à la base réelle

La démonstration utilise exclusivement des données fictives (noms, marques,
catégories et prix) et crée un fichier séparé :

```powershell
python -m scripts.create_demo_catalog
```

Le script crée `data/demo_ecommerce.db` et refuse de remplacer ce fichier s'il
existe déjà. Pour utiliser cette base dans le mode local, définissez
`ECOMMERCE_DB_PATH` avant de lancer l'application. Depuis PowerShell :

```powershell
$env:ECOMMERCE_DB_PATH = (Resolve-Path .\data\demo_ecommerce.db).Path
python -m streamlit run streamlit_app.py
```

Avec l'environnement Python 3.12 de ce projet, vous pouvez aussi lancer
`.\scripts\run_demo_streamlit.ps1`. Ce lanceur définit le chemin avant le
démarrage de Python et restaure la variable à la fermeture. Il ne crée pas et
n'écrase pas la base de démonstration.

La base réelle `ecommerce.db` reste la destination par défaut quand cette
variable n'est pas définie. Fermez le terminal après la démonstration pour
retirer cette variable de son environnement.

### Initialiser le vrai catalogue plus tard

Après avoir vérifié la sauvegarde et le chemin de la base, la création du schéma
peut être lancée depuis la racine du projet :

```powershell
python -m scripts.create_database
```

Le script utilise `CREATE TABLE IF NOT EXISTS` et ne remplace pas les tables ou
les lignes déjà présentes. Il ne crée cependant aucun produit réel : ceux-ci
doivent provenir de votre catalogue validé et être ajoutés par une procédure
d'import approuvée. Ne copiez pas les entrées de démonstration dans le catalogue
réel. Après initialisation, vérifiez le schéma et régénérez `schema.json` avec
une procédure contrôlée avant d'utiliser Text-to-SQL ; `python -m
scripts.extract_schema` écrit dans `schema.json` et affiche des valeurs d'exemple,
donc vérifiez le fichier cible et son contenu avant de lancer cette commande.
