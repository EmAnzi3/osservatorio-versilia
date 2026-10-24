#!/usr/bin/env python3
"""Validate and attach native Istat histories; current data remain unchanged."""
from __future__ import annotations

import argparse
import base64
import copy
import csv
import hashlib
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data/source-snapshots/a3-istat-history-extension.json"
CURRENT_PATH = ROOT / "data/source-snapshots/istat-lavoro-istruzione-eta-genere-2024.json"
SNAPSHOT_REF = "data/source-snapshots/a3-istat-history-extension.json"
DEFAULT_PART = "25-64|total"
INDICATOR = "Incidenza di adulti con diploma o laurea"
NOTE = ("Censimenti tradizionali 1991, 2001 e 2011; Censimento permanente 2024: "
        "discontinuità della modalità di rilevazione. Osservazioni nei soli anni indicati, "
        "senza interpolazione annuale. Nessun aggregato storico Versilia senza denominatori nativi.")

# Pinned acquisition contracts: definitions and workbook identities, not public values.
WORKBOOKS = {'labour': {'url': 'https://www.istat.it/storage/misura-comune/5-Lavoro.xlsx',
            'sha256': '3a735eb22fad37b123d68489652b4b748fdad4f2d6e7e4acc8d9c7fc637aea22',
            'bytes': 3145506},
 'education': {'url': 'https://www.istat.it/storage/misura-comune/4-Istruzione.xlsx',
               'sha256': '7e329c0516a8bca0665b0cf6bacbbe8cbc013c129e6e168c958e0df4a980c760',
               'bytes': 4329441}}
