#!/usr/bin/env python3
"""Sostituisce le percentuali FTTH dello shard AgID con il CSV primario AGCOM.

Il CSV primario è già stato acquisito da ``audit_agcom_primary.py`` e conservato
nello snapshot. Non vengono effettuate stime: sono utilizzate le percentuali
pubblicate direttamente da AGCOM per ciascun Comune.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_agid_indicators as base  # noqa: E402
import audit_agcom_primary as primary  # noqa: E402


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise base.DataError(f"{label}: valore numerico mancante")
    result = float(value)
    if not math.isfinite(result):
        raise base.DataError(f"{label}: valore non finito")
    return result


def weighted_percentage(snapshot_rows, key):
    numerator = 0.0
    denominator = 0.0
    for town in snapshot_rows:
        source = town.get("agcom", {}).get("primaryOfficialCsv")
        if not isinstance(source, dict):
            raise base.DataError(f"AGCOM primario assente per {town.get('code')}")
        households = number(source.get("famiglie_residenti"), f"AGCOM {town.get('code')} famiglie residenti")
        percentage = number(source.get(key), f"AGCOM {town.get('code')} {key}")
        if households < 0 or not 0 <= percentage <= 100:
            raise base.DataError(f"AGCOM {town.get('code')}: valore percentuale fuori intervallo")
        numerator += households * percentage
        denominator += households
    if denominator <= 0:
        raise base.DataError("AGCOM: denominatore famiglie residenti nullo")
    return numerator / denominator


def update_metric(data, snapshot, metric_key, source_key, label):
    metric = data.get("metrics", {}).get(metric_key)
    if not isinstance(metric, dict):
        raise base.DataError(f"Indicatore {metric_key} mancante")
    snap_by_code = {str(t.get("code")): t for t in snapshot.get("towns", [])}
    for row in metric.get("rows", []):
        code = str(row.get("code"))
        source = snap_by_code.get(code, {}).get("agcom", {}).get("primaryOfficialCsv")
        if not isinstance(source, dict):
            raise base.DataError(f"AGCOM primario assente per {code}")
        value = number(source.get(source_key), f"AGCOM {code} {source_key}")
        if not 0 <= value <= 100:
            raise base.DataError(f"AGCOM {code}: percentuale fuori intervallo")
        row["value"] = value
        row["formatted"] = base._format_percent(value)
        row["benchmarkValue"] = value
        agcom_snapshot = snap_by_code[code].setdefault("agcom", {})
        if source_key == "copertura_ftth_desi_pct":
            agcom_snapshot["ftthDesiCoveragePercent"] = value
        else:
            agcom_snapshot["ftthWithin20mCoveragePercent"] = value

    aggregate = weighted_percentage(snapshot.get("towns", []), source_key)
    metric["aggregate"] = {
        "value": aggregate,
        "label": "Media ponderata Versilia",
        "note": "Media delle percentuali comunali AGCOM, ponderata per le famiglie residenti del CSV primario.",
    }
    metric["meta"]["source"] = "AGCOM — Broadband Map, reportistica comunale"
    metric["meta"]["year"] = "31 dicembre 2025"
    metric["sourceUrl"] = primary.AI_READY_PAGE
    metric["method"] = {
        "type": "Dato ufficiale; aggregato elaborato dall'Osservatorio",
        "formula": f"{label} comunale pubblicata da AGCOM; media Versilia ponderata per famiglie residenti AGCOM",
        "caveat": "La copertura descrive la disponibilità dichiarata della rete, non il numero di abbonamenti, la velocità effettiva o la certezza di attivazione per ogni singolo civico.",
        "coverage": "7/7",
    }


def apply(data, snapshot):
    update_metric(data, snapshot, "ftthCoverageDesi", "copertura_ftth_desi_pct", "Copertura FTTH DESI")
    update_metric(data, snapshot, "ftthCoverage20m", "copertura_ftth_20m_pct", "Copertura FTTH entro 20 metri")
    snapshot["agcomPrimarySource"] = {
        "aiReadyPage": primary.AI_READY_PAGE,
        "officialCsvUrl": snapshot.get("agcomAudit", {}).get("officialCsvUrl"),
        "period": "31/12/2025",
        "role": "Fonte primaria utilizzata per percentuali e conteggi FTTH",
    }
    return data, snapshot


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--snapshot", type=Path, default=base.SNAPSHOT)
    args = parser.parse_args(argv)
    data = base._json_load(args.site_data)
    snapshot = base._json_load(args.snapshot)
    data, snapshot = apply(data, snapshot)
    base._json_write(args.site_data, data)
    base._json_write(args.snapshot, snapshot)
    print(json.dumps({
        "status": "ok",
        "source": snapshot["agcomPrimarySource"],
        "ftthCoverageDesi": {row["town"]: row["value"] for row in data["metrics"]["ftthCoverageDesi"]["rows"]},
        "ftthCoverage20m": {row["town"]: row["value"] for row in data["metrics"]["ftthCoverage20m"]["rows"]},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except base.DataError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        raise SystemExit(2)
