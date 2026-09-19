#!/usr/bin/env python3
"""A3.5 lotto 2: integra numeratore/denominatore per indicatori OpenBDAP/SIOPE.

Il lotto usa esclusivamente componenti già congelati negli snapshot versionati:
- bilanci-v1.6.0.json per rendiconto OpenBDAP;
- siope-history-v1.6.0.json per incassi/saldi di cassa.

Non ricostruisce numeratori a partire dal rapporto già pubblicato.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
BILANCI_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
SIOPE_PATH = ROOT / "data" / "source-snapshots" / "siope-history-v1.6.0.json"
YEAR = 2025

BILANCI_TARGETS = (
    "currentRevenueAccruedPerResident",
    "currentExpenditureCommittedPerResident",
    "capitalExpenditureCommittedPerResident",
    "ownRevenueShare",
    "currentCollectionCapacity",
    "currentPaymentCapacity",
    "availableAdministrationResultPerResident",
    "educationMissionExpenditurePerResident",
    "socialMissionExpenditurePerResident",
    "environmentMissionExpenditurePerResident",
    "mobilityMissionExpenditurePerResident",
    "cultureSportMissionExpenditurePerResident",
    "tourismDevelopmentMissionExpenditurePerResident",
    "economicDevelopmentMissionExpenditurePerResident",
)
SIOPE_TARGETS = (
    "cashReceiptsPerResident",
    "cashBalancePerResident",
)
TARGET_METRICS = BILANCI_TARGETS + SIOPE_TARGETS

MISSION_CODES = {
    "educationMissionExpenditurePerResident": ("04",),
    "socialMissionExpenditurePerResident": ("12",),
    "environmentMissionExpenditurePerResident": ("09",),
    "mobilityMissionExpenditurePerResident": ("10",),
    "cultureSportMissionExpenditurePerResident": ("05", "06"),
    "tourismDevelopmentMissionExpenditurePerResident": ("07", "14"),
    "economicDevelopmentMissionExpenditurePerResident": ("14",),
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_close(actual: float, expected: float, label: str) -> None:
    tolerance = max(1e-7, abs(expected) * 1e-10)
    if abs(float(actual) - float(expected)) > tolerance:
        raise RuntimeError(f"{label}: {actual} != {expected}")


def _rows_by_town(metric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("Metrica senza rows")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("Riga metrica non-oggetto")
        town = str(row.get("town") or "").strip()
        if not town or town in out:
            raise RuntimeError(f"Comune mancante o duplicato: {town!r}")
        out[town] = row
    return out


def _mission_amount(raw: dict[str, Any], codes: tuple[str, ...]) -> float:
    missions = raw.get("mission_commitments")
    if not isinstance(missions, dict):
        raise RuntimeError("Snapshot OpenBDAP privo di mission_commitments")
    return sum(float(missions.get(code, 0.0) or 0.0) for code in codes)


def _bilanci_components(metric_id: str, raw: dict[str, Any]) -> tuple[float, float, float, str, str]:
    population = float(raw["population_at_1_january"])
    if population <= 0:
        raise RuntimeError("Popolazione OpenBDAP/Istat non positiva")

    if metric_id == "currentRevenueAccruedPerResident":
        return float(raw["current_revenue_accruals_titles_1_2_3"]), population, 1.0, "Accertamenti entrate correnti Titoli 1+2+3", "Popolazione residente"
    if metric_id == "currentExpenditureCommittedPerResident":
        return float(raw["current_expenditure_commitments_title_1"]), population, 1.0, "Impegni spesa corrente Titolo 1", "Popolazione residente"
    if metric_id == "capitalExpenditureCommittedPerResident":
        return float(raw["capital_expenditure_commitments_title_2"]), population, 1.0, "Impegni spesa in conto capitale Titolo 2", "Popolazione residente"
    if metric_id == "ownRevenueShare":
        return float(raw["own_revenue_accruals_titles_1_3"]), float(raw["current_revenue_accruals_titles_1_2_3"]), 100.0, "Accertamenti entrate proprie Titoli 1+3", "Accertamenti entrate correnti Titoli 1+2+3"
    if metric_id == "currentCollectionCapacity":
        return float(raw["current_revenue_competence_receipts_titles_1_2_3"]), float(raw["current_revenue_accruals_titles_1_2_3"]), 100.0, "Riscossioni di competenza Titoli 1+2+3", "Accertamenti entrate correnti Titoli 1+2+3"
    if metric_id == "currentPaymentCapacity":
        return float(raw["current_expenditure_competence_payments_title_1"]), float(raw["current_expenditure_commitments_title_1"]), 100.0, "Pagamenti di competenza Titolo 1", "Impegni spesa corrente Titolo 1"
    if metric_id == "availableAdministrationResultPerResident":
        return float(raw["available_administration_result_code_0502"]), population, 1.0, "Totale parte disponibile del risultato di amministrazione (0502)", "Popolazione residente"
    if metric_id in MISSION_CODES:
        codes = MISSION_CODES[metric_id]
        amount = _mission_amount(raw, codes)
        label = " + ".join(f"Missione {code}" for code in codes)
        return amount, population, 1.0, f"Impegni {label}", "Popolazione residente"
    raise KeyError(metric_id)


def _siope_components(metric_id: str, raw: dict[str, Any]) -> tuple[float, float, float, str, str]:
    population = float(raw["population_resident"])
    if population <= 0:
        raise RuntimeError("Popolazione SIOPE/Istat non positiva")
    if metric_id == "cashReceiptsPerResident":
        return float(raw["cash_receipts"]), population, 1.0, "Incassi complessivi cumulati a dicembre", "Popolazione residente"
    if metric_id == "cashBalancePerResident":
        return float(raw["cash_balance"]), population, 1.0, "Saldo di cassa (incassi - pagamenti)", "Popolazione residente"
    raise KeyError(metric_id)


def _ratio_payload(
    *,
    metric_id: str,
    numerator: float,
    denominator: float,
    scale: float,
    numerator_label: str,
    denominator_label: str,
    source: str,
    source_url: str,
    source_snapshot: str,
) -> dict[str, Any]:
    if denominator == 0:
        raise RuntimeError(f"{metric_id}: denominatore nullo")
    return {
        "dimension": "numeratore_denominatore",
        "year": YEAR,
        "source": source,
        "sourceUrl": source_url,
        "sourceSnapshot": source_snapshot,
        "scale": scale,
        "numerator": {
            "label": numerator_label,
            "value": numerator,
            "unit": "currency",
        },
        "denominator": {
            "label": denominator_label,
            "value": denominator,
            "unit": "number" if "Popolazione" in denominator_label else "currency",
        },
    }


def _ratio_value(payload: dict[str, Any]) -> float:
    numerator = float(payload["numerator"]["value"])
    denominator = float(payload["denominator"]["value"])
    scale = float(payload["scale"])
    if denominator == 0:
        raise RuntimeError("Denominatore nullo nel payload")
    return numerator / denominator * scale


def apply_enrichment(site: dict[str, Any], bilanci: dict[str, Any], siope: dict[str, Any]) -> dict[str, int]:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")
    missing = [key for key in TARGET_METRICS if key not in metrics]
    if missing:
        raise RuntimeError(f"Metriche A3.5 mancanti: {missing}")

    bilanci_raw = bilanci.get("raw")
    siope_raw = siope.get("raw")
    if not isinstance(bilanci_raw, dict) or not isinstance(siope_raw, dict):
        raise RuntimeError("Snapshot A3.5 privi delle strutture raw richieste")

    expected_towns: set[str] | None = None
    enriched_rows = 0

    for metric_id in TARGET_METRICS:
        metric = metrics[metric_id]
        rows = _rows_by_town(metric)
        towns = set(rows)
        if expected_towns is None:
            expected_towns = towns
        elif towns != expected_towns:
            raise RuntimeError(f"{metric_id}: perimetro comunale non allineato")
        if len(towns) != 7:
            raise RuntimeError(f"{metric_id}: attesi 7 Comuni, trovati {len(towns)}")

        for town, row in rows.items():
            source_url = str(metric.get("sourceUrl") or "").strip()
            if not source_url:
                raise RuntimeError(f"{metric_id}: sourceUrl assente")

            if metric_id in BILANCI_TARGETS:
                raw = bilanci_raw.get(town, {}).get("years", {}).get(str(YEAR))
                if not isinstance(raw, dict):
                    raise RuntimeError(f"{metric_id}/{town}: raw OpenBDAP {YEAR} mancante")
                numerator, denominator, scale, num_label, den_label = _bilanci_components(metric_id, raw)
                payload = _ratio_payload(
                    metric_id=metric_id,
                    numerator=numerator,
                    denominator=denominator,
                    scale=scale,
                    numerator_label=num_label,
                    denominator_label=den_label,
                    source="RGS — OpenBDAP · Rendiconto; popolazione Istat",
                    source_url=source_url,
                    source_snapshot="data/source-snapshots/bilanci-v1.6.0.json",
                )
            else:
                raw = siope_raw.get(town, {}).get(str(YEAR))
                if not isinstance(raw, dict):
                    raise RuntimeError(f"{metric_id}/{town}: raw SIOPE {YEAR} mancante")
                numerator, denominator, scale, num_label, den_label = _siope_components(metric_id, raw)
                payload = _ratio_payload(
                    metric_id=metric_id,
                    numerator=numerator,
                    denominator=denominator,
                    scale=scale,
                    numerator_label=num_label,
                    denominator_label=den_label,
                    source="RGS — BDAP Open Data / SIOPE; popolazione Istat",
                    source_url=source_url,
                    source_snapshot="data/source-snapshots/siope-history-v1.6.0.json",
                )

            expected = _ratio_value(payload)
            _assert_close(float(row["value"]), expected, f"{metric_id}/{town}")
            row["ratioComponents"] = payload
            enriched_rows += 1

    return {
        "metricsEnriched": len(TARGET_METRICS),
        "towns": len(expected_towns or ()),
        "rowsEnriched": enriched_rows,
        "pairsAcquired": len(TARGET_METRICS),
    }


def main() -> None:
    site = load(SITE_PATH)
    bilanci = load(BILANCI_PATH)
    siope = load(SIOPE_PATH)
    summary = apply_enrichment(site, bilanci, siope)
    save(SITE_PATH, site)
    print(
        "A3.5 OpenBDAP numeratore/denominatore: "
        f"{summary['metricsEnriched']} metriche × {summary['towns']} comuni; "
        f"{summary['pairsAcquired']} coppie AVAILABLE_MISSING integrate."
    )


if __name__ == "__main__":
    main()
