from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional

import requests

from scraper.models import JobOffer

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
_SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
_PAGE_SIZE = 150


def _get_token(client_id: str, client_secret: str) -> str:
    resp = requests.post(
        _TOKEN_URL,
        params={"realm": "/partenaire"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "api_offresdemploiv2 o2dsoffre",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _map_offer(raw: dict) -> JobOffer:
    posted_at: Optional[datetime] = None
    if date_str := raw.get("dateCreation"):
        try:
            posted_at = datetime.fromisoformat(date_str.rstrip("Z"))
        except ValueError:
            pass

    salary: Optional[str] = None
    if sal := raw.get("salaire"):
        salary = sal.get("libelle")

    return JobOffer(
        url=f"https://candidat.francetravail.fr/offres/recherche/detail/{raw['id']}",
        source="france_travail",
        title=raw.get("intitule", ""),
        company=raw.get("entreprise", {}).get("nom"),
        location=raw.get("lieuTravail", {}).get("libelle"),
        contract_type=raw.get("typeContratLibelle"),
        salary=salary,
        description=raw.get("description"),
        posted_at=posted_at,
        raw_data=raw,
    )


def _location_to_dept(location: str) -> str:
    """Convert INSEE commune code or free text to a 2-3 digit departement code."""
    loc = location.strip()
    # Si c'est un code commune INSEE à 5 chiffres (ex: 75056), extraire les 2 premiers
    if loc.isdigit() and len(loc) == 5:
        return loc[:2]
    # Déjà un code département (75, 69, 13, 971...)
    if loc.isdigit() and len(loc) in (2, 3):
        return loc
    # Texte libre — on ne filtre pas par département
    return ""


def fetch(keywords: Optional[str] = None, location: Optional[str] = None) -> List[JobOffer]:
    client_id = os.environ.get("FT_CLIENT_ID")
    client_secret = os.environ.get("FT_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.error("FT_CLIENT_ID and FT_CLIENT_SECRET are required for France Travail scraper")
        return []

    kw = keywords or os.environ.get("KEYWORDS", "")
    loc = location or os.environ.get("LOCATION", "")

    try:
        token = _get_token(client_id, client_secret)
    except Exception as exc:
        logger.error("France Travail auth failed: %s", exc)
        return []

    headers = {"Authorization": f"Bearer {token}"}
    results: List[JobOffer] = []
    start = 0

    dept = _location_to_dept(loc)

    while True:
        end = start + _PAGE_SIZE - 1
        params: dict = {"range": f"{start}-{end}"}
        if kw:
            params["motsCles"] = kw
        if dept:
            params["departement"] = dept

        try:
            resp = requests.get(_SEARCH_URL, headers=headers, params=params, timeout=20)
            # 206 Partial Content = résultats OK (réponse normale de l'API FT v2)
            if resp.status_code not in (200, 206):
                resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("France Travail search error (range %d-%d): %s", start, end, exc)
            break

        offers = data.get("resultats", [])
        results.extend(_map_offer(o) for o in offers)

        # Content-Range: offres 0-149/1234
        content_range = resp.headers.get("Content-Range", "")
        try:
            total = int(content_range.split("/")[-1])
        except (ValueError, IndexError):
            break

        start += _PAGE_SIZE
        if start >= total or not offers:
            break

    logger.info("France Travail: fetched %d offers", len(results))
    return results
