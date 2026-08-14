#!/usr/bin/env python3
"""Individua l'uscita social prevista per una data, senza pubblicarla."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CALENDAR = ROOT / "social-kit" / "config" / "editorial-calendar.json"
TIMEZONE = ZoneInfo("Europe/Rome")


def load_calendar() -> dict:
    return json.loads(CALENDAR.read_text(encoding="utf-8"))


def selected_date(value: str | None) -> str:
    if value:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    return datetime.now(TIMEZONE).date().isoformat()


def write_github_output(path: str, values: dict[str, str]) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="Data da verificare, YYYY-MM-DD; default: oggi in Europe/Rome")
    parser.add_argument("--github-output", help="Scrive gli output per GitHub Actions nel file indicato")
    args = parser.parse_args()

    target = selected_date(args.date)
    calendar = load_calendar()
    posts = [post for post in calendar["posts"] if post["date"] == target]

    if len(posts) > 1:
        raise ValueError(f"Più uscite configurate per {target}: {[post['id'] for post in posts]}")

    if not posts:
        result = {"has_post": "false", "date": target, "post_id": "", "status": ""}
        print(f"Nessuna uscita social prevista per {target}.")
    else:
        post = posts[0]
        result = {
            "has_post": "true",
            "date": target,
            "post_id": post["id"],
            "status": post.get("status", "draft"),
        }
        print(json.dumps(post, ensure_ascii=False, indent=2))

    output_path = args.github_output or os.environ.get("GITHUB_OUTPUT")
    if output_path:
        write_github_output(output_path, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
