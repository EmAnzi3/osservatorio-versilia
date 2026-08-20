#!/usr/bin/env python3
"""Sonda read-only delle fonti Istat Demo per il Lotto A demografico.

Non modifica alcun dato del sito. Produce un report JSON utile a confermare URL,
struttura degli archivi e copertura dei sette codici comunali.
"""
from __future__ import annotations

import csv
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "audit-artifacts" / "istat-demography-source-scan.json"
TOWN_CODES = ["046005", "046013", "046018", "046024", "046028", "046030", "046033"]
PAGES = {
    "balance": "https://demo.istat.it/app/?i=P02&l=it",
    "population_age_sex": "https://demo.istat.it/app/?i=POS&l=it",
    "citizenship_birth_country": "https://demo.istat.it/app/?i=RCS&l=it",
}
KNOWN_CANDIDATES = {
    "balance_2025_all_municipalities": [
        "https://demo.istat.it/data/p2/P2_2025_it_Comuni.zip",
    ],
    "population_age_sex_2026": [
        "https://demo.istat.it/data/pos/POS_2026_it_Comuni.zip",
        "https://demo.istat.it/data/pos/Pos_2026_it_Comuni.zip",
        "https://demo.istat.it/data/pos/pos_2026_it_Comuni.zip",
        "https://demo.istat.it/data/pos/Posas_2026_it_Comuni.zip",
        "https://demo.istat.it/data/pos/POSAS_2026_it_Comuni.zip",
    ],
}


def request(url: str, *, timeout: int = 30) -> tuple[int, str, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-data-audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            return response.status, response.headers.get("Content-Type", ""), body
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()
    except Exception as exc:  # network failures belong in the audit report
        return 0, type(exc).__name__, str(exc).encode("utf-8", errors="replace")


def zip_links(page_url: str, body: bytes) -> list[str]:
    text = body.decode("utf-8", errors="replace")
    raw = re.findall(r'''(?:href|src)=["']([^"']+\.zip(?:\?[^"']*)?)["']''', text, flags=re.I)
    raw += re.findall(r'''https?://[^\s"']+\.zip(?:\?[^\s"']*)?''', text, flags=re.I)
    return sorted({urllib.parse.urljoin(page_url, link.replace("&amp;", "&")) for link in raw})


def decode_csv(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def inspect_zip(url: str, body: bytes) -> dict:
    result: dict = {"url": url, "zipBytes": len(body)}
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            names = archive.namelist()
            result["members"] = names[:100]
            csv_names = [name for name in names if name.lower().endswith((".csv", ".txt"))]
            result["csvMembers"] = csv_names[:50]
            found_codes: set[str] = set()
            samples: list[dict] = []
            for name in csv_names:
                text = decode_csv(archive.read(name))
                lines = [line for line in text.splitlines() if line.strip()]
                if not lines:
                    continue
                try:
                    dialect = csv.Sniffer().sniff("\n".join(lines[:10]), delimiters=";,\t|")
                    delimiter = dialect.delimiter
                except csv.Error:
                    delimiter = ";"
                rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
                if not rows:
                    continue
                header = rows[0]
                for row in rows[1:]:
                    row_text = "|".join(row)
                    for code in TOWN_CODES:
                        if code in row_text:
                            found_codes.add(code)
                            if len(samples) < 14:
                                samples.append({"member": name, "header": header, "row": row})
                if len(found_codes) == len(TOWN_CODES):
                    break
            result["townCodesFound"] = sorted(found_codes)
            result["coverage"] = len(found_codes)
            result["samples"] = samples
    except Exception as exc:
        result["inspectionError"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> None:
    report: dict = {
        "townCodes": TOWN_CODES,
        "pages": {},
        "candidateDownloads": {},
    }

    discovered: set[str] = set()
    for key, url in PAGES.items():
        status, content_type, body = request(url)
        links = zip_links(url, body) if status == 200 else []
        discovered.update(links)
        report["pages"][key] = {
            "url": url,
            "status": status,
            "contentType": content_type,
            "bytes": len(body),
            "zipLinks": links,
        }

    candidates = {key: list(urls) for key, urls in KNOWN_CANDIDATES.items()}
    # Qualsiasi URL ZIP esposto dalle pagine ufficiali viene verificato senza
    # assumere a priori il naming scelto da Istat.
    candidates["discovered_from_official_pages"] = sorted(discovered)

    for group, urls in candidates.items():
        entries = []
        for url in urls:
            status, content_type, body = request(url)
            entry = {
                "url": url,
                "status": status,
                "contentType": content_type,
                "bytes": len(body),
            }
            if status == 200 and ("zip" in content_type.lower() or body[:4] == b"PK\x03\x04"):
                entry.update(inspect_zip(url, body))
            entries.append(entry)
        report["candidateDownloads"][group] = entries

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Audit Istat scritto in {OUTPUT}")

    p2_entries = report["candidateDownloads"]["balance_2025_all_municipalities"]
    p2_ok = [entry for entry in p2_entries if entry.get("status") == 200 and entry.get("coverage") == 7]
    if p2_ok:
        print("P02 2025: copertura 7/7 confermata")
    else:
        print("P02 2025: endpoint/copertura da ispezionare nell'artifact")


if __name__ == "__main__":
    main()