COMPONENTS = {'employmentRate': {'workbook': 'labour',
                    'sheet': 'Tav. 1.1 Comuni',
                    'partKey': '15plus|total',
                    'years': [2019, 2021, 2022, 2023],
                    'title': 'Tavola 1.1 - Tasso di occupazione per comune. Anni 2019, 2021-2023',
                    'header': ['Ripartizione',
                               'Codice regione',
                               'Denominazione regione',
                               'Provincia',
                               'Capoluogo',
                               'Denominazione comune',
                               'Codice comune Istat',
                               2019,
                               2021,
                               2022,
                               2023,
                               None],
                    'footers': ['Fonte: Elaborazione su dati Istat - Censimento permanente della popolazione '
                                'e delle abitazioni. Data warehouse Censimenti Permanenti.',
                                'Algoritmo/caratteristiche dei dati:  Occupati 15 anni e più / Popolazione '
                                '15 anni e più*100.'],
                    'transform': 'identity',
                    'extractedRowsSha256': '6c6b8c91ab062f636afda07974f3ab2f14af4aba247acf3a507346193fde6dcf'},
 'unemploymentRate': {'workbook': 'labour',
                      'sheet': 'Tav. 2.1 Comuni',
                      'partKey': '15plus|total',
                      'years': [2019, 2021, 2022, 2023],
                      'title': 'Tavola 2.1 - Tasso di disoccupazione per comune. Anni 2019, 2021-2023',
                      'header': ['Ripartizione',
                                 'Codice regione',
                                 'Denominazione regione',
                                 'Provincia',
                                 'Capoluogo',
                                 'Denominazione comune',
                                 'Codice comune Istat',
                                 2019,
                                 2021,
                                 2022,
                                 2023],
                      'footers': ['Fonte: Elaborazione su dati Istat - Censimento permanente della '
                                  'popolazione e delle abitazioni. Data warehouse Censimenti Permanenti.',
                                  'Algoritmo/caratteristiche dei dati: Disoccupati 15 anni e più / Forza '
                                  'Lavoro 15 anni e più *100.'],
                      'transform': 'identity',
                      'extractedRowsSha256': '1307e854a355ad7b6173920eb9f9a2e7c777f5fbab57f4c8c26fafad15cb36af'},
 'activityRate': {'workbook': 'labour',
                  'sheet': 'Tav. 3.1 Comuni',
                  'partKey': '15plus|total',
                  'years': [2019, 2021, 2022, 2023],
                  'title': 'Tavola 3.1 - Tasso di inattività per comune. Anni 2019, 2021-2023',
                  'header': ['Ripartizione',
                             'Codice regione',
                             'Denominazione regione',
                             'Provincia',
                             'Capoluogo',
                             'Denominazione comune',
                             'Codice comune Istat',
                             2019,
                             2021,
                             2022,
                             2023,
                             None],
                  'footers': ['Fonte: Elaborazione su dati Istat - Censimento permanente della popolazione e '
                              'delle abitazioni. Data warehouse Censimenti Permanenti.',
                              'Algoritmo/caratteristiche dei dati: Popolazione non appartenente alle forze '
                              'di lavoro 15 anni e più / Popolazione residente 15 anni e più *100.'],
                  'transform': '100-minus-native',
                  'extractedRowsSha256': 'e301aba85d77368d34c82203d495883c5469b86f1f60fc5c802840eee7d11ac8'},
 'diplomaPlus': {'workbook': 'education',
                 'sheet': 'Tav. 4.1 Comuni',
                 'partKey': '25-49|total',
                 'years': [2018, 2019, 2020, 2021, 2022, 2023],
                 'title': 'Tavola 4.1 - Incidenza del conseguimento almeno del titolo secondario per comune. '
                          'Anni 2018-2023',
                 'header': ['Ripartizione',
                            'Codice regione',
                            'Denominazione regione',
                            'Provincia',
                            'Capoluogo',
                            'Denominazione comune',
                            'Codice comune Istat',
                            2018,
                            2019,
                            2020,
                            2021,
                            2022,
                            2023],
                 'footers': ['Fonte: Elaborazione su dati Istat - Censimento permanente della popolazione e '
                             'delle abitazioni. Data warehouse Censimenti Permanenti.',
                             'Algoritmo/caratteristiche dei dati: Persone di 25-49 anni che hanno completato '
                             'almeno la scuola secondaria di II grado (titolo non inferiore a Isced 3) / '
                             'Totale delle persone di 25-49 anni*100.'],
                 'transform': 'identity',
                 'extractedRowsSha256': '1c9363ba9986c7ec02f10b8128f5798b91c71d08669ecacb5a52799b3351f4eb'},
 'tertiary': {'workbook': 'education',
              'sheet': 'Tav. 5.1 Comuni',
              'partKey': '25-49|total',
              'years': [2018, 2019, 2020, 2021, 2022, 2023],
              'title': 'Tavola 5.1 - Incidenza del conseguimento del titolo terziario per comune. Anni '
                       '2018-2023',
              'header': ['Ripartizione',
                         'Codice regione',
                         'Denominazione regione',
                         'Provincia',
                         'Capoluogo',
                         'Denominazione comune',
                         'Codice comune Istat',
                         2018,
                         2019,
                         2020,
                         2021,
                         2022,
                         2023],
              'footers': ['Fonte: Elaborazione su dati Istat - Censimento permanente della popolazione e '
                          'delle abitazioni. Data warehouse Censimenti Permanenti.',
                          'Algoritmo/caratteristiche dei dati: Persone di 25-49 anni che hanno conseguito un '
                          'titolo di livello terziario (Isced 5, 6, 7 o 8) / Totale delle persone di 25-49 '
                          'anni * 100.'],
              'transform': 'identity',
              'extractedRowsSha256': '86ac7cbcbd89bcf64dff6a2390296c0f1ee631ef194528eb129de8d80c6795aa'}}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(f"Istat history: {message}")


def number(value: object) -> float:
    require(type(value) in (int, float) and math.isfinite(value), f"invalid number {value!r}")
    return float(value)


def close(actual: object, expected: float, label: str) -> None:
    require(math.isclose(number(actual), expected, rel_tol=0, abs_tol=1e-9), f"mismatch {label}")


