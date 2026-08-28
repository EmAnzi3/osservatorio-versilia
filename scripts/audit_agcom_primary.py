#!/usr/bin/env python3
"""Verifica i conteggi assoluti FTTH sul dataset comunale primario AGCOM.

Il controllo usa direttamente l'endpoint machine-readable ufficiale ArcGIS.
La mappa AGCOM resta il riferimento pubblico; nessun conteggio viene
ricostruito dalle percentuali.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_agid_indicators as base  # noqa: E402

PUBLIC_MAP_URL = "https://maps.agcom.it/"
# Alias di compatibilità per i materializzatori storici: il nome resta disponibile,
# ma punta alla mappa pubblica AGCOM corrente e non alle vecchie pagine dismesse.
AI_READY_PAGE = PUBLIC_MAP_URL
OFFICIAL_CSV_URL = (
    "https://geo.agcom.it/arcgis/sharing/rest/content/items/"
    "25830559c5784c1eb5eb1cf748889f4c/data"
)


def fetch_bytes(url: str, accept: str = "*/*") -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": base.USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def discover_csv_url() -> tuple[str, str]:
    """Restituisce l'endpoint ufficiale stabile senza interrogare pagine dismesse."""
    return OFFICIAL_CSV_URL, "official_arcgis_item_data"


def parse_int(value: str) -> int | None:
    raw = (value or "").strip()
    if not raw:
        return None
    raw = raw.replace(".", "").replace(",", "")
    try:
        return int(float(raw))
    except ValueError:
        return None


def parse_pct(value: str) -> float | None:
    raw = (value or "").strip().rstrip("%").replace(",", ".")
    if not raw:
        return None
    try:
        result = float(raw)
        return result if math.isfinite(result) else None
    except ValueError:
        return None


def parse_csv(body: bytes) -> dict[str, dict[str, Any]]:
    text = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = body.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise base.DataError("CSV AGCOM: encoding non riconosciuto")
    reader = csv.reader(io.StringIO(text), delimiter=";")
    try:
        header = next(reader)
    except StopIteration as exc:
        raise base.DataError("CSV AGCOM vuoto") from exc
    if len(header) < 19:
        raise base.DataError(f"CSV AGCOM: colonne inattese ({len(header)})")
    result: dict[str, dict[str, Any]] = {}
    for raw in reader:
        if len(raw) < 19:
            raw += [""] * (19 - len(raw))
        code = raw[3].strip().zfill(6)
        if not code.strip("0"):
            continue
        result[code] = {
            "comune": raw[2].strip(),
            "famiglie_residenti": parse_int(raw[13]),
            "famiglie_ftth": parse_int(raw[14]),
            "famiglie_ftth_20m": parse_int(raw[15]),
            "copertura_ftth_desi_pct": parse_pct(raw[16]),
            "copertura_ftth_20m_pct": parse_pct(raw[18]),
            "raw": {
                "famiglie_residenti": raw[13],
                "famiglie_ftth": raw[14],
                "famiglie_ftth_20m": raw[15],
                "copertura_ftth_desi_pct": raw[16],
                "copertura_ftth_20m_pct": raw[18],
            },
        }
    return result


def population_by_code(data: dict[str, Any]) -> dict[str, float]:
    metric = data.get("metrics", {}).get("population", {})
    result = {}
    for row in metric.get("rows", []):
        value = row.get("value")
        if isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) > 0:
            result[str(row.get("code"))] = float(value)
    return result


def plausibility(population: float | None, households: int | None, reached: int | None) -> tuple[bool, str]:
    if households is None or households <= 0:
        return False, "famiglie residenti assenti o non positive"
    if reached is None:
        return False, "famiglie FTTH mancanti"
    if reached < 0 or reached > households:
        return False, "famiglie FTTH fuori intervallo rispetto alle famiglie residenti"
    if population and population > 0:
        implied = population / households
        if implied > 5:
            return False, f"{implied:.1f} residenti per famiglia impliciti (>5)"
        return True, f"{implied:.2f} residenti per famiglia impliciti"
    return True, "conteggi internamente coerenti; controllo demografico non disponibile"


