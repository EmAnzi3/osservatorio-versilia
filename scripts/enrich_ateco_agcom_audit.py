#!/usr/bin/env python3
"""Integra il dettaglio ATECO 2023 e verifica i conteggi assoluti AGCOM.

Il dettaglio ATECO resta un dataset strutturale e non incrementa il numero di
indicatori. L'audit AGCOM non stima valori: segnala conteggi assoluti implausibili
ed effettua un controllo diretto sul CSV ufficiale AGCOM quando raggiungibile.
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

AGCOM_CSV_URL = (
    "https://geo.agcom.it/arcgis/sharing/rest/content/items/"
    "6c0b48a9a06c44059656b987d85acb63/data"
)

ATECO_LABELS = {
    "01": "Agricoltura e produzione animale", "02": "Silvicoltura", "03": "Pesca e acquacoltura",
    "05": "Estrazione carbone", "06": "Estrazione petrolio e gas", "07": "Estrazione minerali metalliferi",
    "08": "Altre attività estrattive", "09": "Servizi di supporto all'estrazione", "10": "Industrie alimentari",
    "11": "Industria delle bevande", "12": "Industria del tabacco", "13": "Industrie tessili",
    "14": "Abbigliamento", "15": "Pelli e calzature", "16": "Industria del legno", "17": "Carta",
    "18": "Stampa e supporti registrati", "19": "Coke e prodotti petroliferi", "20": "Prodotti chimici",
    "21": "Prodotti farmaceutici", "22": "Gomma e plastica", "23": "Minerali non metalliferi",
    "24": "Metallurgia", "25": "Prodotti in metallo", "26": "Computer, elettronica e ottica",
    "27": "Apparecchiature elettriche", "28": "Macchinari", "29": "Autoveicoli", "30": "Altri mezzi di trasporto",
    "31": "Mobili", "32": "Altre industrie manifatturiere", "33": "Riparazione e installazione macchinari",
    "35": "Energia elettrica, gas e vapore", "36": "Raccolta e trattamento acque", "37": "Reti fognarie",
    "38": "Rifiuti", "39": "Risanamento e bonifica", "41": "Costruzione di edifici", "42": "Ingegneria civile",
    "43": "Lavori di costruzione specializzati", "45": "Commercio e riparazione autoveicoli",
    "46": "Commercio all'ingrosso", "47": "Commercio al dettaglio", "49": "Trasporto terrestre",
    "50": "Trasporto marittimo", "51": "Trasporto aereo", "52": "Magazzinaggio e supporto ai trasporti",
    "53": "Servizi postali e corriere", "55": "Alloggio", "56": "Ristorazione", "58": "Editoria",
    "59": "Cinema, video e musica", "60": "Radio e TV", "61": "Telecomunicazioni", "62": "Informatica e software",
    "63": "Servizi d'informazione", "64": "Servizi finanziari", "65": "Assicurazioni e fondi pensione",
    "66": "Servizi finanziari ausiliari", "68": "Attività immobiliari", "69": "Attività legali e contabili",
    "70": "Direzione aziendale e consulenza", "71": "Studi tecnici e architettura", "72": "Ricerca e sviluppo",
    "73": "Pubblicità e ricerche di mercato", "74": "Altre attività professionali", "75": "Veterinaria",
    "77": "Noleggio e leasing", "78": "Ricerca e selezione del personale", "79": "Agenzie di viaggio",
    "80": "Vigilanza e investigazioni", "81": "Servizi per edifici e paesaggio", "82": "Supporto d'ufficio e altri servizi alle imprese",
    "84": "Amministrazione pubblica e difesa", "85": "Istruzione", "86": "Assistenza sanitaria",
    "87": "Assistenza sociale residenziale", "88": "Assistenza sociale non residenziale",
    "90": "Attività creative e artistiche", "91": "Biblioteche e musei", "92": "Lotterie e scommesse",
    "93": "Attività sportive e intrattenimento", "94": "Organizzazioni associative",
    "95": "Riparazione computer e beni personali", "96": "Altri servizi personali", "97": "Servizi domestici",
    "98": "Produzione di beni per uso proprio", "99": "Organismi extraterritoriali",
}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _parse_int(value: str) -> int | None:
    value = (value or "").strip().replace(".", "").replace(",", "")
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _parse_pct(value: str) -> float | None:
    value = (value or "").strip().rstrip("%").replace(",", ".")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fetch_official_agcom_rows() -> tuple[dict[str, dict[str, Any]], str]:
    request = urllib.request.Request(AGCOM_CSV_URL, headers={"User-Agent": base.USER_AGENT, "Accept": "text/csv,*/*"})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {}, str(exc)
    try:
        text = body.decode("cp1252")
    except UnicodeDecodeError:
        text = body.decode("latin-1", errors="replace")
    reader = csv.reader(io.StringIO(text), delimiter=";")
    try:
        header = next(reader)
    except StopIteration:
        return {}, "CSV ufficiale vuoto"
    rows: dict[str, dict[str, Any]] = {}
    for raw in reader:
        if len(raw) < 19:
            raw += [""] * (19 - len(raw))
        code = raw[3].strip().zfill(6)
        if not code.strip("0"):
            continue
        rows[code] = {
            "raw": {"famiglie_residenti": raw[13], "famiglie_ftth": raw[14], "famiglie_ftth_20m": raw[15],
                    "copertura_ftth_desi_pct": raw[16], "copertura_ftth_20m_pct": raw[18]},
            "famiglie_residenti": _parse_int(raw[13]),
            "famiglie_ftth": _parse_int(raw[14]),
            "famiglie_ftth_20m": _parse_int(raw[15]),
            "copertura_ftth_desi_pct": _parse_pct(raw[16]),
            "copertura_ftth_20m_pct": _parse_pct(raw[18]),
        }
    return rows, f"header_columns={len(header)}; rows={len(rows)}"


def _metric_row(data: dict[str, Any], key: str, code: str) -> dict[str, Any] | None:
    metric = data.get("metrics", {}).get(key, {})
    return next((row for row in metric.get("rows", []) if row.get("code") == code), None)


def _is_household_count_plausible(data: dict[str, Any], code: str, households: Any) -> tuple[bool, str]:
    count = _number(households)
    population_row = _metric_row(data, "population", code)
    if count is None or count <= 0:
        return False, "conteggio assente o non positivo"
    if not population_row:
        return True, "controllo demografico non disponibile"
    population = _number(population_row.get("value"))
    if not population or population <= 0:
        return True, "controllo demografico non disponibile"
    ratio = population / count
    if ratio > 5:
        return False, f"{ratio:.1f} residenti per famiglia impliciti (>5)"
    return True, f"{ratio:.2f} residenti per famiglia impliciti"


def build_ateco(data: dict[str, Any], asia: dict[str, dict[str, Any]]) -> dict[str, Any]:
    towns = base._town_rows(data)
    sector_codes: set[str] = set()
    for town in towns:
        code = town["code"]
        shard = asia[code]
        detail_by_year = shard.get("ateco_dettaglio")
        year_detail = detail_by_year.get("2023") if isinstance(detail_by_year, dict) else None
        if not isinstance(year_detail, dict):
            raise base.DataError(f"ASIA {code}: dettaglio ATECO 2023 mancante")
        sectors = []
        total_ul = float(shard["kpi"]["ul_totali"])
        total_workers = float(shard["kpi"]["addetti_totali"])
        for sector_code, size_rows in year_detail.items():
            if sector_code == "0010" or not isinstance(size_rows, dict):
                continue
            total = size_rows.get("TOTAL")
            if not isinstance(total, dict):
                continue
            ul = _number(total.get("ul"))
            workers = _number(total.get("addetti"))
            if ul is None and workers is None:
                continue
            ul = ul or 0.0
            workers = workers or 0.0
            if ul <= 0 and workers <= 0:
                continue
            sector_codes.add(sector_code)
            sectors.append({
                "code": sector_code,
                "label": ATECO_LABELS.get(sector_code, f"ATECO {sector_code}"),
                "localUnits": ul,
                "workers": workers,
                "localUnitShare": (ul / total_ul * 100.0) if total_ul else None,
                "workerShare": (workers / total_workers * 100.0) if total_workers else None,
            })
        sectors.sort(key=lambda item: (-item["workers"], -item["localUnits"], item["code"]))
        economy = data.setdefault("details", {}).setdefault(code, {}).setdefault("economy", {})
        economy["atecoYear"] = 2023
        economy["atecoSource"] = "ISTAT ASIA-UL"
        economy["atecoSourceUrl"] = base.ASIA_SOURCE_URL
        economy["atecoSectors"] = sectors
        economy["topSectors"] = sectors[:10]
        economy["topSectorsByUnits"] = sorted(sectors, key=lambda item: (-item["localUnits"], -item["workers"], item["code"]))[:10]

    data["economyAteco"] = {
        "year": 2023,
        "classification": "ATECO 2007 / NACE Rev.2 — divisioni a 2 cifre",
        "source": "ISTAT ASIA-UL",
        "sourceUrl": base.ASIA_SOURCE_URL,
        "coverage": "7/7",
        "sectorCodes": sorted(sector_codes),
        "labels": {code: ATECO_LABELS.get(code, f"ATECO {code}") for code in sorted(sector_codes)},
        "note": "Unità locali e addetti medi annui sono attribuiti al luogo di lavoro. Le divisioni con valore nullo non sono mostrate.",
    }
    return data


def audit_agcom(data: dict[str, Any], snapshot: dict[str, Any], agcom: dict[str, dict[str, Any]]) -> dict[str, Any]:
    official, official_status = fetch_official_agcom_rows()
    invalid_codes: list[str] = []
    rows = []
    town_by_code = {town["code"]: town["name"] for town in data.get("towns", [])}
    snapshot_by_code = {town["code"]: town for town in snapshot.get("towns", [])}

    for code, town_name in town_by_code.items():
        shard_kpi = agcom[code].get("kpi", {})
        direct = official.get(code)
        selected = direct if direct else shard_kpi
        households = selected.get("famiglie_residenti")
        plausible, reason = _is_household_count_plausible(data, code, households)
        reached = selected.get("famiglie_ftth")
        if reached is None:
            plausible = False
            reason = f"{reason}; famiglie FTTH mancanti"
        if not plausible:
            invalid_codes.append(code)
        snap_town = snapshot_by_code.get(code)
        if snap_town:
            ag = snap_town.setdefault("agcom", {})
            ag["auditRawShard"] = {
                "residentHouseholds": shard_kpi.get("famiglie_residenti"),
                "ftthHouseholds": shard_kpi.get("famiglie_ftth"),
                "ftthHouseholdsWithin20m": shard_kpi.get("famiglie_ftth_20m"),
            }
            if direct:
                ag["auditOfficialCsv"] = direct
            ag["absoluteCountsValid"] = plausible
            ag["absoluteCountsValidation"] = reason
            if direct and plausible:
                ag["residentHouseholds"] = direct.get("famiglie_residenti")
                ag["ftthHouseholds"] = direct.get("famiglie_ftth")
                ag["ftthHouseholdsWithin20m"] = direct.get("famiglie_ftth_20m")
        rows.append({"code": code, "town": town_name, "valid": plausible, "reason": reason,
                     "shard": {"resident": shard_kpi.get("famiglie_residenti"), "ftth": shard_kpi.get("famiglie_ftth")},
                     "official": direct})

    snapshot["agcomAudit"] = {
        "officialCsvUrl": AGCOM_CSV_URL,
        "officialCsvStatus": official_status,
        "invalidAbsoluteTownCodes": sorted(invalid_codes),
        "invalidAbsoluteTowns": [town_by_code[code] for code in sorted(invalid_codes)],
        "rows": rows,
        "rule": "I conteggi assoluti non sono stimati. Un controllo demografico grossolano segnala valori incompatibili; i dati percentuali restano indipendenti.",
    }
    return snapshot


def write_report(data: dict[str, Any], snapshot: dict[str, Any], path: Path) -> None:
    audit = snapshot.get("agcomAudit", {})
    lines = ["# Audit ATECO e AGCOM", "", "## Dettaglio ATECO", "",
             f"- Anno: **{data['economyAteco']['year']}**",
             f"- Copertura: **{data['economyAteco']['coverage']}**",
             f"- Divisioni presenti almeno in un Comune: **{len(data['economyAteco']['sectorCodes'])}**", ""]
    for town in data.get("towns", []):
        sectors = data["details"][town["code"]]["economy"]["atecoSectors"]
        top = sectors[0] if sectors else None
        lines.append(f"- **{town['name']}**: {len(sectors)} divisioni con valori; primo per addetti: {top['code']} — {top['label']} ({top['workers']:.2f})" if top else f"- **{town['name']}**: nessun settore")
    lines.extend(["", "## Audit conteggi AGCOM", "", f"- CSV ufficiale: `{audit.get('officialCsvStatus', '')}`",
                  f"- Comuni con conteggi assoluti non validati: **{', '.join(audit.get('invalidAbsoluteTowns', [])) or 'nessuno'}**", "",
                  "| Comune | Shard residenti | Shard FTTH | Esito | Motivo |", "|---|---:|---:|---|---|"])
    for item in audit.get("rows", []):
        lines.append(f"| {item['town']} | {item['shard']['resident']} | {item['shard']['ftth']} | {'OK' if item['valid'] else 'NON VALIDATO'} | {item['reason']} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--snapshot", type=Path, default=base.SNAPSHOT)
    parser.add_argument("--report-md", type=Path, default=base.ROOT / "reports" / "previews" / "imprese-banda-larga" / "ateco-agcom-audit.md")
    args = parser.parse_args(argv)

    data = base._json_load(args.site_data)
    snapshot = base._json_load(args.snapshot)
    towns = base._town_rows(data)
    asia, agcom, _ = base.load_source_shards([town["code"] for town in towns], None)
    build_ateco(data, asia)
    audit_agcom(data, snapshot, agcom)
    base._json_write(args.site_data, data)
    base._json_write(args.snapshot, snapshot)
    write_report(data, snapshot, args.report_md)
    print(json.dumps({"status": "ok", "atecoCoverage": data["economyAteco"]["coverage"],
                      "atecoSectors": len(data["economyAteco"]["sectorCodes"]),
                      "invalidAgcomAbsoluteTowns": snapshot["agcomAudit"]["invalidAbsoluteTowns"],
                      "report": str(args.report_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except base.DataError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        raise SystemExit(2)
