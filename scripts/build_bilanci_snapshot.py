#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
OUT_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
BASE = "https://openbdap.rgs.mef.gov.it"
PORTAL_URL = BASE + "/it/FET/Analizza"
TIMEOUT = 180

TOWN_CODES = {
    "Massarosa": "018",
    "Viareggio": "033",
    "Camaiore": "005",
    "Pietrasanta": "024",
    "Seravezza": "028",
    "Forte dei Marmi": "013",
    "Stazzema": "030",
}

ARCHIVES = {
    "2025-schemi": "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Schemi di bilancio_TOSCANA.zip",
    "2025-indicatori": "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Piano degli indicatori_TOSCANA.zip",
    "2024-schemi": "/Datasets_FET/Rendiconto/2024/2024_Rendiconto - Schemi di bilancio_TOSCANA.zip",
    "2024-indicatori": "/Datasets_FET/Rendiconto/2024/2024_Rendiconto - Piano degli indicatori_TOSCANA.zip",
}

MEMBERS = {
    "entrate": "Rendiconto SDB Entrate Riepilogo Titoli_TOSCANA.csv",
    "spese_titoli": "Rendiconto SDB Spese Riepilogo Titoli_TOSCANA.csv",
    "spese_missioni": "Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv",
    "risultato": "Rendiconto SDB Allegato A Risultato di Amministrazione_TOSCANA.csv",
    "indicatori": "Rendiconto PDI Sintetici Allegato 2-a_TOSCANA.csv",
}

MISSION_CODES = ["04", "05", "06", "07", "09", "10", "12", "14"]


def number(value: str | None) -> float:
    text = str(value or "").strip()
    return float(text) if text else 0.0


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def download_archive(session: requests.Session, path: str) -> tuple[bytes, str]:
    url = BASE + quote(path, safe="/:_-.")
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content, response.url


def find_member(archive: zipfile.ZipFile, suffix: str) -> zipfile.ZipInfo:
    matches = [info for info in archive.infolist() if info.filename.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"Atteso un solo file {suffix}, trovati {len(matches)}")
    return matches[0]


