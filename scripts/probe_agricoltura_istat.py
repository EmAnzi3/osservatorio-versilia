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
    merged = {"User-Agent": "OsservatorioVersilia-agriculture-probe/4.0"}
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


def decode_json_bytes(body: bytes):
    value = json.loads(body.decode("utf-8", errors="replace"), strict=False)
    for _ in range(4):
        if not isinstance(value, str):
            break
        value = json.loads(value, strict=False)
    return value


def istat_csv(flow: str, key: str, *, quiet: bool = False) -> tuple[str, list[dict[str, str]]]:
    url = f"{ISTAT_BASE}/{flow}/{key}/IT1?startPeriod=2020&endPeriod=2020"
    status, content_type, body = request(url, accept=CSV_ACCEPT)
    print(f"\n=== ISTAT {flow} ===")
    print(f"url={url}\nstatus={status} type={content_type} bytes={len(body)}")
    if status != 200:
        print(body[:4000].decode("utf-8", errors="replace"))
        raise SystemExit(f"ISTAT query failed: {flow} {status}")
    rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
    if not quiet:
        for row in rows:
            print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    return url, rows


def print_coverage(label: str, rows: list[dict[str, str]], *, crop: str | None = None) -> None:
    present, zeros = set(), set()
    for row in rows:
        code = row.get("REF_AREA")
        if code not in TOWNS or (crop is not None and row.get("TYPE_OF_CROP") != crop):
            continue
        present.add(code)
        try:
            if float(row.get("OBS_VALUE", "nan")) == 0:
                zeros.add(code)
        except ValueError:
            pass
    print(
        f"COVERAGE {label}: {len(present)}/7; "
        f"missing={[TOWNS[c] for c in TOWNS if c not in present]}; "
        f"explicit_zero={[TOWNS[c] for c in TOWNS if c in zeros]}"
    )


def probe_istat() -> None:
    areas = "+".join(TOWNS)
    _, surf = istat_csv("DF_DCAT_CENSAGRIC2020_SURF_ALL", f"A.{areas}.HO+ARU+FUAA")
    for dtype in ("HO", "ARU", "FUAA"):
        print_coverage(dtype, [r for r in surf if r.get("DATA_TYPE") == dtype])

    _, crop_catalog = istat_csv("DF_DCAT_CENSAGRIC2020_UA_CROPS_2", "A.046005.ARU..TOT", quiet=True)
    crop_codes = sorted({r.get("TYPE_OF_CROP", "") for r in crop_catalog if r.get("TYPE_OF_CROP")})
    print("LOCALIZED CROP CODES MATCH OLI:", [c for c in crop_codes if "OLI" in c.upper()])
    query_codes = ["ALL", "ARLAND", "VINEY", "PGRAPM", "OLIVOOILTR", "OLIVTTR"]
    _, crops = istat_csv(
        "DF_DCAT_CENSAGRIC2020_UA_CROPS_2",
        f"A.{areas}.ARU.{'+'.join(query_codes)}.TOT",
    )
    for crop in query_codes:
        print_coverage(f"localized ARU {crop}", crops, crop=crop)

    _, irrigation = istat_csv("DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS", f"A.{areas}.IA")
    print_coverage("IA", irrigation)


def unwrap_items(value):
    for _ in range(5):
        if isinstance(value, str):
            value = json.loads(value, strict=False)
            continue
        if isinstance(value, dict):
            nested = value.get("items") or value.get("resultset") or value.get("data")
            if nested is not None:
                value = nested
                continue
        break
    return value


def field(entry: dict, *names: str):
    lowered = {str(k).lower(): v for k, v in entry.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def situas_report(date: str) -> list[dict]:
    link = f"https://situas-servizi.istat.it/publish/reportspooljson?pfun=74&pdata={date}"
    status, content_type, body = request(link, accept="application/json", headers={"Referer": "https://situas.istat.it/web/"})
    print(f"\n=== SITUAS Comuni - Dimensione {date} ===\nurl={link}\nstatus={status} type={content_type} bytes={len(body)}")
    if status != 200:
        print(body[:4000].decode("utf-8", errors="replace"))
        raise SystemExit("SITUAS report failed")
    report = unwrap_items(decode_json_bytes(body))
    if isinstance(report, dict):
        report = list(report.values())
    if not isinstance(report, list):
        raise SystemExit(f"Unexpected SITUAS report shape: {type(report).__name__}")
    return [row for row in report if isinstance(row, dict)]


def probe_situas() -> None:
    # Il report 74 è temporale: interrogare la data corrente evita la fotografia
    # censuaria 1951 proposta come primo estremo dal catalogo dei microservizi.
    report = situas_report("26/08/2026")
    found: dict[str, dict] = {}
    for row in report:
        raw_code = field(row, "PRO_COM_T", "PRO_COM", "COD_ISTAT", "CODICE_ISTAT")
        if raw_code is None:
            continue
        code = str(raw_code).strip().replace(".0", "").zfill(6)
        if code in TOWNS:
            found[code] = row
            print("SURFACE", code, TOWNS[code], json.dumps(row, ensure_ascii=False, sort_keys=True))
    print(f"COVERAGE municipal surface: {len(found)}/7; missing={[TOWNS[c] for c in TOWNS if c not in found]}")
    if len(found) < 7:
        raise SystemExit("SITUAS municipal surface coverage incomplete")
    if not all(field(row, "AREA_KMQ") is not None for row in found.values()):
        raise SystemExit("SITUAS current report does not expose AREA_KMQ for all seven towns")


if __name__ == "__main__":
    probe_istat()
    probe_situas()
