#!/usr/bin/env python3
"""Acquire official ARS history for the seven legacy health indicators in A3.5.

This script is acquisition-only: it downloads the official ARS export ZIPs,
selects the total-sex / total-stratum municipal series, validates the latest
point against the canonical catalog, and writes a frozen JSON snapshot.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
DEFAULT_OUTPUT = ROOT / "data" / "source-snapshots" / "ars-a3-5-legacy-history.json"

TOWNS = {
    "46005": "Camaiore",
    "46013": "Forte dei Marmi",
    "46018": "Massarosa",
    "46024": "Pietrasanta",
    "46028": "Seravezza",
    "46030": "Stazzema",
    "46033": "Viareggio",
    "202M": "Versilia",
}
SPECS = {
    275: {"key": "chronicTotal"},
    270: {"key": "dementia"},
    271: {"key": "diabetes"},
    260: {"key": "elderlyHomeCare"},
    1657: {"key": "emergencyAccess"},
    1332: {"key": "hospitalizedAll"},
    1438: {"key": "mortalityAll"},
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_num(value: Any, *, integer: bool = False) -> float | int | None:
    text = str(value or "").strip()
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    result = float(text)
    return int(result) if integer else result


def download_csv(indicator_id: int) -> bytes:
    url = f"https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore={indicator_id}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OsservatorioVersilia-A3.5/1.0",
            "Accept-Language": "it-IT,it;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = archive.namelist()
            csv_name = next((name for name in names if name.lower().endswith(".csv")), None)
            if csv_name:
                return archive.read(csv_name)
            nested = next((name for name in names if name.lower().endswith(".zip")), None)
            if nested:
                with zipfile.ZipFile(io.BytesIO(archive.read(nested))) as inner:
                    csv_name = next(name for name in inner.namelist() if name.lower().endswith(".csv"))
                    return inner.read(csv_name)
    except zipfile.BadZipFile:
        pass
    raise RuntimeError(f"ARS {indicator_id}: export ZIP/CSV non leggibile")


def _norm_period(value: Any) -> str:
    return str(value or "").strip().replace("–", "-").replace("—", "-")


def _period_key(value: str) -> tuple[int, str]:
    head = value.split("-", 1)[0]
    return (int(head), value)


def _is_total(value: Any) -> bool:
    return str(value or "").strip().casefold() in {"", "totale", "total"}


def _metric_rows(metric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("Metrica senza rows")
    result = {str(row["town"]): row for row in rows if isinstance(row, dict) and row.get("town")}
    if len(result) != 7:
        raise RuntimeError("Perimetro comunale catalogo non 7/7")
    return result


def acquire_indicator(indicator_id: int, metric: dict[str, Any]) -> dict[str, Any]:
    raw = download_csv(indicator_id)
    sha = hashlib.sha256(raw).hexdigest()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required = {
        "id_indicatore", "anno", "codice_geografia", "geografia",
        "den", "num", "misura_grezza", "misura_standardizzata",
        "liminf", "limsup", "sesso", "strato1", "strato2",
    }
    if not required.issubset(reader.fieldnames or []):
        raise RuntimeError(f"ARS {indicator_id}: schema inatteso {reader.fieldnames}")

    selected: list[dict[str, Any]] = []
    for row in reader:
        if str(row.get("id_indicatore") or "").strip() != str(indicator_id):
            continue
        code = str(row.get("codice_geografia") or "").strip()
        if code not in TOWNS:
            continue
        if not _is_total(row.get("sesso")):
            continue
        if not _is_total(row.get("strato1")) or not _is_total(row.get("strato2")):
            continue
        standardized = parse_num(row.get("misura_standardizzata"))
        raw_measure = parse_num(row.get("misura_grezza"))
        if standardized is None and raw_measure is None:
            continue
        selected.append(
            {
                "period": _norm_period(row.get("anno")),
                "geoCode": code,
                "geography": TOWNS[code],
                "den": parse_num(row.get("den"), integer=True),
                "num": parse_num(row.get("num"), integer=True),
                "raw": raw_measure,
                "standardized": standardized,
                "ci95Low": parse_num(row.get("liminf")),
                "ci95High": parse_num(row.get("limsup")),
            }
        )

    if not selected:
        raise RuntimeError(f"ARS {indicator_id}: nessuna riga totale per il perimetro atteso")

    periods_by_geo = []
    for geography in TOWNS.values():
        periods = {item["period"] for item in selected if item["geography"] == geography}
        if not periods:
            raise RuntimeError(f"ARS {indicator_id}: nessuna serie per {geography}")
        periods_by_geo.append(periods)
    periods = sorted(set.intersection(*periods_by_geo), key=_period_key)
    if len(periods) < 2:
        raise RuntimeError(f"ARS {indicator_id}: storico comune insufficiente {periods}")

    series: dict[str, list[dict[str, Any]]] = {}
    for geography in TOWNS.values():
        by_period = {
            item["period"]: item
            for item in selected
            if item["geography"] == geography and item["period"] in periods
        }
        if set(by_period) != set(periods):
            raise RuntimeError(f"ARS {indicator_id}: serie incompleta {geography}")
        series[geography] = [by_period[period] for period in periods]

    meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
    expected_period = _norm_period(meta.get("year"))
    if expected_period not in periods:
        raise RuntimeError(
            f"ARS {indicator_id}: periodo catalogo {expected_period} assente dalla fonte {periods}"
        )
    expected_index = periods.index(expected_period)
    periods = periods[: expected_index + 1]
    series = {
        geography: values[: expected_index + 1]
        for geography, values in series.items()
    }

    rows = _metric_rows(metric)
    for town, row in rows.items():
        observed = float(row["value"])
        latest = series[town][-1]
        source_value = latest["standardized"]
        if source_value is None:
            source_value = latest["raw"]
        if source_value is None or not math.isclose(observed, float(source_value), rel_tol=0.0, abs_tol=0.055):
            raise RuntimeError(
                f"ARS {indicator_id}/{town}: catalogo {observed} != fonte {source_value}"
            )

    aggregate = metric.get("aggregate")
    if not isinstance(aggregate, dict) or aggregate.get("value") is None:
        raise RuntimeError(f"ARS {indicator_id}: aggregato Versilia mancante")
    latest_versilia = series["Versilia"][-1]
    aggregate_source = latest_versilia["standardized"]
    if aggregate_source is None:
        aggregate_source = latest_versilia["raw"]
    if aggregate_source is None or not math.isclose(
        float(aggregate["value"]), float(aggregate_source), rel_tol=0.0, abs_tol=0.055
    ):
        raise RuntimeError(
            f"ARS {indicator_id}/Versilia: catalogo {aggregate['value']} != fonte {aggregate_source}"
        )

    values: dict[str, list[float]] = {}
    for geography, records in series.items():
        compact: list[float] = []
        for record in records:
            value = record["standardized"]
            if value is None:
                value = record["raw"]
            if value is None:
                raise RuntimeError(f"ARS {indicator_id}/{geography}: misura finale mancante")
            compact.append(float(value))
        values[geography] = compact

    return {
        "indicatorId": indicator_id,
        "exportUrl": f"https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore={indicator_id}",
        "periods": periods,
        "values": values,
        "sourceFile": {
            "sha256": sha,
            "bytes": len(raw),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    site = load(SITE_PATH)
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")

    out: dict[str, Any] = {
        "schemaVersion": 1,
        "publisher": "ARS Toscana",
        "scope": "A3.5 lotto 7 · serie storiche di 7 indicatori Salute legacy · 7 Comuni + Zona Versilia",
        "retrievedBy": "scripts/acquire_a3_5_ars_legacy_history.py",
        "indicators": {},
    }
    for indicator_id, spec in SPECS.items():
        key = spec["key"]
        metric = metrics.get(key)
        if not isinstance(metric, dict):
            raise RuntimeError(f"Metrica catalogo mancante: {key}")
        item = acquire_indicator(indicator_id, metric)
        out["indicators"][key] = item
        print(
            f"ARS {indicator_id} {key}: {len(item['periods'])} periodi "
            f"{item['periods'][0]} → {item['periods'][-1]}"
        )

    save(Path(args.output), out)
    print(f"Snapshot A3.5 ARS scritto: {args.output}")


if __name__ == "__main__":
    main()