def read_rows(archive: zipfile.ZipFile, suffix: str) -> tuple[list[dict[str, str]], dict]:
    info = find_member(archive, suffix)
    raw = archive.read(info)
    text = decode(raw)
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    rows = []
    wanted_codes = set(TOWN_CODES.values())
    for row in reader:
        if (
            (row.get("Codice Tipologia Soggetto") or "").strip() == "ELCOMU"
            and (row.get("Codice Provincia") or "").strip() == "046"
            and (row.get("Codice Comune") or "").strip().zfill(3) in wanted_codes
        ):
            rows.append({key: value for key, value in row.items() if key and key.strip()})
    return rows, {
        "name": info.filename,
        "size_bytes": info.file_size,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def group_by_town(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    reverse = {code: town for town, code in TOWN_CODES.items()}
    grouped = {town: [] for town in TOWN_CODES}
    for row in rows:
        code = (row.get("Codice Comune") or "").strip().zfill(3)
        grouped[reverse[code]].append(row)
    return grouped


def population_lookup(data: dict) -> dict[str, dict[int, int]]:
    result = {}
    for row in data["metrics"]["population"]["rows"]:
        result[row["town"]] = {
            int(year): int(value)
            for year, value in zip(row["series"]["years"], row["series"]["values"])
        }
    return result


def compute_values(raw: dict) -> dict:
    population = raw["population_at_1_january"]
    current_revenue = raw["current_revenue_accruals_titles_1_2_3"]
    current_expenditure = raw["current_expenditure_commitments_title_1"]
    mission = raw["mission_commitments"]
    return {
        "currentRevenueAccruedPerResident": current_revenue / population,
        "currentExpenditureCommittedPerResident": current_expenditure / population,
        "capitalExpenditureCommittedPerResident": raw["capital_expenditure_commitments_title_2"] / population,
        "ownRevenueShare": raw["own_revenue_accruals_titles_1_3"] / current_revenue * 100,
        "currentCollectionCapacity": raw["current_revenue_competence_receipts_titles_1_2_3"] / current_revenue * 100,
        "currentPaymentCapacity": raw["current_expenditure_competence_payments_title_1"] / current_expenditure * 100,
        "availableAdministrationResultPerResident": raw["available_administration_result_code_0502"] / population,
        "rigidExpenditureShare": raw["rigid_expenditure_share_official_code_01_01"],
        "educationMissionExpenditurePerResident": mission.get("04", 0) / population,
        "socialMissionExpenditurePerResident": mission.get("12", 0) / population,
        "environmentMissionExpenditurePerResident": mission.get("09", 0) / population,
        "mobilityMissionExpenditurePerResident": mission.get("10", 0) / population,
        "cultureSportMissionExpenditurePerResident": (mission.get("05", 0) + mission.get("06", 0)) / population,
        "tourismDevelopmentMissionExpenditurePerResident": (mission.get("07", 0) + mission.get("14", 0)) / population,
    }


def build_year(
    year: int,
    populations: dict[str, dict[int, int]],
    archives: dict[str, tuple[bytes, str]],
) -> tuple[dict, dict]:
    selected_files = {}
    schemes_raw, schemes_url = archives[f"{year}-schemi"]
    indicators_raw, indicators_url = archives[f"{year}-indicatori"]

    with zipfile.ZipFile(io.BytesIO(schemes_raw)) as archive:
        entrance_rows, selected_files["entrate"] = read_rows(archive, MEMBERS["entrate"])
        spending_rows, selected_files["spese_titoli"] = read_rows(archive, MEMBERS["spese_titoli"])
        mission_rows, selected_files["spese_missioni"] = read_rows(archive, MEMBERS["spese_missioni"])
        result_rows, selected_files["risultato"] = read_rows(archive, MEMBERS["risultato"])
    with zipfile.ZipFile(io.BytesIO(indicators_raw)) as archive:
        indicator_rows, selected_files["indicatori"] = read_rows(archive, MEMBERS["indicatori"])

    entrance = group_by_town(entrance_rows)
    spending = group_by_town(spending_rows)
    missions = group_by_town(mission_rows)
    results = group_by_town(result_rows)
    indicators = group_by_town(indicator_rows)

    year_raw = {}
    for town in TOWN_CODES:
        entrance_by_title = {
            (row.get("Codice Titolo") or "").strip().zfill(2): row
            for row in entrance[town]
        }
        spending_by_title = {
            (row.get("Codice Titolo") or "").strip().zfill(2): row
            for row in spending[town]
        }
        mission_by_code = {
            (row.get("Codice Missione") or "").strip().zfill(2): row
            for row in missions[town]
        }
        result_by_code = {
            (row.get("Cod Voce Ris Amm Rend") or "").strip(): row
            for row in results[town]
        }
        indicator_by_code = {
            (
                (row.get("Codice Tipologia Indicatore Sintetico 2)a") or "").strip().zfill(2),
                (row.get("Codice Indicatore Sintetico 2)a") or "").strip().zfill(2),
            ): row
            for row in indicators[town]
        }

        current_revenue = sum(
            number(entrance_by_title.get(code, {}).get("Accertamenti"))
            for code in ("01", "02", "03")
        )
        current_expenditure = number(
            spending_by_title.get("01", {}).get("Impegni")
        )
        if not current_revenue or not current_expenditure:
            raise RuntimeError(f"Valori correnti mancanti per {town}, {year}")

        rigid_row = indicator_by_code.get(("01", "01"))
        if rigid_row is None:
            raise RuntimeError(f"Indicatore rigido mancante per {town}, {year}")

        year_raw[town] = {
            "population_at_1_january": populations[town][year],
            "current_revenue_accruals_titles_1_2_3": current_revenue,
            "own_revenue_accruals_titles_1_3": sum(
                number(entrance_by_title.get(code, {}).get("Accertamenti"))
                for code in ("01", "03")
            ),
            "current_revenue_competence_receipts_titles_1_2_3": sum(
                number(entrance_by_title.get(code, {}).get("Riscossioni in C/Competenza"))
                for code in ("01", "02", "03")
            ),
            "current_expenditure_commitments_title_1": current_expenditure,
            "current_expenditure_competence_payments_title_1": number(
                spending_by_title.get("01", {}).get("Pagamenti in C/Competenza")
            ),
            "capital_expenditure_commitments_title_2": number(
                spending_by_title.get("02", {}).get("Impegni")
            ),
            "available_administration_result_code_0502": number(
                result_by_code.get("0502", {}).get("Totale di Gestione")
            ),
            "rigid_expenditure_share_official_code_01_01": number(
                rigid_row.get("Indicatore Tutte Le Missioni")
            ),
            "mission_commitments": {
                code: number(mission_by_code.get(code, {}).get("Impegni"))
                for code in MISSION_CODES
            },
        }

    archive_meta = {
        "schemi": {
            "url": schemes_url,
            "size_bytes": len(schemes_raw),
            "sha256": hashlib.sha256(schemes_raw).hexdigest(),
        },
        "indicatori": {
            "url": indicators_url,
            "size_bytes": len(indicators_raw),
            "sha256": hashlib.sha256(indicators_raw).hexdigest(),
        },
        "selected_files": selected_files,
    }
    return year_raw, archive_meta


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    populations = population_lookup(data)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)",
            "Accept": "application/zip,*/*;q=0.8",
        }
    )

    downloaded = {
        label: download_archive(session, path)
        for label, path in ARCHIVES.items()
    }

    raw_by_town = {
        town: {
            "code": "046" + code,
            "slug": next(
                row["slug"]
                for row in data["metrics"]["population"]["rows"]
                if row["town"] == town
            ),
            "years": {},
        }
        for town, code in TOWN_CODES.items()
    }
    sources = {}
    for year in (2024, 2025):
        year_raw, sources[str(year)] = build_year(year, populations, downloaded)
        for town, values in year_raw.items():
            raw_by_town[town]["years"][str(year)] = values

    metric_keys = list(compute_values(raw_by_town["Massarosa"]["years"]["2025"]))
    metrics = {}
    for key in metric_keys:
        years = [2025] if key == "rigidExpenditureShare" else [2024, 2025]
        metrics[key] = {
            "coverage": "7/7",
            "years": years,
            "values": {
                town: {
                    str(year): compute_values(raw_by_town[town]["years"][str(year)])[key]
                    for year in years
                }
                for town in TOWN_CODES
            },
        }

    if raw_by_town["Camaiore"]["years"]["2024"]["rigid_expenditure_share_official_code_01_01"] < 100:
        raise RuntimeError("Il controllo dell’anomalia 2024 sulle spese rigide non è più valido")

    payload = {
        "version": "2026.08.05-local-v1.6.0-bilanci",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Rendiconti OpenBDAP 2024 e 2025 dei sette Comuni dell’Osservatorio Versilia.",
        "source": {
            "publisher": "Ragioneria generale dello Stato — OpenBDAP",
            "portal_url": PORTAL_URL,
            "document_type": "Rendiconto",
            "region": "Toscana",
            "years": sources,
        },
        "selection_rules": {
            "subject_type": "ELCOMU — Comuni",
            "province_code": "046 — Lucca",
            "municipality_codes": {
                town: "046" + code for town, code in TOWN_CODES.items()
            },
            "years": [2024, 2025],
            "population_denominator": "Residenti Istat al 1° gennaio dello stesso esercizio finanziario.",
        },
        "raw": raw_by_town,
        "metrics": metrics,
        "caveats": [
            "Accertamenti, impegni, riscossioni e pagamenti sono grandezze contabili diverse e non vengono trattate come equivalenti.",
            "I valori per missione comprendono spesa corrente e in conto capitale.",
            "Il confronto non costituisce una graduatoria di virtuosità: organizzazione dei servizi, presenze turistiche, gestioni associate e investimenti straordinari incidono sui valori.",
            "Per l’incidenza delle spese rigide viene usato soltanto il 2025, perché nel file ufficiale 2024 è stato rilevato almeno un valore formalmente anomalo.",
        ],
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Snapshot Bilanci scritto in {OUT_PATH}")


if __name__ == "__main__":
    main()
