#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path("source-exploration")
OUT.mkdir(exist_ok=True)
S = requests.Session()
S.headers.update({"User-Agent": "OsservatorioVersilia/1.0 source verification"})


def get(url: str, timeout: int = 180) -> requests.Response:
    r = S.get(url, timeout=timeout, allow_redirects=True)
    print(f"GET {r.status_code} {len(r.content):,} {r.headers.get('content-type')} {r.url}")
    return r


def inspect_zip() -> None:
    url = "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip"
    r = get(url)
    r.raise_for_status()
    (OUT / "istat_sha_info.txt").write_text(f"url={r.url}\nbytes={len(r.content)}\n", encoding="utf-8")
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        names = z.namelist()
        (OUT / "istat_zip_files.txt").write_text("\n".join(names), encoding="utf-8")
        print("ISTAT ZIP files:", len(names))
        for name in names:
            low = name.lower()
            if "tosc" in low or re.search(r"(^|[/_])09([/_]|\.)", low):
                print("TOSCANA CANDIDATE", name, z.getinfo(name).file_size)
                if name.lower().endswith((".csv", ".txt")):
                    raw = z.read(name)
                    (OUT / Path(name).name).write_bytes(raw)
                    text = raw[:20000].decode("utf-8", errors="replace")
                    print(text[:3000])


def inspect_url(label: str, url: str) -> None:
    try:
        r = get(url)
        record = {
            "label": label,
            "url": url,
            "final_url": r.url,
            "status": r.status_code,
            "content_type": r.headers.get("content-type"),
            "bytes": len(r.content),
            "head": r.content[:500].decode("utf-8", errors="replace"),
        }
        (OUT / f"{label}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        if r.ok and len(r.content) < 100_000_000:
            suffix = ".csv" if "csv" in url.lower() else ".bin"
            (OUT / f"{label}{suffix}").write_bytes(r.content)
    except Exception as exc:
        (OUT / f"{label}.json").write_text(json.dumps({"label": label, "url": url, "error": repr(exc)}, indent=2), encoding="utf-8")
        print(label, repr(exc))


def inspect_page(label: str, url: str) -> None:
    r = get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for tag in soup.find_all(["a", "iframe", "script"]):
        attr = "href" if tag.name == "a" else "src"
        value = tag.get(attr)
        if not value:
            continue
        absolute = urljoin(r.url, value)
        if any(k in absolute.lower() for k in ("csv", "xls", "ods", "tableau", "powerbi", "iframe", "dashboard", "download", "sil")):
            rows.append({"tag": tag.name, "text": tag.get_text(" ", strip=True)[:200], "url": absolute})
    (OUT / f"{label}_links.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(label, "interesting links", len(rows))
    for row in rows[:100]:
        print(row)


def main() -> None:
    inspect_zip()
    candidates = {
        "mim_anagrafe_statali": "https://dati.istruzione.it/opendata/opendata/catalog/SCUANAGRAFESTAT/SCUANAGRAFESTAT20242520250831.csv",
        "mim_studenti_classi_statali": "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLASTA/ALUCORSOINDCLASTA20242520250831.csv",
        "mim_tempo_scuola_statali": "https://dati.istruzione.it/opendata/opendata/catalog/ALUTEMPOSCUOLASTA/ALUTEMPOSCUOLASTA20242520250831.csv",
        "mim_anagrafe_paritarie": "https://dati.istruzione.it/opendata/opendata/catalog/SCUANAGRAFEPAR/SCUANAGRAFEPAR20242520250831.csv",
        "mim_studenti_classi_paritarie": "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLAPAR/ALUCORSOINDCLAPAR20242520250831.csv",
    }
    for label, url in candidates.items():
        inspect_url(label, url)
    inspect_page("sil", "https://www.regione.toscana.it/osservatorio-regionale-mercato-del-lavoro/consultazione-dati-sil")
    inspect_page("turismo2025", "https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025")


if __name__ == "__main__":
    main()