def native_history(snapshot: dict, reference: dict) -> dict[str, list[float]]:
    history = snapshot.get("historicalDiploma", {})
    require(history.get("indicator") == INDICATOR and history.get("years") == [1991, 2001, 2011]
            and history.get("scope") == "25–64 anni, totale residenti", "historical definition changed")
    expected = {raw["code"]: town for town, raw in reference["towns"].items()}
    candidates = history.get("towns", {})
    require(len(expected) == 7 and len(set(expected.values())) == 7 and set(candidates) == set(expected),
            "native municipal scope incomplete or duplicated")
    result = {}
    for code, town in expected.items():
        candidate = candidates[code]
        require(candidate.get("town") == town and candidate.get("encoding") == "cp1252", "native identity changed")
        require(candidate.get("url") == f"https://ottomilacensus.istat.it/fileadmin/dati/csv/{code[:3]}/dati_{code[:3]}_{code[3:]}_010.csv",
                f"uncertified native URL {code}")
        try:
            body = base64.b64decode(candidate["rawCsvBase64"], validate=True)
        except (KeyError, ValueError) as error:
            raise RuntimeError(f"Istat history: invalid native CSV {code}") from error
        require(hashlib.sha256(body).hexdigest() == candidate.get("sha256") and len(body) == candidate.get("bytes"),
                f"native source hash/size mismatch {code}")
        reader = csv.DictReader(io.StringIO(body.decode("cp1252")), delimiter=";")
        require(reader.fieldnames == ["Descrizione tema", "Descrizione sottotema", "Nome indicatore", "Denominazione11", "AnnoCP", "Value"],
                f"native CSV schema mismatch {code}")
        records = list(reader)
        require(records == candidate.get("records"), f"native CSV replay mismatch {code}")
        values = []
        for label, years in ((town, [1991, 2001, 2011]), ("Toscana", [2011]), ("Italia", [2011])):
            for year in years:
                selected = [row for row in records if row["Nome indicatore"] == INDICATOR
                            and row["Denominazione11"] == label and row["AnnoCP"] == str(year)]
                require(len(selected) == 1, f"native observation missing or duplicated {code}/{label}/{year}")
                value = float(selected[0]["Value"].replace(",", "."))
                require(math.isfinite(value) and 0 <= value <= 100, "native percentage outside range")
                if label == town:
                    values.append(value)
                else:
                    close(history["regionalContext2011"]["tuscany" if label == "Toscana" else "italy"], value, label)
        require(candidate.get("years") == [1991, 2001, 2011] and candidate.get("values") == values,
                f"candidate/native observations mismatch {code}")
        result[code] = values
    return result


def validate_current(metric: dict, reference: dict, key: str) -> None:
    require(str(metric.get("meta", {}).get("year")) == "2024"
            and metric["meta"].get("unit") == "percent"
            and metric["meta"].get("defaultAge") == "25-64"
            and metric["meta"].get("defaultGender") == "total", f"current definition changed {key}")
    expected = {raw["code"]: town for town, raw in reference["towns"].items()}
    rows = metric.get("rows", [])
    require(len(rows) == 7 and {row.get("code") for row in rows} == set(expected)
            and {row.get("town") for row in rows} == set(expected.values()), f"current coverage changed {key}")
    for row in rows:
        town = expected[row["code"]]
        require(row["town"] == town, "town/code mismatch")
        raw = reference["towns"][town]["education" if key in {"diplomaPlus", "tertiary"} else "labour"]
        field = "diplomaPlus" if key == "diplomaPlus" else "tertiaryRate" if key == "tertiary" else key
        close(row.get("value"), round(raw["25-64"]["total"][field], 1), f"{key}/{town}/current")
        parts = row.get("parts", [])
        expected_parts = {f"{age}|{gender}" for age, genders in raw.items() for gender in genders}
        require(len(parts) == len(expected_parts) and {part.get("key") for part in parts} == expected_parts,
                f"current component coverage changed {key}/{town}")
        for part in parts:
            age, gender = part["key"].split("|")
            require(part.get("ageKey") == age and part.get("genderKey") == gender, "component identity mismatch")
            close(part.get("value"), raw[age][gender][field], f"{key}/{town}/{part['key']}")
            numerator_field = "upperSecondaryPlus" if key == "diplomaPlus" else "tertiary" if key == "tertiary" else "employed" if key == "employmentRate" else "unemployed" if key == "unemploymentRate" else "active"
            denominator_field = "active" if key == "unemploymentRate" else "population"
            close(part.get("numerator"), raw[age][gender][numerator_field], "current numerator")
            close(part.get("denominator"), raw[age][gender][denominator_field], "current denominator")


def series(years: list[int], values: list[float], note: str = NOTE) -> dict:
    return {"years": years, "values": values, "source": "Istat — censimenti della popolazione",
            "sourceUrl": "https://ottomilacensus.istat.it/", "sourceSnapshot": SNAPSHOT_REF, "note": note}


def assign_series(target: dict, expected: dict, label: str) -> None:
    empty = {"years": [], "values": [], "note": "Storico non acquisito per questa fascia e questo genere."}
    require(target.get("series") is None or target["series"] in (expected, empty), f"conflicting history {label}")
    target["series"] = expected


