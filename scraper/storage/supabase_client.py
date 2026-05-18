from __future__ import annotations

import os
import logging
from typing import List

from supabase import create_client, Client

from scraper.models import JobOffer

logger = logging.getLogger(__name__)


def _get_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
        )
    return create_client(url, key)


def upsert_jobs(jobs: List[JobOffer]) -> dict:
    """Upsert a list of JobOffer into Supabase, deduplicating on url.

    Returns a dict with 'inserted' and 'skipped' counts.
    """
    if not jobs:
        return {"inserted": 0, "skipped": 0}

    client = _get_client()
    records = [job.to_dict() for job in jobs]

    try:
        response = (
            client.table("jobs")
            .upsert(records, on_conflict="url", ignore_duplicates=True)
            .execute()
        )
        inserted = len(response.data) if response.data else 0
        skipped = len(records) - inserted
        logger.info("Upserted %d jobs (%d new, %d skipped)", len(records), inserted, skipped)
        return {"inserted": inserted, "skipped": skipped}
    except Exception as exc:
        logger.error("Supabase upsert failed: %s", exc)
        raise
