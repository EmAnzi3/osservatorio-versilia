#!/usr/bin/env python3
"""Esegue l'integrazione ASIA/AGCOM applicando una policy prudenziale.

AGCOM può pubblicare la percentuale comunale di copertura anche quando il
conteggio assoluto ``famiglie_ftth`` non è valorizzato nello shard normalizzato.
In quel caso non ricostruiamo il conteggio da una percentuale arrotondata:
pubblichiamo soltanto gli indicatori percentuali con copertura 7/7 e conserviamo
il valore nullo nello snapshot della fonte.

Lo script è idempotente: gli indicatori ASIA/FTTH gestiti da questa pipeline
vengono sostituiti, non conteggiati come nuove aggiunte a ogni esecuzione.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_agid_indicators as base  # noqa: E402

PUBLISHED_BROADBAND_KEYS = ["ftthCoverageDesi", "ftthCoverage20m"]
OMITTED_ABSOLUTE_KEYS = ["ftthReachedHouseholds", "ftthUnreachedHouseholds"]
MANAGED_KEYS = set(base.NEW_ECONOMY_KEYS + base.NEW_BROADBAND_KEYS)


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise base.DataError(f"{label}: valore numerico mancante o non valido")
    number = float(value)
    if not math.isfinite(number):
        raise base.DataError(f"{label}: valore non finito")
    return number


def _weighted_official_percentage(
    agcom: dict[str, dict[str, Any]], percentage_key: str
) -> float:
    numerator = 0.0
    denominator = 0.0
    for code, shard in agcom.items():
        kpi = shard.get("kpi")
        if not isinstance(kpi, dict):
            raise base.DataError(f"AGCOM {code}: sezione kpi mancante")
        households = _number(
            kpi.get("famiglie_residenti"), f"AGCOM {code} famiglie_residenti"
        )
        percentage = _number(
            kpi.get(percentage_key), f"AGCOM {code} {percentage_key}"
        )
        if households < 0 or not 0 <= percentage <= 100:
            raise base.DataError(f"AGCOM {code}: valori di copertura fuori intervallo")
        numerator += households * percentage
        denominator += households
    if denominator <= 0:
        raise base.DataError("AGCOM: famiglie residenti complessive nulle")
    return numerator / denominator


def _prepare_for_base(
    agcom: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    """Crea una copia tecnica per il generatore base.

    I conteggi mancanti sono sostituiti soltanto nella copia transitoria per
    consentire al generatore di costruire il resto del dataset. Gli indicatori
    assoluti vengono poi eliminati e lo snapshot viene ripristinato con i valori
    originali, quindi nessuna stima entra nei dati pubblicabili.
    """
    technical = copy.deepcopy(agcom)
    missing_desi_counts: list[str] = []
    missing_20m_counts: list[str] = []

    for code, shard in technical.items():
        period = shard.get("_data_period")
        kpi = shard.get("kpi")
        if period != "31/12/2025":
            raise base.DataError(f"AGCOM {code}: periodo inatteso ({period})")
        if not isinstance(kpi, dict):
            raise base.DataError(f"AGCOM {code}: sezione kpi mancante")

        resident = _number(
            kpi.get("famiglie_residenti"), f"AGCOM {code} famiglie_residenti"
        )
        desi_pct = _number(
            kpi.get("copertura_ftth_desi_pct"),
            f"AGCOM {code} copertura_ftth_desi_pct",
        )
        within_20m_pct = _number(
            kpi.get("copertura_ftth_20m_pct"),
            f"AGCOM {code} copertura_ftth_20m_pct",
        )
        if resident < 0 or not 0 <= desi_pct <= 100 or not 0 <= within_20m_pct <= 100:
            raise base.DataError(f"AGCOM {code}: valori di copertura fuori intervallo")

        if not isinstance(kpi.get("famiglie_ftth"), (int, float)):
            missing_desi_counts.append(code)
            kpi["famiglie_ftth"] = resident * desi_pct / 100.0
        if not isinstance(kpi.get("famiglie_ftth_20m"), (int, float)):
            missing_20m_counts.append(code)
            kpi["famiglie_ftth_20m"] = resident * within_20m_pct / 100.0

    return technical, missing_desi_counts, missing_20m_counts


def expected_metric_count(source_data: dict[str, Any]) -> int:
    """Numero atteso dopo la fase prudenziale, indipendente dalla release di partenza."""
    unmanaged = [key for key in source_data.get("metrics", {}) if key not in MANAGED_KEYS]
    regenerated = base.NEW_ECONOMY_KEYS + PUBLISHED_BROADBAND_KEYS
    return len(unmanaged) + len(regenerated)


def apply_policy(
    source_data: dict[str, Any],
    asia: dict[str, dict[str, Any]],
    agcom: dict[str, dict[str, Any]],
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    technical_agcom, missing_desi, missing_20m = _prepare_for_base(agcom)
    data, snapshot = base.apply_updates(
        source_data, asia, technical_agcom, generated_at
    )

    # I conteggi assoluti non sono pubblicati in questa fase prudenziale; una
    # fase successiva li ripristina dal CSV primario AGCOM quando la copertura
    # validata raggiunge almeno 6/7.
    for key in OMITTED_ABSOLUTE_KEYS:
        data["metrics"].pop(key, None)

    mobility = data["themes"]["mobilita"]
    mobility["metrics"] = [
        key for key in mobility["metrics"] if key not in OMITTED_ABSOLUTE_KEYS
    ]
    for section in mobility.get("sections", []):
        if section.get("key") == "connettivita":
            section["metrics"] = PUBLISHED_BROADBAND_KEYS
            section["description"] = (
                "Copertura comunale della rete fissa FTTH secondo le due metriche "
                "ufficiali AGCOM disponibili per tutti i sette Comuni."
            )

    desi_aggregate = _weighted_official_percentage(
        agcom, "copertura_ftth_desi_pct"
    )
    within_20m_aggregate = _weighted_official_percentage(
        agcom, "copertura_ftth_20m_pct"
    )
    data["metrics"]["ftthCoverageDesi"]["aggregate"] = {
        "value": desi_aggregate,
        "label": "Media ponderata Versilia",
        "note": (
            "Media delle percentuali comunali ufficiali, ponderata per le "
            "famiglie residenti pubblicate da AGCOM."
        ),
    }
    data["metrics"]["ftthCoverageDesi"]["method"]["type"] = (
        "Elaborazione Osservatorio su dati ufficiali"
    )
    data["metrics"]["ftthCoverageDesi"]["method"]["formula"] = (
        "media delle coperture FTTH DESI comunali, ponderata per le famiglie "
        "residenti AGCOM"
    )
    data["metrics"]["ftthCoverage20m"]["aggregate"] = {
        "value": within_20m_aggregate,
        "label": "Media ponderata Versilia",
        "note": (
            "Media delle percentuali comunali ufficiali, ponderata per le "
            "famiglie residenti pubblicate da AGCOM."
        ),
    }
    data["metrics"]["ftthCoverage20m"]["method"]["type"] = (
        "Elaborazione Osservatorio su dati ufficiali"
    )
    data["metrics"]["ftthCoverage20m"]["method"]["formula"] = (
        "media delle coperture FTTH entro 20 metri comunali, ponderata per le "
        "famiglie residenti AGCOM"
    )

    # Ripristina nello snapshot i valori effettivamente ricevuti dalla fonte.
    raw_by_code = {code: shard["kpi"] for code, shard in agcom.items()}
    for town in snapshot.get("towns", []):
        code = town["code"]
        raw = raw_by_code[code]
        town["agcom"]["ftthHouseholds"] = raw.get("famiglie_ftth")
        town["agcom"]["ftthHouseholdsWithin20m"] = raw.get(
            "famiglie_ftth_20m"
        )

    snapshot.get("formulas", {}).pop("ftthUnreachedHouseholds", None)
    snapshot["coveragePolicy"] = {
        "publishedBroadbandMetrics": PUBLISHED_BROADBAND_KEYS,
        "omittedBroadbandMetrics": OMITTED_ABSOLUTE_KEYS,
        "missingDesiHouseholdCounts": missing_desi,
        "missingWithin20mHouseholdCounts": missing_20m,
        "note": (
            "I conteggi assoluti sono sospesi in questa fase se gli shard "
            "intermedi non sono completi; la pubblicazione finale usa il CSV "
            "primario AGCOM e la soglia minima 6/7, senza stime."
        ),
    }
    return data, snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--snapshot", type=Path, default=base.SNAPSHOT)
    args = parser.parse_args(argv)

    source_data = base._json_load(args.site_data)
    towns = base._town_rows(source_data)
    codes = [town["code"] for town in towns]
    asia, agcom, provenance = base.load_source_shards(codes, args.source_dir)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    updated, snapshot = apply_policy(
        source_data, asia, agcom, generated_at
    )
    snapshot["provenance"] = provenance

    previous_count = len(source_data["metrics"])
    expected_new = base.NEW_ECONOMY_KEYS + PUBLISHED_BROADBAND_KEYS
    metric_count = len(updated["metrics"])
    expected_count = expected_metric_count(source_data)
    if metric_count != expected_count:
        raise base.DataError(
            f"Conteggio indicatori inatteso: {metric_count}; previsto {expected_count}"
        )

    base._json_write(args.site_data, updated)
    base._json_write(args.snapshot, snapshot)
    if args.site_data.resolve() == base.SITE_DATA.resolve():
        base.update_count_files(metric_count, previous_count)

    print(
        json.dumps(
            {
                "status": "ok",
                "metricCount": metric_count,
                "managedMetrics": sorted(MANAGED_KEYS),
                "regeneratedMetrics": expected_new,
                "omittedMetrics": OMITTED_ABSOLUTE_KEYS,
                "snapshot": str(args.snapshot),
                "coveragePolicy": snapshot["coveragePolicy"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except base.DataError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        raise SystemExit(2)
