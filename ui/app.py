from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Job Scraper", page_icon="💼", layout="wide")


def _sb_headers() -> dict:
    key = os.environ["SUPABASE_KEY"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _sb_url() -> str:
    return os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1"


@st.cache_data(ttl=30)
def fetch_jobs(sources: tuple, unread_only: bool, contract_filter: str) -> list[dict]:
    params: dict[str, Any] = {
        "source": f"in.({','.join(sources)})",
        "order": "scraped_at.desc",
        "limit": 500,
    }
    if unread_only:
        params["is_read"] = "eq.false"
    if contract_filter:
        params["contract_type"] = f"ilike.*{contract_filter}*"

    resp = requests.get(
        f"{_sb_url()}/jobs",
        headers=_sb_headers(),
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def mark_read(job_url: str) -> None:
    requests.patch(
        f"{_sb_url()}/jobs",
        json={"is_read": True},
        headers={**_sb_headers(), "Prefer": "return=minimal"},
        params={"url": f"eq.{job_url}"},
        timeout=10,
    ).raise_for_status()


def main() -> None:
    with st.sidebar:
        st.title("Filtres")
        sources = st.multiselect(
            "Source",
            options=["france_travail", "wttj", "apec"],
            default=["france_travail", "wttj", "apec"],
        )
        show_unread_only = st.checkbox("Non lues uniquement", value=False)
        contract_filter = st.text_input("Type de contrat (ex: CDI)")

    if not sources:
        st.warning("Sélectionne au moins une source.")
        return

    try:
        jobs = fetch_jobs(tuple(sources), show_unread_only, contract_filter)
    except Exception as exc:
        st.error(f"Erreur Supabase : {exc}")
        return

    total = len(jobs)
    unread = sum(1 for j in jobs if not j.get("is_read"))

    st.title("💼 Job Scraper")
    st.markdown(f"**{total} offres** | **{unread} non lues**")
    st.divider()

    if not jobs:
        st.info("Aucune offre trouvée avec ces filtres.")
        return

    for job in jobs:
        with st.container():
            col1, col2 = st.columns([9, 1])
            with col1:
                badge = "" if job.get("is_read") else "🔵 "
                st.markdown(
                    f"{badge}**[{job['title']}]({job['url']})** — "
                    f"{job.get('company') or '—'} | "
                    f"{job.get('location') or '—'} | "
                    f"{job.get('contract_type') or '—'} | "
                    f"{job.get('salary') or '—'} | "
                    f"`{job['source']}` | "
                    f"{(job.get('scraped_at') or '')[:10]}"
                )
            with col2:
                if not job.get("is_read"):
                    if st.button("Lu ✓", key=f"read_{job['url']}"):
                        mark_read(job["url"])
                        st.cache_data.clear()
                        st.rerun()
        st.divider()


if __name__ == "__main__":
    main()
