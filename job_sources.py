"""Public job-board connectors for Greenhouse and Lever hosted job boards.

Only fetches public, unauthenticated company job-board feeds. No login scraping.
"""
from __future__ import annotations

from typing import Any
import requests

TIMEOUT_SECONDS = 20
USER_AGENT = "AIJobSearchAgent/2.0 (public job-board discovery)"


def _get_json(url: str) -> Any:
    response = requests.get(url, timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()


def fetch_greenhouse(board_token: str) -> list[dict]:
    token = board_token.strip()
    if not token or "/" in token:
        raise ValueError("Enter a Greenhouse board token, not a URL.")
    payload = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    jobs = []
    for item in payload.get("jobs", []):
        loc = (item.get("location") or {}).get("name", "")
        jobs.append({
            "title": item.get("title", ""), "company": token,
            "location": loc, "work_mode": "Remote" if "remote" in loc.lower() else "",
            "url": item.get("absolute_url", ""), "posted_date": item.get("updated_at", "")[:10],
            "description": item.get("content", "") or "",
            "source": "Greenhouse", "external_id": str(item.get("id", "")),
        })
    return jobs


def fetch_lever(site: str) -> list[dict]:
    slug = site.strip()
    if not slug or "/" in slug:
        raise ValueError("Enter a Lever site slug, not a URL.")
    payload = _get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    jobs = []
    for item in payload if isinstance(payload, list) else []:
        categories = item.get("categories") or {}
        location = categories.get("location", "")
        description = "\n".join(filter(None, [
            item.get("descriptionPlain", ""), item.get("additionalPlain", ""),
            "\n".join(x.get("content", "") for x in item.get("lists", []) if isinstance(x, dict)),
        ]))
        jobs.append({
            "title": item.get("text", ""), "company": slug,
            "location": location, "work_mode": "Remote" if "remote" in location.lower() else "",
            "url": item.get("hostedUrl", ""), "posted_date": "",
            "description": description, "source": "Lever",
            "external_id": str(item.get("id", "")),
        })
    return jobs


def fetch_configured_sources(config_text: str) -> tuple[list[dict], list[str]]:
    """Read newline-separated `greenhouse:token` / `lever:slug` entries."""
    jobs: list[dict] = []
    errors: list[str] = []
    entries = [line.strip() for line in config_text.splitlines() if line.strip() and not line.strip().startswith("#")]
    for entry in entries:
        try:
            kind, value = entry.split(":", 1)
            if kind.lower() == "greenhouse":
                jobs.extend(fetch_greenhouse(value))
            elif kind.lower() == "lever":
                jobs.extend(fetch_lever(value))
            else:
                raise ValueError("Source must be greenhouse or lever.")
        except Exception as exc:
            errors.append(f"{entry}: {exc}")
    return jobs, errors
