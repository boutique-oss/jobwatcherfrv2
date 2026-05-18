from __future__ import annotations

import os
import logging
from typing import List

import requests

from scraper.models import JobOffer

logger = logging.getLogger(__name__)

# La clé Supabase peut être au format JWT (eyJ...) ou publishable (sb_publishable_...).
# Le SDK Python supabase-py rejette le format publishable ; on utilise l'API REST directement.


def _get_config() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
        )
    return url, key


def _headers(key: str) -> dict:
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore-duplicates,return=representation",
    }


def upsert_jobs(jobs: List[JobOffer]) -> dict:
    """Upsert a list of JobOffer into Supabase, deduplicating on url.

    Returns a dict with 'inserted' and 'skipped' counts.
    Fonctionne avec les clés JWT (eyJ...) et publishable (sb_publishable_...).
    """
    if not jobs:
        return {"inserted": 0, "skipped": 0}

    url, key = _get_config()
    endpoint = f"{url}/rest/v1/jobs"
    records = [job.to_dict() for job in jobs]

    # Supabase upsert : on_conflict=url + ignore_duplicates via Prefer header
    try:
        resp = requests.post(
            endpoint,
            json=records,
            headers=_headers(key),
            params={"on_conflict": "url"},
            timeout=30,
        )
        resp.raise_for_status()
        inserted = len(resp.json()) if resp.content else 0
        skipped = len(records) - inserted
        logger.info("Upserted %d jobs (%d new, %d skipped)", len(records), inserted, skipped)
        return {"inserted": inserted, "skipped": skipped}
    except Exception as exc:
        logger.error("Supabase upsert failed: %s", exc)
        raise


def count_by_source(source: str) -> int:
    """Retourne le nombre d'offres pour une source donnée."""
    url, key = _get_config()
    headers = {**_headers(key), "Prefer": "count=exact"}
    resp = requests.get(
        f"{url}/rest/v1/jobs",
        headers=headers,
        params={"source": f"eq.{source}", "select": "url"},
        timeout=10,
    )
    resp.raise_for_status()
    return int(resp.headers.get("content-range", "0/0").split("/")[-1])


def get_last_scraped(source: str) -> str:
    """Retourne la date de dernière collecte pour une source."""
    url, key = _get_config()
    resp = requests.get(
        f"{url}/rest/v1/jobs",
        headers=_headers(key),
        params={"source": f"eq.{source}", "select": "scraped_at", "order": "scraped_at.desc", "limit": 1},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data[0]["scraped_at"] if data else "jamais"
