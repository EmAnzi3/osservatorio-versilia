#!/usr/bin/env python3
"""Sonda read-only delle fonti Istat Demo per il Lotto A demografico.

Non modifica alcun dato del sito. P02 viene ispezionato per la copertura 7/7;
per gli archivi POS/RCS nazionali si effettua solo discovery/HEAD, così l'audit
non scarica inutilmente dataset nazionali molto grandi.
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
    "balance_2025_all_municipalities": ["https://demo.istat.it/data/p2/P2_2025_it_Comuni.zip"],
    "population_age_sex_2026": [
        "https://demo.istat.it/data/pos/POS_2026_it_Comuni.zip",
        "https://demo.istat.it/data/pos/Pos_2026_it_Comuni.zip",
        "https://demo.istat.it/data/pos/pos_2026_it_Comuni.zip",
        "https://demo.istat.it/data/pos/Posas_2026_it_Comuni.zip",
        "https://demo.istat.it/data/pos/POSAS_2026_it_Comuni.zip",
    ],
}


def request(url: str, *, method: str = "GET", timeout: int = 12) -> tuple[int, str, bytes, dict[str, str]]:
    req = urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": "OsservatorioVersilia-data-audit/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = b"" if method == "HEAD" else response.read()
            return response.status, response.headers.get("Content-Type", ""), body, dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        body = b"" if method == "HEAD" else exc.read()
        return exc.code, exc.headers.get("Content-Type", ""), body, dict(exc.headers.items())
    except Exception as exc:
        return 0, type(exc).__name__, str(exc).encode("utf-8", errors="replace"), {}


def zip_links(page_url: str, body: bytes) -> list[str]:
    text = body.decode("utf-8", errors="replace")
    raw = re.findall(r'''(?:href|src)=["']([^"']+\.zip(?:\?[^"']*)?)["']''', text, flags=re.I)
    raw += re.findall(r'''https?://[^\s"']+\.zip(?:\?[^\s"']*)?''', text, flags=re.I)
    return sorted({urllib.parse.urljoin(page_url, link.replace("&amp;", "&")) for link in raw})


def delimiter_for(archive: zipfile.ZipFile, name: str) -> str:
    with archive.open(name) as stream:
        sample = stream.read(8192).decode("utf-8-sig", errors="replace")
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t|").delimiter
    except csv.Error:
        counts = {separator: sample.count(separator) for separator in (";", ",", "\t", "|")}
        return max(counts, key=counts.get)


def iter_rows(archive: zipfile.ZipFile, name: str, delimiter: str):
    with archive.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
        yield from csv.reader(text, delimiter=delimiter)


def inspect_zip(url: str, body: bytes) -> dict:
    result: dict = {"url": url, "zipBytes": len(body)}
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            names = archive.namelist()
            csv_names = [name for name in names if name.lower().endswith((".csv", ".txt"))]
            result["members"] = names[:100]
            result["csvMembers"] = csv_names[:50]
            found_codes: set[str] = set()
            samples: list[dict] = []
            scanned_rows = 0
            for name in csv_names:
                delimiter = delimiter_for(archive, name)
                reader = iter_rows(archive, name, delimiter)
                try:
                    header = next(reader)
                except StopIteration:
                    continue
                for row in reader:
                    scanned_rows += 1
                    row_text = "|".join(row)
                    matched = [code for code in TOWN_CODES if code in row_text]
                    if not matched:
                        continue
                    for code in matched:
                        if code not in found_codes and len(samples) < 14:
                            samples.append({"code": code, "member": name, "header": header, "row": row})
                        found_codes.add(code)
                    if len(found_codes) == len(TOWN_CODES):
                        break
                if len(found_codes) == len(TOWN_CODES):
                    break
            result["townCodesFound"] = sorted(found_codes)
            result["coverage"] = len(found_codes)
            result["rowsScannedUntilCoverage"] = scanned_rows
            result["samples"] = samples
    except Exception as exc:
        result["inspectionError"] = f"{type(exc).__name__}: {exc}"
    return result


def head_entry(url: str) -> dict:
    status, content_type, _body, headers = request(url, method="HEAD")
    return {
        "url": url,
        "method": "HEAD",
        "status": status,
        "contentType": content_type,
        "contentLength": headers.get("Content-Length"),
        "location": headers.get("Location"),
    }


def main() -> None:
    report: dict = {"townCodes": TOWN_CODES, "pages": {}, "candidateDownloads": {}}

    discovered: set[str] = set()
    for key, url in PAGES.items():
        status, content_type, body, _headers = request(url)
        links = zip_links(url, body) if status == 200 else []
        discovered.update(links)
        report["pages"][key] = {
            "url": url,
            "status": status,
            "contentType": content_type,
            "bytes": len(body),
            "zipLinks": links,
        }

    # Il solo archivio nazionale che scarichiamo in questa sonda è P02: è
    # relativamente compatto e serve a confermare davvero la copertura 7/7.
    p2_url = KNOWN_CANDIDATES["balance_2025_all_municipalities"][0]
    status, content_type, body, _headers = request(p2_url)
    p2_entry = {"url": p2_url, "method": "GET", "status": status, "contentType": content_type, "bytes": len(body)}
    if status == 200 and ("zip" in content_type.lower() or body[:4] == b"PK\x03\x04"):
        p2_entry.update(inspect_zip(p2_url, body))
    report["candidateDownloads"]["balance_2025_all_municipalities"] = [p2_entry]

    # POS: solo discovery/HEAD. La successiva acquisizione userà il file della
    # provincia di Lucca, non l'archivio nazionale.
    report["candidateDownloads"]["population_age_sex_2026"] = [
        head_entry(url) for url in KNOWN_CANDIDATES["population_age_sex_2026"]
    ]
    report["candidateDownloads"]["discovered_from_official_pages"] = [head_entry(url) for url in sorted(discovered)[:100]]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Audit Istat scritto in {OUTPUT}")

    p2_ok = p2_entry.get("status") == 200 and p2_entry.get("coverage") == 7
    print("P02 2025: copertura 7/7 confermata" if p2_ok else "P02 2025: endpoint/copertura da ispezionare nell'artifact")


if __name__ == "__main__":
    main()
