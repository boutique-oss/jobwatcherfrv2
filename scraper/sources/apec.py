from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional

import requests

from scraper.models import JobOffer

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.apec.fr/cms/webservices/rechercheOffre/rechercheOffresCriteres"


def _map_offer(raw: dict) -> JobOffer:
    posted_at: Optional[datetime] = None
    if date_ms := raw.get("datePublication"):
        try:
            posted_at = datetime.fromtimestamp(date_ms / 1000)
        except (TypeError, OSError):
            pass

    offer_id = raw.get("numeroOffre", "")
    url = f"https://www.apec.fr/candidat/recherche-emploi.html/emploi/{offer_id}" if offer_id else ""

    return JobOffer(
        url=url,
        source="apec",
        title=raw.get("intitule", ""),
        company=raw.get("nomEntreprise"),
        location=raw.get("lieuTravail"),
        contract_type=raw.get("typeContrat"),
        salary=raw.get("salaireTexte"),
        description=raw.get("texteHtml") or raw.get("accroche"),
        posted_at=posted_at,
        raw_data=raw,
    )


def fetch(keywords: Optional[str] = None, location: Optional[str] = None) -> List[JobOffer]:
    api_key = os.environ.get("APEC_API_KEY")
    kw = keywords or os.environ.get("KEYWORDS", "")
    loc = location or os.environ.get("LOCATION", "")

    headers: dict = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "motsCles": kw,
        "lieu": loc,
        "nbResultatsParPage": 50,
        "numeroPage": 0,
        "typesTeletravail": [],
        "typesContrat": [],
    }

    results: List[JobOffer] = []
    page = 0

    while True:
        payload["numeroPage"] = page
        try:
            resp = requests.post(_SEARCH_URL, json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("APEC request error (page %d): %s", page, exc)
            break

        offers = data.get("resultats", [])
        if not offers:
            break

        results.extend(_map_offer(o) for o in offers)

        total = data.get("totalCount", 0)
        page += 1
        if page * 50 >= total:
            break

    logger.info("APEC: fetched %d offers", len(results))
    return results
