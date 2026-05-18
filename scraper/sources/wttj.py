from __future__ import annotations

import logging
import os
import random
import time
from typing import List, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from scraper.models import JobOffer

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.welcometothejungle.com/fr/jobs"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _parse_page(html: str, base_url: str = "https://www.welcometothejungle.com") -> List[JobOffer]:
    soup = BeautifulSoup(html, "html.parser")
    offers: List[JobOffer] = []

    for card in soup.select("[data-testid='search-results-list-item-wrapper']"):
        try:
            title_el = card.select_one("[data-testid='job-title']") or card.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else ""

            company_el = card.select_one("[data-testid='company-name']") or card.select_one("span[class*='company']")
            company: Optional[str] = company_el.get_text(strip=True) if company_el else None

            location_el = card.select_one("[data-testid='job-location']") or card.select_one("span[class*='location']")
            location: Optional[str] = location_el.get_text(strip=True) if location_el else None

            contract_el = card.select_one("[data-testid='job-contract-type']")
            contract_type: Optional[str] = contract_el.get_text(strip=True) if contract_el else None

            link_el = card.select_one("a[href]")
            href: str = link_el["href"] if link_el else ""
            url = href if href.startswith("http") else f"{base_url}{href}"

            if not url or not title:
                continue

            offers.append(
                JobOffer(
                    url=url,
                    source="wttj",
                    title=title,
                    company=company,
                    location=location,
                    contract_type=contract_type,
                )
            )
        except Exception as exc:
            logger.debug("WTTJ card parse error: %s", exc)

    return offers


def fetch(keywords: Optional[str] = None, location: Optional[str] = None) -> List[JobOffer]:
    kw = keywords or os.environ.get("KEYWORDS", "")
    loc = location or os.environ.get("LOCATION", "")

    params: dict = {}
    if kw:
        params["query"] = kw
    if loc:
        params["aroundQuery"] = loc

    results: List[JobOffer] = []
    page = 1

    while page <= 5:  # cap at 5 pages to be respectful
        try:
            resp = requests.get(
                _BASE_URL,
                headers=_HEADERS,
                params={**params, "page": page},
                timeout=20,
            )
            resp.raise_for_status()
        except Exception as exc:
            logger.error("WTTJ request error (page %d): %s", page, exc)
            break

        offers = _parse_page(resp.text)
        if not offers:
            break

        results.extend(offers)
        page += 1
        time.sleep(random.uniform(1, 3))

    logger.info("WTTJ: fetched %d offers", len(results))
    return results