def audit(data: dict[str, Any], snapshot: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    csv_url, discovery = discover_csv_url()
    try:
        body = fetch_bytes(csv_url, "text/csv,application/octet-stream,*/*")
        rows = parse_csv(body)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, base.DataError) as exc:
        raise base.DataError(f"CSV primario AGCOM non acquisibile: {exc}") from exc

    population = population_by_code(data)
    town_names = {str(t.get("code")): t.get("name") for t in data.get("towns", [])}
    invalid: list[str] = []
    report_rows: list[dict[str, Any]] = []
    snapshot_by_code = {str(t.get("code")): t for t in snapshot.get("towns", [])}

    for code, town_name in town_names.items():
        source = rows.get(code)
        if source is None:
            invalid.append(code)
            report_rows.append({"code": code, "town": town_name, "valid": False, "reason": "Comune assente nel CSV primario", "official": None})
            continue
        valid, reason = plausibility(population.get(code), source["famiglie_residenti"], source["famiglie_ftth"])
        if not valid:
            invalid.append(code)
        target = snapshot_by_code.get(code)
        if target is not None:
            agcom = target.setdefault("agcom", {})
            agcom["primaryOfficialCsv"] = source
            agcom["absoluteCountsValid"] = valid
            agcom["absoluteCountsValidation"] = reason
            if valid:
                agcom["residentHouseholds"] = source["famiglie_residenti"]
                agcom["ftthHouseholds"] = source["famiglie_ftth"]
                agcom["ftthHouseholdsWithin20m"] = source["famiglie_ftth_20m"]
            else:
                agcom["ftthHouseholds"] = None
        report_rows.append({"code": code, "town": town_name, "valid": valid, "reason": reason, "official": source})

    snapshot["agcomAudit"] = {
        "sourceType": "primary_official_csv",
        "publicMapUrl": PUBLIC_MAP_URL,
        "officialCsvUrl": csv_url,
        "discovery": discovery,
        "rowCount": len(rows),
        "invalidAbsoluteTownCodes": sorted(invalid),
        "invalidAbsoluteTowns": [town_names[code] for code in sorted(invalid)],
        "rows": report_rows,
        "rule": (
            "Nessun conteggio assoluto viene ricostruito dalle percentuali. I valori sono letti dal dataset comunale AGCOM; "
            "il controllo demografico segnala valori palesemente incompatibili con la popolazione residente."
        ),
    }
    return snapshot, csv_url, discovery


def write_report(snapshot: dict[str, Any], path: Path) -> None:
    audit = snapshot["agcomAudit"]
    lines = [
        "# Audit primario AGCOM — conteggi FTTH",
        "",
        f"- Mappa pubblica: {audit['publicMapUrl']}",
        f"- Dataset acquisito: {audit['officialCsvUrl']}",
        f"- Accesso: `{audit['discovery']}`",
        f"- Righe CSV: **{audit['rowCount']}**",
        f"- Comuni non validati: **{', '.join(audit['invalidAbsoluteTowns']) or 'nessuno'}**",
        "",
        "| Comune | Famiglie residenti | Famiglie FTTH | FTTH 20 m | Copertura DESI | Esito | Motivo |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for item in audit["rows"]:
        source = item.get("official") or {}
        lines.append(
            f"| {item['town']} | {source.get('famiglie_residenti', 'n.d.')} | {source.get('famiglie_ftth', 'n.d.')} | "
            f"{source.get('famiglie_ftth_20m', 'n.d.')} | {source.get('copertura_ftth_desi_pct', 'n.d.')}% | "
            f"{'OK' if item['valid'] else 'NON VALIDATO'} | {item['reason']} |"
        )
    lines.extend(["", "> I valori non validati restano `n.d.`. Nessuna stima viene effettuata.", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--snapshot", type=Path, default=base.SNAPSHOT)
    parser.add_argument("--report-md", type=Path, default=base.ROOT / "reports" / "previews" / "imprese-banda-larga" / "agcom-primary-audit.md")
    args = parser.parse_args(argv)
    data = base._json_load(args.site_data)
    snapshot = base._json_load(args.snapshot)
    snapshot, csv_url, discovery = audit(data, snapshot)
    base._json_write(args.snapshot, snapshot)
    write_report(snapshot, args.report_md)
    print(json.dumps({
        "status": "ok",
        "officialCsvUrl": csv_url,
        "publicMapUrl": PUBLIC_MAP_URL,
        "discovery": discovery,
        "invalidTowns": snapshot["agcomAudit"]["invalidAbsoluteTowns"],
        "report": str(args.report_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except base.DataError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        raise SystemExit(2)
