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
        typer.echo(f"  -> {len(jobs)} offres")
        all_jobs.extend(jobs)

    if not all_jobs:
        typer.echo("No offers collected.")
        raise typer.Exit()

    typer.echo(f"Upserting {len(all_jobs)} offers...")
    stats = upsert_jobs(all_jobs)
    typer.echo(
        f"Done: {stats['inserted']} nouvelles offres inserees, {stats['skipped']} doublons ignores."
    )


@app.command()
def stats() -> None:
    """Show offer counts per source and last scrape date."""
    from scraper.storage.supabase_client import count_by_source, get_last_scraped

    for src in ("france_travail", "wttj", "apec"):
        count = count_by_source(src)
        last = get_last_scraped(src)
        typer.echo(f"{src:15s} {count:>5} offres   dernière collecte: {last[:19] if last != 'jamais' else last}")


@app.command(name="reset-read")
def reset_read() -> None:
    """Reset is_read=False on all job offers."""
    import requests as req
    from scraper.storage.supabase_client import _get_config, _headers

    url, key = _get_config()
    req.patch(
        f"{url}/rest/v1/jobs",
        json={"is_read": False},
        headers={**_headers(key), "Prefer": "return=minimal"},
        params={"is_read": "eq.true"},
        timeout=15,
    ).raise_for_status()
    typer.echo("Toutes les offres remises en 'non lu'.")


if __name__ == "__main__":
    app()
