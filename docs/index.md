---
layout: default
title: Accueil
nav_order: 1
---

# Job Watcher FR

Agrégateur d'offres d'emploi scrappées toutes les 6h depuis trois sources françaises.

## Sources

| Source | Méthode |
|---|---|
| France Travail | API OAuth2 officielle |
| Welcome to the Jungle | API WelcomeKit |
| APEC | API publique |

## Démarrage rapide

```bash
# Installer les dépendances
pip install -r requirements.txt

# Copier et remplir les credentials
cp .env.example .env

# Premier scraping
python cli.py scrape

# Interface locale
streamlit run ui/app.py
```

## Commandes CLI

```bash
python cli.py scrape              # toutes les sources
python cli.py scrape --source ft  # France Travail uniquement
python cli.py stats               # statistiques
python cli.py reset-read          # marquer toutes non lues
```

## Variables d'environnement

| Variable | Usage |
|---|---|
| `SUPABASE_URL` | URL du projet Supabase |
| `SUPABASE_KEY` | Clé anon ou service |
| `FT_CLIENT_ID` | OAuth2 France Travail |
| `FT_CLIENT_SECRET` | OAuth2 France Travail |
| `APEC_API_KEY` | Clé API APEC (optionnelle) |
| `WTTJ_API_KEY` | Token Bearer WelcomeKit |
| `KEYWORDS` | Mots-clés de recherche |
| `LOCATION` | Code commune ou département |

## Architecture

```
job-scraper/
├── cli.py                        # Typer CLI
├── ui/app.py                     # Interface Streamlit
├── scraper/
│   ├── models.py                 # Dataclass JobOffer
│   ├── sources/
│   │   ├── france_travail.py
│   │   ├── wttj.py
│   │   └── apec.py
│   └── storage/
│       └── supabase_client.py    # Upsert via REST
└── .github/workflows/scrape.yml  # Cron toutes les 6h
```

[Voir le code source sur GitHub](https://github.com/boutique-oss/jobwatcherfrv2)
