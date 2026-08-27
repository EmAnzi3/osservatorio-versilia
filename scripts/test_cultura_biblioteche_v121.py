#!/usr/bin/env python3
"""Gate dati e metodo del lotto Cultura e biblioteche v1.21.0."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "regione-toscana-cultura-biblioteche-2024.json"
MATERIALIZER = ROOT / "scripts" / "materialize_cultura_biblioteche_v121.py"

KEYS = (
    "libraryLoansPerResident",
    "libraryActiveBorrowersPer100",
    "libraryWeeklyOpeningHours",
)
CODES = {"046005", "046013", "046018", "046024", "046028", "046030", "046033"}
CURRENT = {
    "046005": (0.25, 13.64, 56.04),
    "046013": (0.86, 11.57, 61.96),
    "046018": (None, None, None),
    "046024": (0.22, 2.83, 47.98),
    "046028": (0.24, 2.81, 40.65),
    "046030": (None, None, None),
    "046033": (0.15, 8.58, 63.75),
}
EXPECTED_AGG = {
    "libraryLoansPerResident": 0.22957554282827833,
    "libraryActiveBorrowersPer100": 8.421880566636212,
    "libraryWeeklyOpeningHours": 54.076,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def by_code(metric: dict) -> dict[str, dict]:
    return {row["code"]: row for row in metric["rows"]}


def main() -> None:
    site = load(SITE)
    registry = load(REGISTRY)
    snapshot = load(SNAPSHOT)

    require(site["version"] == "v1.21.0" and site["updated"] == "27 agosto 2026", "Release non finalizzata")
    require(len(site["metrics"]) == 157, "Conteggio catalogo diverso da 157")
    require(registry["expectedMetricCount"] == 157, "Conteggio registry diverso da 157")
    require(registry["expectedInlineMetricCount"] == 153 and registry["expectedExternalMetricCount"] == 4, "Ripartizione 153+4 incoerente")

    community = site["themes"]["comunita"]
    section = next((item for item in community["sections"] if item["key"] == "cultura-biblioteche"), None)
    require(section is not None, "Sezione Cultura e biblioteche mancante")
    require(section["metrics"] == list(KEYS), "Ordine o contenuto della sezione Cultura errato")
    require(all(community["metrics"].count(key) == 1 for key in KEYS), "Metrica duplicata nel tema Comunità")
    all_section_refs = [key for s in community["sections"] for key in s["metrics"]]
    require(Counter(all_section_refs) == Counter(community["metrics"]), "Sezioni Comunità non riconciliate")

    require(snapshot["sources"]["indicatorCsv"]["sha256"] == "847b5e4a3d4d3104dd219e8da766228127d7ba764f7a2a7316f979b772608978", "Hash Indicatori errato")
    require(snapshot["sources"]["librariesCsv"]["sha256"] == "4914a35c89bede4ba5ae735925e62380a2db4db9dc578e072708356e552165c5", "Hash Biblioteche errato")
    require(set(snapshot["scope"]["townCodes"]) == CODES, "Sette codici ISTAT non riconciliati")

    current_snap = {row["code"]: row for row in snapshot["current2024"]}
    require(current_snap["046018"]["libraries2024"][0]["Codice ICCU"] == "IT-LU0029", "ICCU Massarosa errato")
    require(current_snap["046018"]["libraries2024"][0]["Stato"] == "Aperto/Attivo", "Massarosa non deve essere classificata chiusa")
    require(current_snap["046030"]["libraries2024"] == [] and not current_snap["046030"]["indicatorRowPresent"], "Stazzema deve restare riga assente")
    require(len(current_snap["046033"]["allIndicatorRows2024"]) == 2, "Doppia riga Viareggio non conservata nello snapshot")
    require(sum(row["Indice di prestito Comunale"] is not None for row in current_snap["046033"]["allIndicatorRows2024"]) == 1, "Viareggio: selezione riga valorizzata ambigua")

    for index, key in enumerate(KEYS):
        metric = site["metrics"][key]
        rows = by_code(metric)
        require(set(rows) == CODES and len(rows) == 7, f"{key}: copertura righe non 7/7")
        require(metric["meta"]["year"] == "2024", f"{key}: anno corrente non 2024")
        for code in CODES:
            expected = CURRENT[code][index]
            require(rows[code]["value"] == expected, f"{key}/{code}: valore 2024 errato")
            if expected is None:
                require(rows[code]["formatted"] == "n.d.", f"{key}/{code}: mancante non reso n.d.")
            else:
                require(rows[code]["series"] is not None, f"{key}/{code}: storico assente nonostante dato corrente")
                require(rows[code]["series"]["values"][-1] == expected, f"{key}/{code}: ultimo storico non coincide")
        require(math.isclose(metric["aggregate"]["value"], EXPECTED_AGG[key], rel_tol=0, abs_tol=1e-12), f"{key}: aggregato errato")
        require("(5/7)" in metric["aggregate"]["label"], f"{key}: aggregato non dichiara 5/7")
        require(metric["method"]["coverage"] == "5/7", f"{key}: metodo non dichiara esattamente 5/7")

    loans = by_code(site["metrics"]["libraryLoansPerResident"])
    impact = by_code(site["metrics"]["libraryActiveBorrowersPer100"])
    opening = by_code(site["metrics"]["libraryWeeklyOpeningHours"])

    # Un Comune coperto per tutto il periodo verifica l'estensione canonica della serie.
    require(loans["046005"]["series"]["years"] == [2019, 2020, 2021, 2022, 2023, 2024], "Storico prestiti Camaiore inatteso")
    require(impact["046005"]["series"]["years"] == [2019, 2020, 2021, 2022, 2023, 2024], "Storico impatto Camaiore inatteso")
    require(opening["046005"]["series"]["years"] == [2022, 2023, 2024], "Apertura Camaiore deve partire dal 2022")

    # I mancanti non ricevono code nulle o serie artificiali: ogni serie termina
    # all'ultima osservazione realmente pubblicata dalla Regione Toscana.
    require(loans["046018"]["series"] is not None and loans["046018"]["series"]["years"][-1] == 2022, "Massarosa prestiti deve interrompersi al 2022")
    require(impact["046018"]["series"] is not None and impact["046018"]["series"]["years"][-1] == 2021, "Massarosa impatto deve interrompersi al 2021")
    require(opening["046018"]["series"] is not None and opening["046018"]["series"]["years"][-1] == 2022, "Massarosa apertura deve interrompersi al 2022")
    for key in KEYS:
        require(by_code(site["metrics"][key])["046030"]["series"] is None, f"{key}: Stazzema non deve avere una serie artificiale")

    require(site["metrics"]["libraryActiveBorrowersPer100"]["meta"]["unit"] == "per100", "Impatto convertito impropriamente a 1.000")

    profile = registry["sourceProfiles"].get("regione-toscana-biblioteche-annual")
    require(profile and profile["publisher"] == "Regione Toscana", "Profilo fonte biblioteche mancante")
    for key in KEYS:
        require(registry["metricOverrides"].get(key, {}).get("profile") == "regione-toscana-biblioteche-annual", f"{key}: profilo monitor mancante")

    tracked = [
        SITE, REGISTRY, ROOT / "README.md", ROOT / "docs" / "copertura-serie-storiche.md",
        ROOT / "scripts" / "finalize_catalog_release.py", ROOT / "scripts" / "test_catalog_release_v116.py",
        ROOT / ".github" / "workflows" / "pages.yml", ROOT / "assets" / "app.js",
        ROOT / "assets" / "app-parts" / "05.txt", ROOT / "service-worker.js",
    ]
    before = {path: sha(path) for path in tracked}
    subprocess.run([sys.executable, str(MATERIALIZER)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    after = {path: sha(path) for path in tracked}
    require(before == after, "Materializzatore non idempotente: una seconda esecuzione produce diff")

    print("Cultura e biblioteche v1.21.0 verificata: 3 indicatori, 2024 5/7 esplicito, serie interrotte all'ultima osservazione reale, ICCU deduplicati, materializzatore idempotente.")


if __name__ == "__main__":
    main()
