#!/usr/bin/env python3
"""Controlla ricorrenze e capienza prima di preparare i due caroselli settimanali."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def monday_of(value: date) -> date:
    return value - timedelta(days=value.weekday())


def event_date(month_day: str, year: int) -> date:
    month, day = [int(item) for item in month_day.split("-")]
    return date(year, month, day)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=date.today().isoformat(), help="Una data della settimana, YYYY-MM-DD")
    args = parser.parse_args()
    requested = datetime.strptime(args.date, "%Y-%m-%d").date()
    start = monday_of(requested)
    end = start + timedelta(days=6)
    recurrences = load(KIT / "config" / "recurrences.json")
    calendar = load(KIT / "config" / "editorial-calendar.json")
    ready = load(KIT / "config" / "social-ready.json")["approved_metrics"]
    site = load(ROOT / "data" / "site-data.json")["metrics"]
    events = []
    for event in recurrences["events"]:
        occurrence = event_date(event["month_day"], start.year)
        if start <= occurrence <= end:
            candidates = [
                metric for metric in event["candidate_metrics"]
                if metric in ready and metric in site and site[metric].get("sourceUrl")
            ]
            events.append({
                **event,
                "date": occurrence.isoformat(),
                "eligible": bool(candidates),
                "eligible_metrics": candidates,
                "decision": "replace_one_standard_slot" if candidates else "do_not_force",
            })
    scheduled = [post for post in calendar["posts"] if start.isoformat() <= post["date"] <= end.isoformat()]
    result = {
        "week": {"from": start.isoformat(), "to": end.isoformat()},
        "target_posts": calendar["cadence"]["target_posts_per_week"],
        "maximum_posts": calendar["cadence"]["maximum_posts_per_week"],
        "scheduled_posts": [{"id": post["id"], "date": post["date"]} for post in scheduled],
        "official_recurrences": events,
        "rule": recurrences["policy"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
