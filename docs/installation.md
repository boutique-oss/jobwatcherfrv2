---
layout: default
title: Installation
nav_order: 2
---

# Installation

## Prérequis

- Python 3.11+
- Un projet [Supabase](https://supabase.com) (gratuit)
- Accès aux APIs : France Travail, WTTJ, APEC

## 1. Cloner le repo

```bash
git clone https://github.com/boutique-oss/jobwatcherfrv2.git
cd jobwatcherfrv2
```

## 2. Environnement virtuel

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

## 3. Credentials

```bash
cp .env.example .env
```

Éditer `.env` avec tes valeurs :

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
FT_CLIENT_ID=...
FT_CLIENT_SECRET=...
WTTJ_API_KEY=...
KEYWORDS=data analyst
LOCATION=75
```

## 4. Schéma Supabase

Coller ce SQL dans **Supabase → SQL Editor** :

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

## 5. Premier test

```bash
python cli.py scrape --source ft
python cli.py stats
```
