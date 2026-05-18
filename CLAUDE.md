# job-scraper — CLAUDE.md

## Architecture

- `scraper/models.py` — `JobOffer` dataclass, clé de dédup = `url`
- `scraper/sources/` — un module par source, chacun expose `fetch() -> List[JobOffer]`
- `scraper/storage/supabase_client.py` — `upsert_jobs()` avec `on_conflict='url'`
- `cli.py` — Typer app : `scrape`, `stats`, `reset-read`
- `ui/app.py` — Streamlit, lecture seule + bouton "Marquer lu"
- `.github/workflows/scrape.yml` — cron toutes les 6h, chaque source en step séparée

## Règles absolues

- Jamais de credentials dans le code — uniquement `os.environ`
- Toutes les fonctions Python typées (annotations complètes)
- L'échec d'un scraper ne doit jamais crasher les autres (try/except + log)
- `.env` est dans `.gitignore` ; `.env.example` ne l'est pas

## Variables d'environnement requises

| Variable | Usage |
|---|---|
| `SUPABASE_URL` | URL du projet Supabase |
| `SUPABASE_KEY` | Clé anon ou service |
| `FT_CLIENT_ID` | OAuth2 France Travail |
| `FT_CLIENT_SECRET` | OAuth2 France Travail |
| `APEC_API_KEY` | Clé API APEC (optionnelle) |
| `WTTJ_API_KEY` | Token Bearer WelcomeKit API (contacter contact@welcomekit.co) |
| `KEYWORDS` | Mots-clés de recherche |
| `LOCATION` | Code commune ou département |

## Schema Supabase (à exécuter une seule fois)

```sql
create table if not exists jobs (
  url          text primary key,
  source       text not null,
  title        text not null,
  company      text,
  location     text,
  contract_type text,
  salary       text,
  description  text,
  posted_at    timestamptz,
  raw_data     jsonb,
  is_read      boolean default false,
  scraped_at   timestamptz default now()
);
```

## Commandes utiles

```bash
# Lancer tous les scrapers
python cli.py scrape

# Une seule source
python cli.py scrape --source ft

# Stats
python cli.py stats

# UI locale
streamlit run ui/app.py
```
