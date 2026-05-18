from __future__ import annotations

import logging
import os
from typing import Optional

import typer
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = typer.Typer(help="Job Scraper CLI — France Travail, WTTJ, APEC")


def _run_source(name: str) -> list:
    from scraper.sources import france_travail, wttj, apec

    runners = {
        "ft": france_travail.fetch,
        "wttj": wttj.fetch,
        "apec": apec.fetch,
    }
    try:
        return runners[name]()
    except Exception as exc:
        logging.error("Source %s failed: %s", name, exc)
        return []


@app.command()
def scrape(
    source: Optional[str] = typer.Option(
        None,
        "--source",
        "-s",
        help="Run a single source: ft | wttj | apec",
    )
) -> None:
    """Scrape job offers and upsert them into Supabase."""
    from scraper.storage.supabase_client import upsert_jobs

    sources = [source] if source else ["ft", "wttj", "apec"]

    all_jobs = []
    for src in sources:
        typer.echo(f"Scraping {src}...")
        jobs = _run_source(src)
        typer.echo(f"  → {len(jobs)} offers fetched")
        all_jobs.extend(jobs)

    if not all_jobs:
        typer.echo("No offers collected.")
        raise typer.Exit()

    typer.echo(f"Upserting {len(all_jobs)} offers...")
    stats = upsert_jobs(all_jobs)
    typer.echo(
        f"Done — {stats['inserted']} new offers inserted, {stats['skipped']} duplicates skipped."
    )


@app.command()
def stats() -> None:
    """Show offer counts per source and last scrape date."""
    from dotenv import load_dotenv
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        typer.echo("SUPABASE_URL and SUPABASE_KEY are required.", err=True)
        raise typer.Exit(1)

    client = create_client(url, key)

    for src in ("france_travail", "wttj", "apec"):
        resp = client.table("jobs").select("scraped_at").eq("source", src).order("scraped_at", desc=True).limit(1).execute()
        count_resp = client.table("jobs").select("url", count="exact").eq("source", src).execute()
        count = count_resp.count or 0
        last = resp.data[0]["scraped_at"] if resp.data else "never"
        typer.echo(f"{src:15s} {count:>5} offers   last: {last}")


@app.command(name="reset-read")
def reset_read() -> None:
    """Reset is_read=False on all job offers."""
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        typer.echo("SUPABASE_URL and SUPABASE_KEY are required.", err=True)
        raise typer.Exit(1)

    client = create_client(url, key)
    client.table("jobs").update({"is_read": False}).neq("is_read", None).execute()
    typer.echo("All offers marked as unread.")


if __name__ == "__main__":
    app()
