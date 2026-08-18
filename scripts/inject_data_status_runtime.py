#!/usr/bin/env python3
"""Incorpora i metadata di stato nelle schede indicatore prerenderizzate.

L'applicazione principale può rerenderizzare il contenuto di #app nel browser.
Per evitare fetch e mantenere i metadata derivati disponibili anche dopo quel
rerender, ogni scheda riceve un piccolo payload JSON locale e l'enhancer comune.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def italian_date(value: str) -> str:
    if not value:
        return "Non ancora registrato"
    from datetime import datetime

    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    months = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
    ]
    return f"{date.day} {months[date.month - 1]} {date.year}"


def main() -> None:
    status_path = DIST / "data" / "data-status.json"
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    metrics = payload.get("metrics") or []
    by_slug = {slugify(str(item["label"])): item for item in metrics}
    injected = 0

    for path in (DIST / "indicatori").glob("*/index.html"):
        metric = by_slug.get(path.parent.name)
        if not metric:
            continue
        text = path.read_text(encoding="utf-8")
        if 'id="ov-indicator-status"' in text:
            injected += 1
            continue

        local = {
            "publishedPeriod": metric.get("publishedPeriod") or "—",
            "statusLabel": metric.get("statusLabel") or "Verifica necessaria",
            "statusTone": metric.get("statusTone") or "problem",
            "statusDescription": metric.get("statusDescription") or "",
            "lastCheckedLabel": italian_date(str(metric.get("lastChecked") or "")),
            "cadenceNote": metric.get("cadenceNote") or "",
            "nextExpectedRelease": metric.get("nextExpectedRelease"),
        }
        encoded = json.dumps(local, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        block = (
            f'<script type="application/json" id="ov-indicator-status">{encoded}</script>\n'
            '  <script src="../../assets/data-status.js" defer></script>\n'
        )
        text = text.replace("</body>", block + "</body>", 1)
        path.write_text(text, encoding="utf-8")
        injected += 1

    if injected != 123:
        raise SystemExit(f"Attese 123 schede indicatore, payload incorporato in {injected}")
    print("Payload stato dati incorporato nelle 123 schede indicatore")


if __name__ == "__main__":
    main()
