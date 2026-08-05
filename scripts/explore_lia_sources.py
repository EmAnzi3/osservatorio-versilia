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
S.headers.update({"User-Agent": "OsservatorioVersilia/1.0 source verification"})


def head(label: str, url: str) -> None:
    try:
        r = S.head(url, timeout=60, allow_redirects=True)
        record = {
            "label": label,
            "url": url,
            "final_url": r.url,
            "status": r.status_code,
            "content_type": r.headers.get("content-type"),
            "content_length": r.headers.get("content-length"),
            "last_modified": r.headers.get("last-modified"),
        }
        print("HEAD", record)
    except Exception as exc:
        record = {"label": label, "url": url, "error": repr(exc)}
        print(record)
    (OUT / f"{label}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def inspect_istat_dataflows() -> None:
    url = "https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1/all/latest"
    r = S.get(url, timeout=120, allow_redirects=True)
    print("ISTAT DATAFLOW", r.status_code, len(r.content), r.headers.get("content-type"))
    r.raise_for_status()
    text = r.text
    (OUT / "istat_dataflows.xml").write_text(text, encoding="utf-8")
    soup = BeautifulSoup(text, "xml")
    matches = []
    words = ("cens", "occup", "lavor", "istruz", "titolo", "abitaz", "famigl")
    for flow in soup.find_all(["Dataflow", "structure:Dataflow"]):
        names = [n.get_text(" ", strip=True) for n in flow.find_all(["Name", "common:Name"])]
        label = " | ".join(names)
        if any(word in label.lower() for word in words):
            matches.append({"id": flow.get("id"), "agency": flow.get("agencyID"), "version": flow.get("version"), "name": label})
    (OUT / "istat_candidate_flows.json").write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ISTAT candidate flows", len(matches))
    for row in matches:
        print(row)


def inspect_page(label: str, url: str) -> None:
    try:
        r = S.get(url, timeout=90, allow_redirects=True)
        print("PAGE", label, r.status_code, len(r.content), r.url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        rows = []
        for tag in soup.find_all(["a", "iframe", "script"]):
            attr = "href" if tag.name == "a" else "src"
            value = tag.get(attr)
            if not value:
                continue
            absolute = urljoin(r.url, value)
            if any(k in absolute.lower() for k in ("csv", "xls", "ods", "tableau", "powerbi", "dashboard", "download", "sil", "open_data")):
                rows.append({"tag": tag.name, "text": tag.get_text(" ", strip=True)[:200], "url": absolute})
        (OUT / f"{label}_links.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(label, "interesting links", len(rows))
        for row in rows[:100]:
            print(row)
    except Exception as exc:
        print(label, repr(exc))
        (OUT / f"{label}_error.txt").write_text(repr(exc), encoding="utf-8")


def main() -> None:
    urls = {
        "istat_sections_zip": "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip",
        "mim_anagrafe_statali": "https://dati.istruzione.it/opendata/opendata/catalog/SCUANAGRAFESTAT/SCUANAGRAFESTAT20242520250831.csv",
        "mim_studenti_classi_statali": "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLASTA/ALUCORSOINDCLASTA20242520250831.csv",
        "mim_tempo_scuola_statali": "https://dati.istruzione.it/opendata/opendata/catalog/ALUTEMPOSCUOLASTA/ALUTEMPOSCUOLASTA20242520250831.csv",
        "mim_anagrafe_paritarie": "https://dati.istruzione.it/opendata/opendata/catalog/SCUANAGRAFEPAR/SCUANAGRAFEPAR20242520250831.csv",
        "mim_studenti_classi_paritarie": "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLAPAR/ALUCORSOINDCLAPAR20242520250831.csv",
    }
    for label, url in urls.items():
        head(label, url)
    inspect_istat_dataflows()
    inspect_page("sil", "https://www.regione.toscana.it/osservatorio-regionale-mercato-del-lavoro/consultazione-dati-sil")
    inspect_page("turismo2025", "https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025")


if __name__ == "__main__":
    main()
