#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path("source-exploration")
OUT.mkdir(exist_ok=True)
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 OsservatorioVersilia/1.0"})


def inspect_page(label: str, url: str, keywords: tuple[str, ...]) -> None:
    try:
        r = S.get(url, timeout=60, allow_redirects=True)
        print("PAGE", label, r.status_code, len(r.content), r.headers.get("content-type"), r.url, flush=True)
        record = {
            "label": label,
            "url": url,
            "final_url": r.url,
            "status": r.status_code,
            "content_type": r.headers.get("content-type"),
            "bytes": len(r.content),
        }
        r.raise_for_status()
        text = r.text
        (OUT / f"{label}_page.html").write_text(text, encoding="utf-8")
        soup = BeautifulSoup(text, "html.parser")
        rows = []
        for tag in soup.find_all(["a", "iframe", "script", "link"]):
            attr = "href" if tag.name in ("a", "link") else "src"
            value = tag.get(attr)
            if not value:
                continue
            absolute = urljoin(r.url, value)
            combined = (absolute + " " + tag.get_text(" ", strip=True)).lower()
            if any(k in combined for k in keywords):
                rows.append({"tag": tag.name, "text": tag.get_text(" ", strip=True)[:300], "url": absolute})
        record["links"] = rows
        print(label, "interesting links", len(rows), flush=True)
        for row in rows[:100]:
            print(row, flush=True)
    except Exception as exc:
        record = {"label": label, "url": url, "error": repr(exc)}
        print(label, repr(exc), flush=True)
    (OUT / f"{label}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    pages = {
        "mim_anagrafe_statali": "https://dati.istruzione.it/opendata/opendata/catalog/SCUANAGRAFESTAT/SCUANAGRAFESTAT20242520250831.csv",
        "mim_studenti_classi_statali": "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLASTA/ALUCORSOINDCLASTA20242520250831.csv",
        "mim_tempo_scuola_statali": "https://dati.istruzione.it/opendata/opendata/catalog/ALUTEMPOSCUOLASTA/ALUTEMPOSCUOLASTA20242520250831.csv",
        "mim_anagrafe_paritarie": "https://dati.istruzione.it/opendata/opendata/catalog/SCUANAGRAFEPAR/SCUANAGRAFEPAR20242520250831.csv",
        "mim_studenti_classi_paritarie": "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLAPAR/ALUCORSOINDCLAPAR20242520250831.csv",
        "mim_tempo_scuola_paritarie": "https://dati.istruzione.it/opendata/opendata/catalog/ALUTEMPOSCUOLAPAR20242520250831.csv",
    }
    for label, url in pages.items():
        inspect_page(label, url, (".csv", "download", "scarica", "202425"))
    inspect_page("sil", "https://www.regione.toscana.it/osservatorio-regionale-mercato-del-lavoro/consultazione-dati-sil", ("csv", "xls", "ods", "tableau", "powerbi", "dashboard", "download", "sil"))
    inspect_page("turismo2025", "https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025", ("csv", "xls", "ods", "download", "locazioni", "comuni"))


if __name__ == "__main__":
    main()
