from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

st.set_page_config(page_title="Job Scraper", page_icon="💼", layout="wide")


@st.cache_resource
def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def mark_read(client: Client, job_url: str) -> None:
    client.table("jobs").update({"is_read": True}).eq("url", job_url).execute()


def main() -> None:
    client = get_client()

    # --- sidebar filters ---
    with st.sidebar:
        st.title("Filtres")
        sources = st.multiselect(
            "Source",
            options=["france_travail", "wttj", "apec"],
            default=["france_travail", "wttj", "apec"],
        )
        show_unread_only = st.checkbox("Non lues uniquement", value=False)
        contract_filter = st.text_input("Type de contrat (ex: CDI)")

    # --- fetch data ---
    query = client.table("jobs").select("*").in_("source", sources).order("scraped_at", desc=True)
    if show_unread_only:
        query = query.eq("is_read", False)
    if contract_filter:
        query = query.ilike("contract_type", f"%{contract_filter}%")

    response = query.execute()
    jobs = response.data or []

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
                read_badge = "" if job.get("is_read") else "🔵 "
                st.markdown(
                    f"{read_badge}**[{job['title']}]({job['url']})** — "
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
                        mark_read(client, job["url"])
                        st.rerun()
        st.divider()


if __name__ == "__main__":
    main()
