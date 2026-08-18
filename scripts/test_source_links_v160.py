#!/usr/bin/env python3
"""Static checks for the source links exposed by the data model."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))

ASIA_DATAFLOW_URL = (
    "https://esploradati.istat.it/databrowser/#/it/dw/categories/"
    "IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/"
    "183_1163_DF_DICA_ASIAULP_TERRIFDATA_7"
)
PNRR_TOSCANA_URL = "https://dati.toscana.it/dataset/regione-toscana-pnrr"
ASIA_DATAFLOW_KEYS = {
    "localEmployees",
    "employeesPerLocalUnit",
    "localUnitsChange",
    "localEmployeesChange",
}

EXPECTED = {
    "oldAgeIndex": "https://www.istat.it/statistiche-per-temi/censimenti/popolazione-e-abitazioni/risultati/",
    "femaleEmploymentRate": "https://www.istat.it/notizia/dati-per-sezioni-di-censimento/",
    "tourismBeds": "https://www.istat.it/informazioni-sulla-rilevazione/capacita-degli-esercizi-ricettivi/",
    "schoolSites": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Scuole",
    "schoolStudents": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti",
    "hospitals": "https://www.salute.gov.it/new/it/banche-dati/elenco-aziende-sanitarie-locali-e-strutture-di-ricovero/?tema=Statistiche+sanitarie",
    "motorization": "https://www.istat.it/comunicato-stampa/indicatori-del-parco-veicolare-anno-2024/",
    "evPoints": "https://www.piattaformaunicanazionale.it/idr",
    "floodExposure": "https://www.isprambiente.gov.it/it/banche-dati/banche-dati-folder/suolo-e-territorio/rischi-geologici-e-naturali",
    "pnrrFunding": PNRR_TOSCANA_URL,
    "pnrrConcluded": PNRR_TOSCANA_URL,
    "cashReceiptsPerResident": "https://openbdap.rgs.mef.gov.it/it/FET/Analizza",
}

FORBIDDEN_SUBSTRINGS = (
    "dati-censimentipermanenti.istat.it",
    "Dati_regionali_2023.zip",
    "unica.istruzione.gov.it",
    "idrogeo.isprambiente.it/app",
    "Siope2Web",
    "/it/catalogo-open-data/Progetti_del_PNRR.html",
)

FORBIDDEN_EXACT = {
    "https://dati.istruzione.it/opendata/",
    "https://www.piattaformaunicanazionale.it/",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    links: list[tuple[str, str]] = []
    for key, metric in DATA["metrics"].items():
        url = metric.get("sourceUrl")
        if not url:
            continue
        links.append((key, url))
        parsed = urlparse(url)
        require(parsed.scheme == "https", f"Fonte non HTTPS: {key} -> {url}")
        require(bool(parsed.netloc), f"Fonte senza dominio: {key} -> {url}")
        require(url == url.strip(), f"Spazi nel link fonte: {key} -> {url!r}")
        require(url not in FORBIDDEN_EXACT,
                f"Link fonte troppo generico: {key} -> {url}")
        for fragile in FORBIDDEN_SUBSTRINGS:
            require(fragile not in url,
                    f"Link fonte fragile o obsoleto: {key} -> {url}")

        if "esploradati.istat.it" in url:
            require(key in ASIA_DATAFLOW_KEYS,
                    f"Permalink EsploraDati inatteso: {key} -> {url}")
            require(url == ASIA_DATAFLOW_URL,
                    f"Dataflow ASIA inatteso: {key} -> {url}")

    require(len(links) == len(DATA["metrics"]),
            "Almeno un indicatore è privo di sourceUrl")

    for key, expected in EXPECTED.items():
        actual = DATA["metrics"][key]["sourceUrl"]
        require(actual == expected, f"Fonte stabile inattesa: {key}: {actual} != {expected}")

    for key in ASIA_DATAFLOW_KEYS:
        require(DATA["metrics"][key]["sourceUrl"] == ASIA_DATAFLOW_URL,
                f"Fonte ASIA inattesa: {key}")

    require(DATA["metrics"]["schoolStudents"]["sourceUrl"] ==
            DATA["metrics"]["studentsPerClass"]["sourceUrl"] ==
            DATA["metrics"]["primaryFullTimeShare"]["sourceUrl"],
            "Gli indicatori scolastici devono rinviare allo stesso catalogo Studenti")
    require(DATA["metrics"]["cashReceiptsPerResident"]["sourceUrl"] ==
            DATA["metrics"]["cashBalancePerResident"]["sourceUrl"],
            "Gli indicatori SIOPE di cassa devono rinviare alla stessa pagina OpenBDAP")
    require(DATA["metrics"]["pnrrFunding"]["sourceUrl"] ==
            DATA["metrics"]["pnrrConcluded"]["sourceUrl"] == PNRR_TOSCANA_URL,
            "I due indicatori PNRR devono rinviare allo stesso dataset Regione Toscana")

    print(f"Link fonte validati staticamente: {len(links)} indicatori.")


if __name__ == "__main__":
    main()
