#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
TEST_STATIC = ROOT / "scripts" / "test_static.py"
CALENDAR = ROOT / "social-kit" / "config" / "editorial-calendar.json"


def clean_series(series):
    if not isinstance(series, dict):
        return series
    years = series.get("years") or []
    values = series.get("values") or []
    pairs = [(year, value) for year, value in zip(years, values) if value is not None]
    result = dict(series)
    result["years"] = [year for year, _ in pairs]
    result["values"] = [value for _, value in pairs]
    return result


def patch_site_data() -> None:
    data = json.loads(SITE.read_text(encoding="utf-8"))
    metric = data["metrics"]["roadSafety"]
    for row in metric["rows"]:
        row["series"] = clean_series(row.get("series"))
        if isinstance(row.get("componentSeries"), dict):
            row["componentSeries"] = {
                key: clean_series(series)
                for key, series in row["componentSeries"].items()
            }
    SITE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_test_static() -> None:
    text = TEST_STATIC.read_text(encoding="utf-8")
    if "expected_indicator_count = len(json.loads" not in text:
        text = text.replace(
            "import contextlib\nimport os\nimport re\n",
            "import contextlib\nimport json\nimport os\nimport re\n",
            1,
        )
        old = '''        hero_facts = mobile_page.locator(".hero-facts").inner_text()\n        assert "119 INDICATORI" in hero_facts and "115 INDICATORI" not in hero_facts, (\n            f"Conteggio complessivo degli indicatori errato in home: {hero_facts!r}"\n        )'''
        new = '''        hero_facts = mobile_page.locator(".hero-facts").inner_text()\n        expected_indicator_count = len(json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))["metrics"])\n        assert f"{expected_indicator_count} INDICATORI" in hero_facts, (\n            f"Conteggio complessivo degli indicatori errato in home: attesi {expected_indicator_count}, trovato {hero_facts!r}"\n        )'''
        if old not in text:
            raise RuntimeError("Assertion hardcoded del conteggio non trovata")
        text = text.replace(old, new, 1)
        TEST_STATIC.write_text(text, encoding="utf-8")


def patch_calendar() -> None:
    data = json.loads(CALENDAR.read_text(encoding="utf-8"))
    changed = False
    for week in data.get("weeks", []):
        if week.get("metric") == "roadInjuries":
            week["metric"] = "roadSafety"
            changed = True
    if changed:
        CALENDAR.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    patch_site_data()
    patch_test_static()
    patch_calendar()
    print("Compatibilità draft sicurezza aggiornata")


if __name__ == "__main__":
    main()
