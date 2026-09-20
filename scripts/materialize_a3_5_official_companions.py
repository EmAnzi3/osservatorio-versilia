#!/usr/bin/env python3
"""A3.5 lotto 8: dimensioni strutturali da snapshot Istat, AGCOM e RGS già versionati.

Il lotto è esclusivamente non-visivo: aggiunge strutture A3 ignorate dal renderer
senza cambiare valori, testi, metadati o aggregati pubblici. Ogni acquisizione è
riconciliata contro conteggi ufficiali già congelati nella repository.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
ISTAT_2024_PATH = ROOT / "data" / "source-snapshots" / "istat-lavoro-istruzione-eta-genere-2024.json"
LIA_2023_PATH = ROOT / "data" / "source-snapshots" / "lia-v1.4.0.json"
AGCOM_PATH = ROOT / "data" / "source-snapshots" / "agid-asia-agcom-2026-08.json"
RGS_ADMIN_PATH = ROOT / "data" / "source-snapshots" / "rgs-amministrazione-2024.json"
RGS_TRAINING_PATH = ROOT / "data" / "source-snapshots" / "rgs-formazione-2024.json"

ISTAT_TARGETS = ("femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap")
AGCOM_TARGETS = ("ftthCoverageDesi", "ftthCoverage20m", "ftthReachedHouseholds", "ftthUnreachedHouseholds")
RGS_TURNOVER = "municipalStaffTurnover"
RGS_TRAINING = "municipalStaffTraining"

AGE_KEYS = ("15-24", "25-49", "50-64", "65plus", "25-64", "15plus")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _num(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label}: valore numerico atteso")
    number = float(value)
    if not math.isfinite(number):
        raise RuntimeError(f"{label}: valore non finito")
    return number


def _assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance):
        raise RuntimeError(f"{label}: {actual} != {expected}")


def _rows_by_town(metric: dict[str, Any], metric_id: str) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError(f"{metric_id}: rows mancanti")
    result = {str(row["town"]): row for row in rows if isinstance(row, dict) and row.get("town")}
    if len(result) != 7:
        raise RuntimeError(f"{metric_id}: perimetro comunale atteso 7/7")
    return result


def _employment_rate(cell: dict[str, Any]) -> float:
    population = _num(cell.get("population"), "population")
    employed = _num(cell.get("employed"), "employed")
    if population <= 0:
        raise RuntimeError("popolazione nulla")
    return employed / population * 100.0


def _istat_public_value_2023(metric_id: str, raw: dict[str, Any]) -> float:
    female = _num(raw.get("P103"), f"{metric_id}: P103") / _num(raw.get("female1564"), f"{metric_id}: female1564") * 100.0
    male = _num(raw.get("P102"), f"{metric_id}: P102") / _num(raw.get("male1564"), f"{metric_id}: male1564") * 100.0
    if metric_id == "femaleEmploymentRate":
        return female
    if metric_id == "maleEmploymentRate":
        return male
    if metric_id == "employmentGenderGap":
        return male - female
    raise KeyError(metric_id)


def _apply_istat(metrics: dict[str, Any], istat: dict[str, Any], lia: dict[str, Any]) -> int:
    towns = istat.get("towns")
    raw_2023 = lia.get("raw", {}).get("istat2023")
    if not isinstance(towns, dict) or len(towns) != 7:
        raise RuntimeError("Snapshot Istat lavoro 2024 privo di 7 Comuni")
    if not isinstance(raw_2023, list) or len(raw_2023) != 7:
        raise RuntimeError("Snapshot LIA 2023 privo di 7 Comuni")
    by_town_2023 = {str(item["town"]): item for item in raw_2023}

    pairs = 0
    for metric_id in ISTAT_TARGETS:
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            raise RuntimeError(f"Metrica Istat mancante: {metric_id}")
        for town, row in _rows_by_town(metric, metric_id).items():
            public_expected = _istat_public_value_2023(metric_id, by_town_2023[town])
            _assert_close(_num(row.get("value"), f"{metric_id}/{town}: value"), public_expected, f"{metric_id}/{town}: pubblico 2023", 0.12)

            labour = towns[town].get("labour")
            if not isinstance(labour, dict):
                raise RuntimeError(f"{metric_id}/{town}: labour 2024 mancante")

            gender = {}
            for gender_key in ("total", "men", "women"):
                cell = labour["25-64"][gender_key]
                gender[gender_key] = {
                    "value": _employment_rate(cell),
                    "population": _num(cell.get("population"), f"{metric_id}/{town}/{gender_key}: population"),
                    "employed": _num(cell.get("employed"), f"{metric_id}/{town}/{gender_key}: employed"),
                }

            age = []
            for age_key in AGE_KEYS:
                if metric_id == "femaleEmploymentRate":
                    value = _employment_rate(labour[age_key]["women"])
                elif metric_id == "maleEmploymentRate":
                    value = _employment_rate(labour[age_key]["men"])
                else:
                    value = _employment_rate(labour[age_key]["men"]) - _employment_rate(labour[age_key]["women"])
                age.append({"ageClass": age_key, "value": value, "unit": "percent" if metric_id != "employmentGenderGap" else "percentagePoints"})

            payload: dict[str, Any] = {
                "referenceYear": 2024,
                "source": "Istat — Censimento permanente della popolazione",
                "sourceSnapshot": "data/source-snapshots/istat-lavoro-istruzione-eta-genere-2024.json",
                "gender": gender,
                "age": age,
            }

            if metric_id in {"femaleEmploymentRate", "maleEmploymentRate"}:
                gender_key = "women" if metric_id == "femaleEmploymentRate" else "men"
                cell = labour["25-64"][gender_key]
                population = _num(cell.get("population"), f"{metric_id}/{town}: population")
                employed = _num(cell.get("employed"), f"{metric_id}/{town}: employed")
                unemployed = _num(cell.get("unemployed"), f"{metric_id}/{town}: unemployed")
                active = _num(cell.get("active"), f"{metric_id}/{town}: active")
                inactive = population - active
                if min(employed, unemployed, inactive) < -1e-8:
                    raise RuntimeError(f"{metric_id}/{town}: categorie lavoro negative")
                _assert_close(employed + unemployed + inactive, population, f"{metric_id}/{town}: partizione lavoro", 1e-6)
                payload["categories"] = [
                    {"key": "employed", "label": "Occupati", "value": employed, "unit": "people"},
                    {"key": "unemployed", "label": "In cerca di occupazione", "value": unemployed, "unit": "people"},
                    {"key": "inactive", "label": "Inattivi", "value": inactive, "unit": "people"},
                ]

            row["a3LabourDimensions"] = payload

        pairs += 2
        if metric_id != "employmentGenderGap":
            pairs += 1

    return pairs


def _agcom_source(raw: dict[str, Any], metric_id: str, town: str) -> dict[str, float]:
    agcom = raw.get("agcom")
    if not isinstance(agcom, dict):
        raise RuntimeError(f"{metric_id}/{town}: AGCOM mancante")
    primary = agcom.get("primaryOfficialCsv")
    if not isinstance(primary, dict):
        raise RuntimeError(f"{metric_id}/{town}: CSV primario AGCOM mancante")
    resident = _num(primary.get("famiglie_residenti"), f"{metric_id}/{town}: resident")
    reached = _num(primary.get("famiglie_ftth"), f"{metric_id}/{town}: reached")
    within20m = _num(primary.get("famiglie_ftth_20m"), f"{metric_id}/{town}: within20m")
    desi_pct = _num(primary.get("copertura_ftth_desi_pct"), f"{metric_id}/{town}: desi pct")
    within20m_pct = _num(primary.get("copertura_ftth_20m_pct"), f"{metric_id}/{town}: 20m pct")
    if not (0 <= within20m <= reached <= resident):
        raise RuntimeError(f"{metric_id}/{town}: conteggi AGCOM non annidati")
    if resident <= 0:
        raise RuntimeError(f"{metric_id}/{town}: famiglie residenti nulle")
    _assert_close(reached / resident * 100.0, desi_pct, f"{metric_id}/{town}: DESI", 0.11)
    _assert_close(within20m / resident * 100.0, within20m_pct, f"{metric_id}/{town}: 20m", 0.11)
    return {
        "resident": resident,
        "reached": reached,
        "within20m": within20m,
        "desiPct": desi_pct,
        "within20mPct": within20m_pct,
    }


def _apply_agcom(metrics: dict[str, Any], snapshot: dict[str, Any]) -> int:
    towns = snapshot.get("towns")
    if not isinstance(towns, list) or len(towns) != 7:
        raise RuntimeError("Snapshot AGCOM privo di 7 Comuni")
    by_town = {str(item["town"]): item for item in towns}

    pairs = 0
    for metric_id in AGCOM_TARGETS:
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            raise RuntimeError(f"Metrica AGCOM mancante: {metric_id}")
        for town, row in _rows_by_town(metric, metric_id).items():
            values = _agcom_source(by_town[town], metric_id, town)
            if metric_id == "ftthCoverageDesi":
                absolute = values["reached"]
                normalized = values["desiPct"]
                _assert_close(_num(row.get("value"), f"{metric_id}/{town}: value"), normalized, f"{metric_id}/{town}: pubblico", 0.11)
            elif metric_id == "ftthCoverage20m":
                absolute = values["within20m"]
                normalized = values["within20mPct"]
                _assert_close(_num(row.get("value"), f"{metric_id}/{town}: value"), normalized, f"{metric_id}/{town}: pubblico", 0.11)
            elif metric_id == "ftthReachedHouseholds":
                absolute = values["reached"]
                normalized = values["desiPct"]
                _assert_close(_num(row.get("value"), f"{metric_id}/{town}: value"), absolute, f"{metric_id}/{town}: pubblico", 0.51)
            else:
                absolute = values["resident"] - values["reached"]
                normalized = absolute / values["resident"] * 100.0
                _assert_close(_num(row.get("value"), f"{metric_id}/{town}: value"), absolute, f"{metric_id}/{town}: pubblico", 0.51)

            payload: dict[str, Any] = {
                "referencePeriod": "31/12/2025",
                "source": "AGCOM — Broadband Map",
                "sourceSnapshot": "data/source-snapshots/agid-asia-agcom-2026-08.json",
                "absolute": absolute,
                "normalized": normalized,
                "categories": [
                    {"key": "within20m", "label": "FTTH entro 20 m", "value": values["within20m"], "unit": "households"},
                    {"key": "desiBeyond20m", "label": "FTTH DESI oltre 20 m", "value": values["reached"] - values["within20m"], "unit": "households"},
                    {"key": "unreached", "label": "Non raggiunte FTTH DESI", "value": values["resident"] - values["reached"], "unit": "households"},
                ],
            }
            _assert_close(sum(item["value"] for item in payload["categories"]), values["resident"], f"{metric_id}/{town}: categorie AGCOM", 1e-6)
            if metric_id in {"ftthCoverageDesi", "ftthCoverage20m"}:
                payload["numerator"] = absolute
                payload["denominator"] = values["resident"]
                _assert_close(absolute / values["resident"] * 100.0, normalized, f"{metric_id}/{town}: rapporto", 0.11)
            row["a3FtthDimensions"] = payload

        pairs += 2
        if metric_id in {"ftthCoverageDesi", "ftthCoverage20m"}:
            pairs += 1

    return pairs


def _apply_rgs(metrics: dict[str, Any], admin: dict[str, Any], training: dict[str, Any]) -> int:
    admin_towns = admin.get("towns")
    training_towns = training.get("towns")
    if not isinstance(admin_towns, dict) or len(admin_towns) != 7:
        raise RuntimeError("Snapshot RGS amministrazione privo di 7 Comuni")
    if not isinstance(training_towns, dict) or len(training_towns) != 7:
        raise RuntimeError("Snapshot RGS formazione privo di 7 Comuni")

    turnover = metrics.get(RGS_TURNOVER)
    if not isinstance(turnover, dict):
        raise RuntimeError("Metrica turnover RGS mancante")
    for town, row in _rows_by_town(turnover, RGS_TURNOVER).items():
        raw = admin_towns[town]
        absolute = _num(raw.get("netTurnoverHeadcount"), f"{town}: turnover absolute")
        normalized = _num(raw.get("netTurnoverRatePct"), f"{town}: turnover rate")
        _assert_close(_num(row.get("value"), f"{town}: turnover pubblico"), normalized, f"{town}: turnover", 0.0002)
        row["a3StaffTurnoverDimensions"] = {
            "referenceYear": 2024,
            "source": "Ragioneria Generale dello Stato — Conto Annuale",
            "sourceSnapshot": "data/source-snapshots/rgs-amministrazione-2024.json",
            "absolute": absolute,
            "normalized": normalized,
            "categories": [
                {"key": "hires", "label": "Assunzioni nette", "value": _num(raw.get("netHires"), f"{town}: hires"), "unit": "people"},
                {"key": "cessations", "label": "Cessazioni nette", "value": _num(raw.get("netCessations"), f"{town}: cessations"), "unit": "people"},
            ],
        }

    metric = metrics.get(RGS_TRAINING)
    if not isinstance(metric, dict):
        raise RuntimeError("Metrica formazione RGS mancante")
    for town, row in _rows_by_town(metric, RGS_TRAINING).items():
        raw = training_towns[town]
        _assert_close(_num(row.get("value"), f"{town}: training pubblico"), _num(raw.get("meanTotalRgs"), f"{town}: mean total"), f"{town}: training", 1e-10)
        men_days = _num(raw.get("menDays"), f"{town}: men days")
        women_days = _num(raw.get("womenDays"), f"{town}: women days")
        total_days = _num(raw.get("totalDays"), f"{town}: total days")
        _assert_close(men_days + women_days, total_days, f"{town}: training gender days", 1e-9)
        row["a3TrainingGender"] = {
            "referenceYear": 2024,
            "source": "Ragioneria Generale dello Stato — Conto Annuale",
            "sourceSnapshot": "data/source-snapshots/rgs-formazione-2024.json",
            "gender": [
                {"key": "men", "label": "Uomini", "days": men_days, "mean": _num(raw.get("meanMen"), f"{town}: mean men")},
                {"key": "women", "label": "Donne", "days": women_days, "mean": _num(raw.get("meanWomen"), f"{town}: mean women")},
            ],
        }

    return 3


def apply_enrichment(
    site: dict[str, Any],
    istat: dict[str, Any],
    lia: dict[str, Any],
    agcom: dict[str, Any],
    rgs_admin: dict[str, Any],
    rgs_training: dict[str, Any],
) -> dict[str, int]:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")
    required = set(ISTAT_TARGETS) | set(AGCOM_TARGETS) | {RGS_TURNOVER, RGS_TRAINING}
    missing = sorted(required - set(metrics))
    if missing:
        raise RuntimeError(f"Metriche lotto 8 mancanti: {missing}")

    istat_pairs = _apply_istat(metrics, istat, lia)
    agcom_pairs = _apply_agcom(metrics, agcom)
    rgs_pairs = _apply_rgs(metrics, rgs_admin, rgs_training)
    pairs = istat_pairs + agcom_pairs + rgs_pairs
    if pairs != 21:
        raise RuntimeError(f"Conteggio coppie lotto 8 inatteso: {pairs}")

    return {
        "istatPairs": istat_pairs,
        "agcomPairs": agcom_pairs,
        "rgsPairs": rgs_pairs,
        "pairsAcquired": pairs,
    }


def main() -> None:
    site = load(SITE_PATH)
    summary = apply_enrichment(
        site,
        load(ISTAT_2024_PATH),
        load(LIA_2023_PATH),
        load(AGCOM_PATH),
        load(RGS_ADMIN_PATH),
        load(RGS_TRAINING_PATH),
    )
    save(SITE_PATH, site)
    print(
        "A3.5 Istat + AGCOM + RGS companions: "
        f"{summary['pairsAcquired']} coppie integrate "
        f"({summary['istatPairs']} Istat, {summary['agcomPairs']} AGCOM, {summary['rgsPairs']} RGS)."
    )


if __name__ == "__main__":
    main()
