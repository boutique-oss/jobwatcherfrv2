from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional

import requests

from scraper.models import JobOffer

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.apec.fr/cms/webservices/rechercheOffre"
_OFFER_BASE  = "https://www.apec.fr/candidat/recherche-emploi.html/emploi"
_PAGE_SIZE   = 50

_CONTRACT_TYPES: dict[int, str] = {
    101887: "CDD",
    101888: "CDI",
    597171: "Stage",
    101930: "Intérim",
    20053:  "Alternance",
}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": "https://www.apec.fr/candidat/recherche-emploi.html",
    "Origin": "https://www.apec.fr",
    "Content-Type": "application/json;charset=UTF-8",
}


def _build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_HEADERS)
    try:
        s.get("https://www.apec.fr/", timeout=10)
    except Exception:
        pass
    return s


def _map_offer(raw: dict) -> Optional[JobOffer]:
    numero = raw.get("numeroOffre")
    if not numero:
        return None

    posted_at: Optional[datetime] = None
    if date_ms := raw.get("datePublication"):
        try:
            posted_at = datetime.fromtimestamp(int(date_ms) / 1000)
        except (TypeError, OSError, ValueError):
            pass

    return JobOffer(
        url=f"{_OFFER_BASE}/{numero}",
        source="apec",
        title=raw.get("intitule", ""),
        company=raw.get("nomCommercial") or raw.get("raisonSociale"),
        location=raw.get("lieuTexte"),
        contract_type=_CONTRACT_TYPES.get(raw.get("typeContrat", 0)) or raw.get("libelleTypeContrat"),
        salary=raw.get("salaireTexte"),
        description=raw.get("texteOffre"),
        posted_at=posted_at,
        raw_data=raw,
    )


def _build_payload(kw: str, start: int) -> dict:
    return {
        "motsCles": kw or None,
        "lieux": [],
        "fonctions": [],
        "secteursActivite": [],
        "typesTeletravail": [],
        "typesContrat": [],
        "niveauxExperience": [],
        "niveauEtude": None,
        "anciennetePublication": None,
        "salaireMinimum": None,
        "salaireMaximum": None,
        "pagination": {"startIndex": start, "range": _PAGE_SIZE},
        "sorts": [],
        "activeFiltre": False,
        "activeSurbrillance": False,
        "localisable": False,
        "confidentielle": False,
    }


def fetch(keywords: Optional[str] = None, location: Optional[str] = None) -> List[JobOffer]:
    kw = keywords or os.environ.get("KEYWORDS", "")
    # APEC n'accepte pas de filtre géographique textuel libre dans ce payload —
    # utiliser lieux[] avec des IDs APEC si besoin de filtrage précis.

    session = _build_session()
    results: List[JobOffer] = []
    start = 0

    while True:
        payload = _build_payload(kw, start)
        try:
            resp = session.post(_SEARCH_URL, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("APEC request error (start %d): %s", start, exc)
            break

        for raw in data.get("resultats", []):
            offer = _map_offer(raw)
            if offer:
                results.append(offer)

        total = data.get("totalCount", 0)
        start += _PAGE_SIZE
        if start >= total or not data.get("resultats"):
            break

        # Cap à 500 offres pour éviter les requêtes excessives
        if start >= 500:
            logger.info("APEC: cap 500 offres atteint, arrêt pagination")
            break

    logger.info("APEC: fetched %d offers", len(results))
    return results
