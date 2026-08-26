#!/usr/bin/env python3
"""Probe one-shot per chiudere il gate dati del lotto agricoltura.

Legge esclusivamente endpoint ufficiali ISTAT: IstatData SDMX e SITUAS.
Non modifica i dati canonici della repository.
"""
from __future__ import annotations

import csv
import io
import json
import urllib.error
import urllib.parse
import urllib.request

TOWNS = {
    "046005": "Camaiore",
    "046013": "Forte dei Marmi",
    "046018": "Massarosa",
    "046024": "Pietrasanta",
    "046028": "Seravezza",
    "046030": "Stazzema",
    "046033": "Viareggio",
}
ISTAT_BASE = "https://esploradati.istat.it/SDMXWS/rest/data"
CSV_ACCEPT = "application/vnd.sdmx.data+csv;version=1.0.0"


def request(url: str, *, accept: str | None = None, data: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, str, bytes]:
    merged = {"User-Agent": "OsservatorioVersilia-agriculture-probe/2.0"}
    if accept:
        merged["Accept"] = accept
    if headers:
        merged.update(headers)
    req = urllib.request.Request(url, data=data, headers=merged)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return response.status, response.headers.get("Content-Type", ""), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()


def istat_csv(flow: str, key: str) -> tuple[str, list[dict[str, str]]]:
    url = f"{ISTAT_BASE}/{flow}/{key}/IT1?startPeriod=2020&endPeriod=2020"
    status, content_type, body = request(url, accept=CSV_ACCEPT)
    print(f"\n=== ISTAT {flow} ===")
    print(f"url={url}\nstatus={status} type={content_type} bytes={len(body)}")
    if status != 200:
        print(body[:4000].decode("utf-8", errors="replace"))
        raise SystemExit(f"ISTAT query failed: {flow} {status}")
    text = body.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    for row in rows:
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    return url, rows


def print_coverage(label: str, rows: list[dict[str, str]], *, crop: str | None = None) -> None:
    present = set()
    zeros = set()
    for row in rows:
        code = row.get("REF_AREA")
        if code not in TOWNS:
            continue
        if crop is not None and row.get("TYPE_OF_CROP") != crop:
            continue
        present.add(code)
        try:
            if float(row.get("OBS_VALUE", "nan")) == 0:
                zeros.add(code)
        except ValueError:
            pass
    missing = [TOWNS[c] for c in TOWNS if c not in present]
    zero_names = [TOWNS[c] for c in TOWNS if c in zeros]
    print(f"COVERAGE {label}: {len(present)}/7; missing={missing}; explicit_zero={zero_names}")


def probe_istat() -> None:
    areas = "+".join(TOWNS)

    _, surf = istat_csv(
        "DF_DCAT_CENSAGRIC2020_SURF_ALL",
        f"A.{areas}.HO+ARU+FUAA",
    )
    for dtype in ("HO", "ARU", "FUAA"):
        print_coverage(dtype, [r for r in surf if r.get("DATA_TYPE") == dtype])

    crop_codes = ("ALL", "ARLAND", "OLIV", "VINEY", "PGRAPM")
    _, crops = istat_csv(
        "DF_DCAT_CENSAGRIC2020_UA_CROPS_2",
        f"A.{areas}.ARU.{'+'.join(crop_codes)}.TOT",
    )
    for crop in crop_codes:
        print_coverage(f"localized ARU {crop}", crops, crop=crop)

    _, irrigation = istat_csv(
        "DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS",
        f"A.{areas}.IA",
    )
    print_coverage("IA", irrigation)


def probe_situas() -> None:
    gateway = "https://situas.istat.it/ShibO2Module/api/Report/ReportByUrl"
    payload = json.dumps({"url": "get_elenco_microservizi"}).encode("utf-8")
    status, content_type, body = request(
        gateway,
        accept="application/json",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Referer": "https://situas.istat.it/web/",
            "language": "IT",
        },
    )
    print(f"\n=== SITUAS catalog ===\nstatus={status} type={content_type} bytes={len(body)}")
    if status != 200:
        print(body[:4000].decode("utf-8", errors="replace"))
        raise SystemExit("SITUAS catalog failed")
    catalog = json.loads(body.decode("utf-8", errors="replace"), strict=False)
    entries = catalog.get("items") or catalog.get("resultset") or []
    candidates = []
    for entry in entries:
        text = json.dumps(entry, ensure_ascii=False).lower()
        pfun = str(entry.get("PFUN") or entry.get("pfun") or entry.get("P_FUN") or entry.get("p_fun") or "")
        if pfun == "74" or ("comuni" in text and "dimension" in text):
            candidates.append(entry)
    print(f"catalog entries={len(entries)} candidates={len(candidates)}")
    for entry in candidates:
        print("CANDIDATE", json.dumps(entry, ensure_ascii=False, sort_keys=True))

    # Preferisci pfun 74, noto dal catalogo SITUAS; usa il link ufficiale pubblicato nel catalogo.
    entry = next((e for e in candidates if str(e.get("PFUN") or e.get("pfun") or e.get("P_FUN") or e.get("p_fun") or "") == "74"), None)
    if entry is None and candidates:
        entry = candidates[0]
    if entry is None:
        raise SystemExit("SITUAS Comuni - Dimensione report not found")

    link = None
    for key, value in entry.items():
        if "spool" in key.lower() and "count" not in key.lower() and isinstance(value, str) and value.startswith("http"):
            link = value
            break
    if not link:
        print("No SPOOL link found in candidate keys:", list(entry))
        raise SystemExit("SITUAS spool link not found")
    print("SPOOL_LINK", link)
    status, content_type, body = request(link, accept="application/json", headers={"Referer": "https://situas.istat.it/web/"})
    print(f"SITUAS report status={status} type={content_type} bytes={len(body)}")
    if status != 200:
        print(body[:4000].decode("utf-8", errors="replace"))
        raise SystemExit("SITUAS report failed")
    report = json.loads(body.decode("utf-8", errors="replace"), strict=False)
    rows = report.get("resultset") or report.get("items") or []
    print(f"SITUAS report rows={len(rows)}")
    found: dict[str, dict] = {}
    for row in rows:
        code = str(
            row.get("PRO_COM_T")
            or row.get("PRO_COM")
            or row.get("COD_ISTAT")
            or row.get("CODICE_ISTAT")
            or ""
        ).zfill(6)
        if code in TOWNS:
            found[code] = row
            print("SURFACE", code, TOWNS[code], json.dumps(row, ensure_ascii=False, sort_keys=True))
    print(f"COVERAGE municipal surface: {len(found)}/7; missing={[TOWNS[c] for c in TOWNS if c not in found]}")


if __name__ == "__main__":
    probe_istat()
    probe_situas()
