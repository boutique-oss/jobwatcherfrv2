from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional

import requests

from scraper.models import JobOffer

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.welcomekit.co/api/v1/external"
_PAGE_SIZE = 100


def _get_api_key() -> Optional[str]:
    return os.environ.get("WTTJ_API_KEY") or os.environ.get("WK_API_KEY")


def _parse_salary(salary: Optional[dict]) -> Optional[str]:
    if not salary:
        return None
    parts = []
    if salary.get("min"):
        parts.append(str(salary["min"]))
    if salary.get("max"):
        parts.append(str(salary["max"]))
    currency = salary.get("currency", "EUR")
    period = salary.get("period", "")
    if parts:
        return f"{' - '.join(parts)} {currency}/{period}".strip("/").strip()
    return None


def _map_offer(raw: dict) -> Optional[JobOffer]:
    # L'URL canonique est apply_url ou construite depuis le slug organisation + référence
    url = raw.get("apply_url") or ""
    if not url:
        org = (raw.get("organization") or {}).get("slug", "")
        ref = raw.get("reference", "")
        if org and ref:
            url = f"https://www.welcometothejungle.com/fr/companies/{org}/jobs/{ref}"
    if not url:
        return None

    posted_at: Optional[datetime] = None
    if date_str := raw.get("published_at") or raw.get("created_at"):
        try:
            posted_at = datetime.fromisoformat(date_str.rstrip("Z"))
        except ValueError:
            pass

    salary_str = _parse_salary(raw.get("salary"))

    company: Optional[str] = None
    if org_data := raw.get("organization"):
        company = org_data.get("name")

    location: Optional[str] = None
    if office := raw.get("office"):
        city = office.get("city") or ""
        country = office.get("country") or ""
        location = f"{city}, {country}".strip(", ") or None

    return JobOffer(
        url=url,
        source="wttj",
        title=raw.get("name", ""),
        company=company,
        location=location,
        contract_type=raw.get("contract_type"),
        salary=salary_str,
        description=raw.get("description") or raw.get("profile"),
        posted_at=posted_at,
        raw_data=raw,
    )


def fetch(keywords: Optional[str] = None, location: Optional[str] = None) -> List[JobOffer]:
    api_key = _get_api_key()
    if not api_key:
        logger.error(
            "WTTJ_API_KEY manquant. Demander un token sur contact@welcomekit.co "
            "ou via le portail partenaire WTTJ."
        )
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    results: List[JobOffer] = []
    page = 1

    while True:
        params: dict = {
            "status": "published",
            "per_page": _PAGE_SIZE,
            "page": page,
            "office": "true",
            "organization": "true",
        }

        try:
            resp = requests.get(
                f"{_BASE_URL}/jobs/all",
                headers=headers,
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("WTTJ API error (page %d): %s", page, exc)
            break

        jobs_page = data if isinstance(data, list) else data.get("data", data.get("jobs", []))
        if not jobs_page:
            break

        for raw in jobs_page:
            offer = _map_offer(raw)
            if offer:
                results.append(offer)

        # Filtrage local par mot-clé si pas de filtre API disponible
        if keywords and page == 1:
            kw = keywords.lower()
            results = [
                j for j in results
                if kw in j.title.lower() or kw in (j.description or "").lower()
            ]

        # Arrêt si la page est incomplète (dernière page)
        if len(jobs_page) < _PAGE_SIZE:
            break

        page += 1

    logger.info("WTTJ: fetched %d offers", len(results))
    return results
