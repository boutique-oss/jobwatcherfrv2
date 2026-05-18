# job-scraper

Scraper automatisé de recherche d'emploi — France Travail, WTTJ, APEC.

## Installation

```bash
git clone <repo>
cd job-scraper
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

## Configuration

```bash
cp .env.example .env
# Éditer .env avec vos credentials
```

| Variable | Description |
|---|---|
| `SUPABASE_URL` | URL de votre projet Supabase |
| `SUPABASE_KEY` | Clé anon ou service role |
| `FT_CLIENT_ID` | Client ID France Travail (Portail Entreprises) |
| `FT_CLIENT_SECRET` | Client Secret France Travail |
| `APEC_API_KEY` | Clé API APEC (optionnelle) |
| `KEYWORDS` | Mots-clés, ex : `développeur python` |
| `LOCATION` | Code commune INSEE, ex : `75056` pour Paris |

## Schema Supabase

Exécuter ce SQL dans l'éditeur SQL Supabase **avant** le premier lancement :

```sql
create table if not exists jobs (
  url           text primary key,
  source        text not null,
  title         text not null,
  company       text,
  location      text,
  contract_type text,
  salary        text,
  description   text,
  posted_at     timestamptz,
  raw_data      jsonb,
  is_read       boolean default false,
  scraped_at    timestamptz default now()
);
```

## Lancement CLI

```bash
# Toutes les sources
python cli.py scrape

# Une source seulement
python cli.py scrape --source ft      # France Travail
python cli.py scrape --source wttj    # Welcome to the Jungle
python cli.py scrape --source apec    # APEC

# Statistiques
python cli.py stats

# Remettre toutes les offres en "non lu"
python cli.py reset-read
```

## Lancement UI Streamlit

```bash
streamlit run ui/app.py
# Ouvre http://localhost:8501
```

## Déploiement GitHub Actions

1. Pusher le repo sur GitHub
2. Dans **Settings > Secrets and variables > Actions**, ajouter :
   - `SUPABASE_URL`, `SUPABASE_KEY`
   - `FT_CLIENT_ID`, `FT_CLIENT_SECRET`
   - `APEC_API_KEY`
   - `KEYWORDS`, `LOCATION`
3. Le workflow `.github/workflows/scrape.yml` tourne automatiquement toutes les 6h
4. Déclenchement manuel possible via **Actions > Scrape Jobs > Run workflow**

Chaque source est un step indépendant (`continue-on-error: true`) — une panne n'arrête pas les autres.