def component_histories(snapshot: dict, reference: dict) -> dict:
    expected = {raw["code"]: town for town, raw in reference["towns"].items()}
    require(set(snapshot.get("componentWorkbooks", {})) == set(WORKBOOKS), "workbook coverage changed")
    for key, contract in WORKBOOKS.items():
        book = snapshot["componentWorkbooks"][key]
        require(all(book.get(field) == value for field, value in contract.items()), "workbook provenance changed")
    require(set(snapshot.get("componentHistories", {})) == set(COMPONENTS), "component acquisition incomplete")
    result = {}
    for key, contract in COMPONENTS.items():
        item = snapshot["componentHistories"][key]
        require(all(item.get(field) == value for field, value in contract.items()), f"native component definition changed {key}")
        rows = item.get("rows", [])
        digest = hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        require(digest == item.get("extractedRowsSha256"), f"native extracted rows changed {key}")
        require(len(rows) == 7, f"incomplete native component {key}")
        selected = {}
        positions = set()
        for entry in rows:
            cells = entry.get("cells", [])
            position = entry.get("worksheetRow")
            require(type(position) is int and position > 4 and position not in positions, "invalid native worksheet position")
            positions.add(position)
            require(len(cells) == len(contract["header"]), "native row/header width changed")
            code = str(cells[6])
            require(code in expected and code not in selected and cells[5] == expected[code]
                    and cells[1:4] == ["09", "Toscana", "Lucca"], "native town/code/region mismatch")
            values = [number(cells[7+i]) for i in range(len(contract["years"]))]
            require(all(0 <= value <= 100 for value in values), "native percentage outside range")
            if contract["transform"] == "100-minus-native":
                values = [100 - value for value in values]
            selected[code] = values
        require(set(selected) == set(expected), "native municipal component coverage changed")
        result[key] = selected
    return result


def apply_history(site: dict) -> None:
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    require(snapshot.get("schemaVersion") == 1, "unsupported schema")
    frozen = snapshot.get("referenceSnapshot", {})
    require(frozen.get("path") == str(CURRENT_PATH.relative_to(ROOT)) and frozen.get("year") == 2024
            and frozen.get("sha256") == hashlib.sha256(CURRENT_PATH.read_bytes()).hexdigest(),
            "current reference snapshot changed")
    reference = json.loads(CURRENT_PATH.read_text(encoding="utf-8"))
    historic = native_history(snapshot, reference)
    components = component_histories(snapshot, reference)
    # Validate every current numerator, denominator and value before atomic publication.
    candidate = copy.deepcopy(site)
    for key, contract in COMPONENTS.items():
        metric = candidate["metrics"][key]
        validate_current(metric, reference, key)
        book = WORKBOOKS[contract["workbook"]]
        age = "15 anni e più" if contract["partKey"] == "15plus|total" else "25–49 anni"
        note = (f"Censimento permanente, {age}, totale residenti. {contract['title']}. "
                f"{contract['footers'][1]} "
                + ("Attività = 100 − tasso nativo di inattività. " if key == "activityRate" else "")
                + "2024: componente corrente riconciliata con lo snapshot nativo Istat. "
                "Solo osservazioni native negli anni indicati; nessuna interpolazione o aggregazione storica Versilia.")
        for row in metric["rows"]:
            if key == "diplomaPlus":
                assign_series(row, series([1991, 2001, 2011, 2024], historic[row["code"]] + [row["value"]]), row["town"])
            else:
                require(row.get("series") is None, f"unsupported default history {key}/{row['town']}")
            for part in row["parts"]:
                if part["key"] == contract["partKey"]:
                    expected = series(contract["years"] + [2024], components[key][row["code"]] + [part["value"]], note)
                    expected["sourceUrl"] = book["url"]
                elif key == "diplomaPlus" and part["key"] == DEFAULT_PART:
                    expected = series([1991, 2001, 2011, 2024], historic[row["code"]] + [part["value"]])
                else:
                    expected = {"years": [], "values": [], "note": "Storico non acquisito per questa fascia e questo genere."}
                assign_series(part, expected, f"{key}/{row['town']}/{part['key']}")
    for key in COMPONENTS:
        site["metrics"][key] = candidate["metrics"][key]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "dist/data/site-data.json")
    args = parser.parse_args()
    apply_history(json.loads(args.input.read_text(encoding="utf-8")))
    print("Istat history PASS: diploma 25–64 plus five native component histories, 7/7 towns; check only")
