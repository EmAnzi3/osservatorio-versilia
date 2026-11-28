#!/usr/bin/env python3
"""Personale comunale (RGS, Conto annuale): serie storiche e confronto Toscana/Italia.

Stesse regole dei valori pubblicati (`audit_rgs_amministrazione_values.py`, `rgs-formazione-2024.json`):

- personale al 31 dicembre = somma dei sei campi tempo pieno/part time del file «Occupazione e Turnover»
  per Ente; il Comune è identificato dal Codice Ente BDAP del file dell'anno pubblicato (con lo stesso
  Codice Istituzione in ogni anno);
- struttura per età = dipendenti per fascia del file «Anzianità», sommati in tre macrofasce; vale solo
  se il totale per età coincide con il personale;
- turnover netto = (assunti − passaggi da altre amministrazioni) − (cessati − passaggi ad altre
  amministrazioni), dai file per causale, diviso per il personale; vale solo se le causali sommano ai
  totali del file Turnover (nessuna riga per causale è ammessa solo se quel totale è zero: è uno zero
  dichiarato nel file, non imputato);
- formazione = riga «FUNZIONI LOCALI» dell'API RGS (per i sette Comuni coincide con il totale; nelle
  selezioni con più comparti la riga «TOTALE» somma le medie dei comparti e non è una media).

Per ogni grandezza la serie risale dall'anno pubblicato finché tutti e sette i Comuni sono validi
(anni consecutivi). L'anno pubblicato deve coincidere con i valori del catalogo. Il confronto
Toscana/Italia usa i Comuni con dati validi dell'anno pubblicato, con copertura dichiarata sui
residenti Istat al 1° gennaio (soglia 90%).
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import math
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import Any, Callable
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = "data/source-snapshots/rgs-personale-serie.json"
BENCHMARK = "data/source-snapshots/rgs-personale-benchmark-{year}.json"
FROZEN = "data/source-snapshots/a3-rgs-staff-benchmark-2024.json"
METRIC = "municipalStaffAgeStructure, municipalStaffTurnover, municipalStaffTraining, municipalEmployeesPer1000"
AGE, TURNOVER, TRAINING, PER1000 = ("municipalStaffAgeStructure", "municipalStaffTurnover",
                                    "municipalStaffTraining", "municipalEmployeesPer1000")
METRICS = (AGE, TURNOVER, TRAINING)
FIRST = 2010
MIN_COVERAGE = 0.90
ANAGRAFE_MIN = 5000  # enti attesi nell'Anagrafe BDAP (sono decine di migliaia)
CSV_URL = "https://bdap-opendata.rgs.mef.gov.it/export/csv/{year}---Dipendenti-Pubblici---{name}.csv"
FILES = {
    "turnover": "Occupazione-e-Turnover---Dati-analitici-per-Ente",
    "age": "Anzianita---Dati-analitici-per-Ente",
    "hires": "Assunzioni---Dati-Analitici-per-Causale-Assunzione",
    "cessations": "Cessazioni---Dati-analitici-per-Causale-Cessazione",
}
ANAGRAFE_URLS = ("https://bdap-opendata.rgs.mef.gov.it/export/csv/Anagrafe-Enti---Ente.csv",
                 "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/745861d3-e741-43ff-b68a-7cf357aab888.csv")
TRAINING_API = ("https://contoannuale.rgs.mef.gov.it/o/sico-rest-APIs/sicoAPI/formazione"
                "?anno={year}&tipoIstituzioneFilters=C{filter}")
TRAINING_PAGE = "https://contoannuale.rgs.mef.gov.it/web/sicosito/assenze-e-turnover/formazione-acc"
STAFF_FIELDS = ("Numero Dipendenti Donne Tempo Pieno", "Numero Dipendenti Uomini Tempo Pieno",
                "Numero Dipendenti Donne Part time Inf. 50%", "Numero Dipendenti Uomini Part time Inf. 50%",
                "Numero Dipendenti Donne Part time Sup. 50%", "Numero Dipendenti Uomini Part time Sup. 50%")
HIRE_FIELDS = ("Numero Dipendenti Donne Assunte", "Numero Dipendenti Uomini Assunti")
CESS_FIELDS = ("Numero Dipendenti Donne Cessate", "Numero Dipendenti Uomini Cessati")
TOWNS = {"046005": "Camaiore", "046013": "Forte dei Marmi", "046018": "Massarosa", "046024": "Pietrasanta",
         "046028": "Seravezza", "046030": "Stazzema", "046033": "Viareggio"}
TUSCANY = ("045", "046", "047", "048", "049", "050", "051", "052", "053", "100")
# Macrofasce pubblicate, nell'ordine delle parti: (etichetta, minimo, massimo incluso).
AGE_GROUPS = (("55+", 55, 999), ("40–54", 40, 54), ("<40", 0, 39))
TRAINING_PARTS = ("Media totale RGS", "Giornate complessive", "Media uomini", "Media donne")
TOL = 1e-9


class StaffHistoryError(RuntimeError):
    pass


class Unavailable(StaffHistoryError):
    """Il file o l'anno non è pubblicato dalla fonte."""


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def number(value: Any) -> float:
    raw = str(value or "").strip().replace(" ", "").replace(" ", "")
    if not raw:
        return 0.0
    if "," in raw and "." not in raw:
        raw = raw.replace(",", ".")
    return float(raw)


def _text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            return raw.decode(encoding).replace("\x00", "")
        except UnicodeDecodeError:
            continue
    raise StaffHistoryError("codifica CSV non riconosciuta")


def _rows(raw: bytes, label: str):
    """Righe COMUNI del CSV RGS come dizionari (lettura in streaming)."""
    text = _text(raw)
    if not text.lstrip().startswith('"Anno Rilevazione"'):
        raise Unavailable(f"{label}: risposta non CSV ({text[:80]!r})")
    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = [re.sub(r"[\t\r\n]+", "", h).strip() for h in next(reader)]  # RGS spezza alcune intestazioni con tabulazioni
    tipo = header.index("Descrizione Tipo Istituzione")
    for values in reader:
        if len(values) > tipo and norm(values[tipo]) == "COMUNI":
            yield dict(zip(header, values))


def age_bounds(label: str) -> tuple[int, int]:
    n = norm(label)
    nums = [int(x) for x in re.findall(r"\d+", n)]
    if n.startswith("FINO A") and len(nums) == 1:
        return 0, nums[0]
    if n.startswith("DA") and len(nums) == 2:
        return nums[0], nums[1]
    if (n.startswith("OLTRE") or n.startswith("PIU DI")) and len(nums) == 1:
        return nums[0] + 1, 999
    raise StaffHistoryError(f"fascia di età non riconosciuta: {label!r}")


def age_group(label: str) -> int:
    lo, hi = age_bounds(label)
    for index, (_, gmin, gmax) in enumerate(AGE_GROUPS):
        if gmin <= lo and hi <= gmax:
            return index
    raise StaffHistoryError(f"fascia {label!r} a cavallo delle macrofasce pubblicate")


def is_transfer(cause: str) -> bool:
    n = norm(cause)
    return "PASSAGGI" in n and "AMMINISTRAZ" in n


def read_year(fetch: Callable[[str], bytes], year: int, keep: set[str] | None) -> dict[str, dict[str, Any]]:
    """Per Ente (Codice Ente BDAP): personale, assunti/cessati lordi, fasce d'età e flussi per causale.
    `keep` limita la lettura agli enti indicati (None = tutti i Comuni)."""
    entities: dict[str, dict[str, Any]] = {}

    def entity(row: dict[str, str]) -> dict[str, Any] | None:
        code = row.get("Codice Ente BDAP", "").strip()
        if not code.isdigit():
            raise StaffHistoryError(f"{year}: Codice Ente BDAP non valido {code!r}")
        if keep is not None and code not in keep:
            return None
        e = entities.setdefault(code, {"institution": row.get("Codice Istituzione", "").strip(), "name": row.get("Descrizione Ente", "").strip(),
                                       "staff": 0.0, "grossHires": 0.0, "grossCessations": 0.0, "turnoverRows": 0,
                                       "age": [0.0, 0.0, 0.0], "bands": {}, "ageRows": 0, "hires": [0.0, 0.0, 0], "cessations": [0.0, 0.0, 0]})
        if e["institution"] != row.get("Codice Istituzione", "").strip():
            raise StaffHistoryError(f"{year} {code}: Codice Istituzione incoerente")
        return e

    with ThreadPoolExecutor(max_workers=len(FILES)) as pool:  # il portale è lento: i quattro file in parallelo
        raws = dict(zip(FILES, pool.map(fetch, [CSV_URL.format(year=year, name=name) for name in FILES.values()])))
    for row in _rows(raws["turnover"], f"{year} turnover"):
        if row.get("Anno Rilevazione", "").strip() != str(year):
            raise StaffHistoryError(f"{year}: anno di rilevazione diverso nel file turnover")
        e = entity(row)
        if e is None:
            continue
        e["staff"] += sum(number(row.get(f)) for f in STAFF_FIELDS)
        e["grossHires"] += sum(number(row.get(f)) for f in HIRE_FIELDS)
        e["grossCessations"] += sum(number(row.get(f)) for f in CESS_FIELDS)
        e["turnoverRows"] += 1
    for row in _rows(raws["age"], f"{year} età"):
        e = entity(row)
        if e is None:
            continue
        label, count = row.get("Descrizione Fascia Eta", ""), number(row.get("Numero Dipendenti Donne")) + number(row.get("Numero Dipendenti Uomini"))
        e["age"][age_group(label)] += count
        lo = str(age_bounds(label)[0])
        e["bands"][lo] = e["bands"].get(lo, 0.0) + count
        e["ageRows"] += 1
    for key in ("hires", "cessations"):
        for row in _rows(raws[key], f"{year} {key}"):
            e = entity(row)
            if e is None:
                continue
            count = number(row.get("Donne")) + number(row.get("Uomini"))
            e[key][0] += count
            if is_transfer(row.get("Descrizione Causale", "")):
                e[key][1] += count
            e[key][2] += 1
    sources = {key: {"url": CSV_URL.format(year=year, name=name), "sha256": hashlib.sha256(raws[key]).hexdigest(), "bytes": len(raws[key])}
               for key, name in FILES.items()}
    return {"entities": entities, "sources": sources}


def age_valid(e: dict[str, Any]) -> bool:
    return e["staff"] > 0 and e["ageRows"] > 0 and math.isclose(sum(e["age"]), e["staff"], rel_tol=0, abs_tol=1e-6)


def cohort_consistent(before: dict[str, Any], after: dict[str, Any]) -> bool:
    """Coerenza delle fasce tra due anni consecutivi (condizioni necessarie, nessuna stima): chi ha almeno 55 (40)
    anni resta nella fascia finché è in servizio, quindi la fascia cala al più dei cessati dell'anno; cresce al più
    dei dipendenti della fascia quinquennale precedente (50–54, 35–39) più gli assunti dell'anno."""
    def above(e: dict[str, Any], lo: int) -> float:
        return sum(v for k, v in e["bands"].items() if int(k) >= lo)
    # Una fascia assente nel file vale zero: il totale per età è già riconciliato con il personale (age_valid).
    for lo, prev in ((55, "50"), (40, "35")):
        if above(after, lo) < above(before, lo) - after["grossCessations"] - 1e-6:
            return False
        if above(after, lo) > above(before, lo) + before["bands"].get(prev, 0.0) + after["grossHires"] + 1e-6:
            return False
    return True


def flows_valid(e: dict[str, Any]) -> bool:
    if e["staff"] <= 0:
        return False
    for key, gross in (("hires", e["grossHires"]), ("cessations", e["grossCessations"])):
        total, _, rows = e[key]
        if rows == 0 and gross != 0:
            return False
        if not math.isclose(total, gross, rel_tol=0, abs_tol=1e-6):
            return False
    return True


def net_flows(e: dict[str, Any]) -> tuple[float, float]:
    return e["hires"][0] - e["hires"][1], e["cessations"][0] - e["cessations"][1]


def _api(fetch: Callable[[str], bytes], year: int, codes: list[str] | None) -> dict[str, Any] | None:
    flt = "" if codes is None else "&istituzioneFilters=" + ",".join(codes)
    url = TRAINING_API.format(year=year, filter=flt)
    payload = json.loads(_text(fetch(url)))
    if str(payload.get("anno")) != str(year):
        raise StaffHistoryError(f"formazione {year}: anno diverso nella risposta")
    rows = {}
    for item in payload.get("ripartizione") or []:
        for label, entries in item.items():
            rows[norm(label)] = entries[0]
    if not rows:
        return None
    fl = rows.get("FUNZIONI LOCALI")
    if fl is None:
        raise StaffHistoryError(f"formazione {year}: riga FUNZIONI LOCALI assente ({sorted(rows)})")
    out = {"totalDays": number(fl["totale"]), "menDays": number(fl["uomini"]), "womenDays": number(fl["donne"]),
           "meanMen": number(fl["media_uomini"]), "meanWomen": number(fl["media_donne"]), "meanTotalRgs": number(fl["media_totale"]),
           "otherComparti": sorted(k for k in rows if k not in ("TOTALE", "FUNZIONI LOCALI")),
           "allCompartiDays": number(rows["TOTALE"]["totale"]) if "TOTALE" in rows else None}
    if not math.isclose(out["menDays"] + out["womenDays"], out["totalDays"], rel_tol=0, abs_tol=1e-6):
        raise StaffHistoryError(f"formazione {year}: uomini + donne ≠ totale")
    return out


def _published(metrics: dict[str, Any]) -> dict[str, Any]:
    """Valori pubblicati dell'anno corrente, per codice Istat del Comune."""
    age = {r["code"]: {"staff": r["staffAt31Dec"], "counts": [p["count"] for p in r["parts"]]} for r in metrics[AGE]["rows"]}
    turnover = {r["code"]: {"netHires": r["netHires"], "netCessations": r["netCessations"], "value": r["value"]} for r in metrics[TURNOVER]["rows"]}
    training = {r["code"]: [p["value"] for p in r["parts"]] for r in metrics[TRAINING]["rows"]}
    per1000 = {r["code"]: {"staff": r["staffAt31Dec"], "population": r["residentPopulation"], "value": r["value"]} for r in metrics[PER1000]["rows"]}
    labels = [p["selectorLabel"] for p in metrics[AGE]["rows"][0]["parts"]]
    if labels != [g[0] for g in AGE_GROUPS]:
        raise StaffHistoryError(f"macrofasce pubblicate cambiate: {labels}")
    tlabels = [p["selectorLabel"] for p in metrics[TRAINING]["rows"][0]["parts"]]
    if tlabels != list(TRAINING_PARTS):
        raise StaffHistoryError(f"parti della formazione cambiate: {tlabels}")
    years = {str(metrics[m]["meta"]["year"]) for m in (AGE, TURNOVER, TRAINING, PER1000)}
    if len(years) != 1:
        raise StaffHistoryError(f"anni pubblicati diversi: {years}")
    return {"year": int(years.pop()), "age": age, "turnover": turnover, "training": training, "per1000": per1000,
            "versiliaTraining": [p["value"] for p in metrics[TRAINING]["aggregate"]["parts"]]}


def frozen_population(root: Path = ROOT) -> tuple[dict[str, int], dict[str, str], str]:
    """Residenti Istat al 1° gennaio 2024 (P2, impronta verificata) e mappa Tuscany Id_Ente → Istat congelate."""
    snap = json.loads((root / FROZEN).read_text(encoding="utf-8"))
    s = snap["source"]
    raw = base64.b64decode(s["populationZipBase64"], validate=True)
    if hashlib.sha256(raw).hexdigest() != s["populationSha256"]:
        raise StaffHistoryError("popolazione Istat congelata: impronta diversa")
    with ZipFile(io.BytesIO(raw)) as archive:
        text = archive.read("P2_2024_it_Comuni.csv").decode("utf-8-sig")
    lines = text.splitlines()
    population = {}
    for row in csv.DictReader(io.StringIO("\n".join(lines[1:])), delimiter=";"):
        population[row["Codice comune"]] = int(row["Popolazione censita al 1° gennaio - Totale"])
    tuscany = {g["Id_Ente"]: g["Codice_ISTAT_Comune"] for g in snap["geographies"]}
    return population, tuscany, s["populationUrl"]


def read_anagrafe(fetch: Callable[[str], bytes]) -> tuple[dict[str, str], str, str]:
    """Id_Ente → codice Istat del Comune, dall'Anagrafe Enti BDAP."""
    errors = []
    for url in ANAGRAFE_URLS:
        try:
            raw = fetch(url)
        except Exception as error:  # noqa: BLE001 - si prova l'indirizzo alternativo
            errors.append(f"{url}: {error}")
            continue
        text = _text(raw)
        if not text.lstrip().startswith('"Id_Ente"') and not text.lstrip().startswith("Id_Ente"):
            errors.append(f"{url}: risposta non CSV ({text[:60]!r})")
            continue
        mapping = {}
        for row in csv.DictReader(io.StringIO(text), delimiter=";" if text.split("\n", 1)[0].count(";") else ","):
            ident, code = str(row.get("Id_Ente") or "").strip(), str(row.get("Codice_ISTAT_Comune") or "").strip()
            if ident and code.isdigit():
                mapping[ident] = code.zfill(6)
        if len(mapping) < ANAGRAFE_MIN:
            errors.append(f"{url}: copertura inattesa {len(mapping)}")
            continue
        return mapping, url, hashlib.sha256(raw).hexdigest()
    raise StaffHistoryError("Anagrafe Enti BDAP non disponibile: " + "; ".join(errors))


def _scope(entities: dict[str, Any], codes: dict[str, str], population: dict[str, int], valid: Callable[[dict], bool], tuscany: bool) -> dict[str, Any]:
    """Comuni del territorio coperti: ente presente nel file e valido (o con zero dipendenti dichiarati)."""
    territory = {c for c in population if c[:3] in TUSCANY or not tuscany}
    covered, used = set(), []
    for ident, e in entities.items():
        istat = codes.get(ident)
        if istat not in territory:
            continue
        if e["staff"] == 0 and e["turnoverRows"] > 0:
            covered.add(istat)
        elif valid(e):
            covered.add(istat)
            used.append(e)
    total = sum(population[c] for c in territory)
    share = sum(population[c] for c in covered) / total
    return {"entities": used, "municipalities": len(covered), "municipalitiesTotal": len(territory),
            "residentsCovered": sum(population[c] for c in covered), "residentsTotal": total, "coverageShare": share}


def build_snapshots(fetch: Callable[[str], bytes], metrics: dict[str, Any], root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    pub = _published(metrics)
    last = pub["year"]
    population, tuscany_ids, population_url = frozen_population(root)
    anagrafe, anagrafe_url, anagrafe_sha = read_anagrafe(fetch)
    for ident, code in tuscany_ids.items():
        if anagrafe.get(ident) != code:
            raise StaffHistoryError(f"Anagrafe: {ident} → {anagrafe.get(ident)} ≠ {code} congelato")
    current = read_year(fetch, last, None)
    ents = current["entities"]
    town_ids: dict[str, str] = {}
    for ident, e in ents.items():
        code = anagrafe.get(ident)
        if code in TOWNS:
            if code in town_ids:
                raise StaffHistoryError(f"{TOWNS[code]}: più enti RGS")
            town_ids[code] = ident
    if set(town_ids) != set(TOWNS):
        raise StaffHistoryError(f"Comuni assenti nel file {last}: {sorted(set(TOWNS) - set(town_ids))}")
    for code, ident in town_ids.items():
        e = ents[ident]
        if not (age_valid(e) and flows_valid(e)):
            raise StaffHistoryError(f"{TOWNS[code]} {last}: file non riconciliati")
        if e["staff"] != pub["age"][code]["staff"] or e["staff"] != pub["per1000"][code]["staff"]:
            raise StaffHistoryError(f"{TOWNS[code]} {last}: personale {e['staff']} ≠ pubblicato")
        if [round(x) for x in e["age"]] != pub["age"][code]["counts"]:
            raise StaffHistoryError(f"{TOWNS[code]} {last}: fasce {e['age']} ≠ pubblicate {pub['age'][code]['counts']}")
        nh, nc = net_flows(e)
        if (nh, nc) != (pub["turnover"][code]["netHires"], pub["turnover"][code]["netCessations"]):
            raise StaffHistoryError(f"{TOWNS[code]} {last}: flussi netti {(nh, nc)} ≠ pubblicati")
    keep = set(town_ids.values())
    per_year = {last: {"entities": {i: ents[i] for i in keep}, "sources": current["sources"]}}
    stop: dict[str, str | None] = {"staff": None, "age": None, "turnover": None}
    for year in range(last - 1, FIRST - 1, -1):
        try:
            data = read_year(fetch, year, keep)
        except Unavailable as error:
            for k in stop:
                stop[k] = stop[k] or f"{year}: {error}"
            break
        per_year[year] = data
    def consecutive(check: Callable[[dict], bool], key: str, link: Callable[[dict, dict], bool] | None = None) -> list[int]:
        years = []
        for year in sorted(per_year, reverse=True):
            bad = [TOWNS[c] for c, i in town_ids.items() if i not in per_year[year]["entities"] or not check(per_year[year]["entities"][i])
                   or (link and years and not link(per_year[year]["entities"][i], per_year[years[-1]]["entities"][i]))]
            if bad:
                stop[key] = f"{year}: non valido per {bad}"
                break
            years.append(year)
        return sorted(years)
    staff_years = consecutive(lambda e: e["staff"] > 0, "staff")
    age_years = consecutive(age_valid, "age", cohort_consistent)
    turnover_years = consecutive(flows_valid, "turnover")
    institutions = {c: ents[i]["institution"] for c, i in town_ids.items()}
    for year, data in per_year.items():
        for c, i in town_ids.items():
            e = data["entities"].get(i)
            if e and e["institution"] != institutions[c]:
                raise StaffHistoryError(f"{TOWNS[c]} {year}: Codice Istituzione cambiato")
    # Formazione: API RGS, riga FUNZIONI LOCALI, Comune per Comune.
    training: dict[int, dict[str, Any]] = {}
    training_stop = None
    for year in range(last, FIRST - 3, -1):
        values = {}
        for c in TOWNS:
            values[c] = _api(fetch, year, [institutions[c]])
        missing = [TOWNS[c] for c, v in values.items() if v is None]
        if missing:
            if year == last:
                raise StaffHistoryError(f"formazione {last}: Comuni assenti {missing}")
            training_stop = f"{year}: nessun dato per {missing}"
            break
        training[year] = values
    for c, parts in pub["training"].items():
        v = training[last][c]
        live = [v["meanTotalRgs"], v["totalDays"], v["meanMen"], v["meanWomen"]]
        if any(not math.isclose(a, b, rel_tol=0, abs_tol=TOL) for a, b in zip(live, parts)):
            raise StaffHistoryError(f"{TOWNS[c]} formazione {last}: {live} ≠ pubblicato {parts}")
    def town_series(year_list: list[int], fn: Callable[[dict], Any]) -> dict[str, dict[str, Any]]:
        return {TOWNS[c]: {str(y): fn(per_year[y]["entities"][i]) for y in year_list} for c, i in town_ids.items()}
    history = {
        "schemaVersion": 1, "version": f"rgs-personale-serie-{FIRST}-{last}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Ragioneria Generale dello Stato — Conto Annuale (OpenBDAP e API formazione)",
        "years": sorted(set(staff_years) | set(age_years) | set(turnover_years) | set(training)),
        "rule": ("Comuni identificati dal Codice Ente BDAP dell'anno pubblicato; per ogni grandezza anni consecutivi "
                 "fino all'anno pubblicato con 7/7 Comuni validi; anno pubblicato identico ai valori del catalogo."),
        "institutions": {TOWNS[c]: {"bdap": i, "institution": institutions[c]} for c, i in town_ids.items()},
        "sources": {str(y): d["sources"] for y, d in sorted(per_year.items())},
        "staff": {"years": staff_years, "stoppedAt": stop["staff"], "towns": town_series(staff_years, lambda e: e["staff"])},
        "age": {"years": age_years, "stoppedAt": stop["age"], "groups": [g[0] for g in AGE_GROUPS],
                "towns": town_series(age_years, lambda e: [e["age"][0], e["age"][1], e["age"][2]])},
        "turnover": {"years": turnover_years, "stoppedAt": stop["turnover"],
                     "towns": town_series(turnover_years, lambda e: {"staff": e["staff"], "netHires": net_flows(e)[0], "netCessations": net_flows(e)[1]})},
        "training": {"years": sorted(training), "stoppedAt": training_stop, "api": TRAINING_API.format(year="{year}", filter="&istituzioneFilters={codes}"),
                     "towns": {TOWNS[c]: {str(y): {k: training[y][c][k] for k in ("meanTotalRgs", "totalDays", "meanMen", "meanWomen")} for y in sorted(training)} for c in TOWNS}},
        "qualityGate": {"status": "PASS", "note": f"Anno {last} identico ai valori pubblicati per i 7 Comuni (personale, fasce, flussi netti, formazione)."},
    }
    # Confronto Toscana/Italia dell'anno pubblicato.
    benchmarks: dict[str, Any] = {}
    for scope, is_tuscany in (("tuscany", True), ("italy", False)):
        age_scope = _scope(ents, anagrafe, population, age_valid, is_tuscany)
        flow_scope = _scope(ents, anagrafe, population, flows_valid, is_tuscany)
        counts = [sum(e["age"][k] for e in age_scope["entities"]) for k in range(3)]
        staff_age = sum(counts)
        staff_flow = sum(e["staff"] for e in flow_scope["entities"])
        net = sum(net_flows(e)[0] - net_flows(e)[1] for e in flow_scope["entities"])
        entry = {
            "age": {k: v for k, v in age_scope.items() if k != "entities"} | {"staff": staff_age, "counts": counts,
                    "shares": [x / staff_age * 100 for x in counts] if age_scope["coverageShare"] >= MIN_COVERAGE else None},
            "turnover": {k: v for k, v in flow_scope.items() if k != "entities"} | {"staff": staff_flow, "netTurnoverHeadcount": net,
                         "rate": net / staff_flow * 100 if flow_scope["coverageShare"] >= MIN_COVERAGE else None},
        }
        present = _scope(ents, anagrafe, population, lambda e: e["staff"] > 0, is_tuscany)
        if is_tuscany:
            inst = sorted({e["institution"] for e in present["entities"]}, key=int)
            entry["training"] = _api(fetch, last, inst) | {"institutions": len(inst), "coverageShare": present["coverageShare"]}
        else:
            entry["training"] = _api(fetch, last, None) | {"institutions": None, "coverageShare": present["coverageShare"]}
        benchmarks[scope] = entry
    versilia = _api(fetch, last, [institutions[c] for c in TOWNS])
    live = [versilia["meanTotalRgs"], versilia["totalDays"], versilia["meanMen"], versilia["meanWomen"]]
    if any(not math.isclose(a, b, rel_tol=0, abs_tol=TOL) for a, b in zip(live, pub["versiliaTraining"])):
        raise StaffHistoryError(f"formazione Versilia {last}: {live} ≠ pubblicato {pub['versiliaTraining']}")
    benchmark = {
        "schemaVersion": 1, "version": f"rgs-personale-benchmark-{last}-v1", "retrieved": date.today().isoformat(), "year": last,
        "publisher": "Ragioneria Generale dello Stato — Conto Annuale", "sources": current["sources"],
        "anagrafe": {"url": anagrafe_url, "sha256": anagrafe_sha}, "population": {"url": population_url, "note": "residenti al 1° gennaio, P2 Istat congelato in " + FROZEN},
        "trainingApi": TRAINING_API, "trainingPage": TRAINING_PAGE,
        "rule": ("Somma sui Comuni del territorio con dati validi (stesse regole dei valori comunali); copertura = quota dei residenti "
                 "nei Comuni coperti (ente presente con dati riconciliati o zero dipendenti); pubblicato con almeno il 90%. Formazione: "
                 "riga FUNZIONI LOCALI dell'API RGS sulla selezione dei Comuni toscani con personale e sulla selezione nazionale."),
        "benchmarks": benchmarks,
        "versiliaTrainingCheck": versilia,
        "qualityGate": {"status": "PASS", "note": f"Valori {last} dei 7 Comuni e aggregato Versilia della formazione identici ai pubblicati."},
    }
    return history, benchmark


# ------------------------------------------------------------------ materializzazione

def _fmt(value: float, digits: int = 1) -> str:
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def apply(metrics: dict[str, Any], snapshot: dict[str, Any], path: str) -> None:
    """Serie annuali dei quattro indicatori del personale; l'ultimo anno deve coincidere con i valori pubblicati."""
    year = str(metrics[AGE]["meta"]["year"])
    age, turnover, staff, training = snapshot["age"], snapshot["turnover"], snapshot["staff"], snapshot["training"]
    for block in (age, turnover, staff, training):
        if block["years"] and str(block["years"][-1]) != year:
            raise StaffHistoryError("serie non allineata all'anno pubblicato")
    # Struttura per età: una serie per macrofascia.
    m = metrics[AGE]
    if len(age["years"]) > 1:
        for row in m["rows"]:
            counts = age["towns"][row["town"]]
            shares = {str(y): [x / sum(counts[str(y)]) * 100 for x in counts[str(y)]] for y in age["years"]}
            for i, part in enumerate(row["parts"]):
                if not math.isclose(shares[year][i], part["value"], rel_tol=0, abs_tol=1e-9):
                    raise StaffHistoryError(f"{row['town']}: quota {part['label']} non coincide")
            row["componentSeries"] = {p["selectorLabel"]: {"years": list(age["years"]), "values": [shares[str(y)][i] for y in age["years"]]}
                                      for i, p in enumerate(row["parts"])}
            row["series"] = row["componentSeries"][row["parts"][0]["selectorLabel"]]
        m["method"]["historyNote"] = (f"Serie {age['years'][0]}–{age['years'][-1]} dai file RGS «Anzianità» per Ente di ciascun anno, "
                                      "stesse macrofasce; anni in cui per tutti e sette i Comuni il totale per età coincide con il personale al 31 dicembre "
                                      "e le fasce sono coerenti con l'anno precedente (55+ e 40+ calano al più dei cessati e crescono al più della "
                                      "fascia quinquennale precedente più gli assunti).")
    # Turnover netto.
    m = metrics[TURNOVER]
    if len(turnover["years"]) > 1:
        for row in m["rows"]:
            t = turnover["towns"][row["town"]]
            values = [(t[str(y)]["netHires"] - t[str(y)]["netCessations"]) / t[str(y)]["staff"] * 100 for y in turnover["years"]]
            if not math.isclose(values[-1], row["value"], rel_tol=0, abs_tol=1e-9):
                raise StaffHistoryError(f"{row['town']}: turnover non coincide")
            row["series"] = {"years": list(turnover["years"]), "values": values}
        m["method"]["historyNote"] = (f"Serie {turnover['years'][0]}–{turnover['years'][-1]} dai file RGS «Assunzioni» e «Cessazioni» per causale "
                                      "di ciascun anno, al netto dei passaggi tra amministrazioni; anni in cui per tutti e sette i Comuni le causali "
                                      "sommano ai totali del file Turnover.")
    # Dipendenti per 1.000 residenti: personale RGS / popolazione residente al 1° gennaio già pubblicata nel catalogo.
    m = metrics[PER1000]
    pop = {r["town"]: dict(zip(map(str, r["series"]["years"]), r["series"]["values"])) for r in metrics["population"]["rows"]}
    years = [y for y in staff["years"] if all(str(y) in pop[t] for t in pop)]
    if len(years) > 1:
        for row in m["rows"]:
            if pop[row["town"]][year] != row["residentPopulation"]:
                raise StaffHistoryError(f"{row['town']}: popolazione {year} diversa dal denominatore pubblicato")
            values = [staff["towns"][row["town"]][str(y)] / pop[row["town"]][str(y)] * 1000 for y in years]
            if not math.isclose(values[-1], row["value"], rel_tol=0, abs_tol=1e-9):
                raise StaffHistoryError(f"{row['town']}: dipendenti per 1.000 non coincide")
            row["series"] = {"years": years, "values": values}
        m["method"]["historyNote"] = (f"Serie {years[0]}–{years[-1]}: personale RGS al 31 dicembre di ciascun anno diviso per i residenti al "
                                      "1° gennaio dello stesso anno dell'indicatore «Popolazione residente»; il 2021 segue la ricostruzione "
                                      "censuaria della popolazione.")
    # Formazione: una serie per lettura.
    m = metrics[TRAINING]
    if len(training["years"]) > 1:
        keys = ("meanTotalRgs", "totalDays", "meanMen", "meanWomen")
        for row in m["rows"]:
            t = training["towns"][row["town"]]
            for i, part in enumerate(row["parts"]):
                if not math.isclose(t[year][keys[i]], part["value"], rel_tol=0, abs_tol=1e-9):
                    raise StaffHistoryError(f"{row['town']}: formazione {part['label']} non coincide")
            row["componentSeries"] = {p["selectorLabel"]: {"years": list(training["years"]), "values": [t[str(y)][keys[i]] for y in training["years"]]}
                                      for i, p in enumerate(row["parts"])}
            row["series"] = row["componentSeries"][row["parts"][0]["selectorLabel"]]
        m["method"]["historyNote"] = (f"Serie {training['years'][0]}–{training['years'][-1]} dall'API formazione RGS, riga «Funzioni locali» "
                                      "di ciascun Comune (per i sette Comuni coincide con il totale); valori come pubblicati da RGS.")
    for key in (AGE, TURNOVER, TRAINING, PER1000):
        metrics[key]["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path


def apply_benchmark(key: str, metric: dict[str, Any], snap: dict[str, Any], path: str) -> None:
    year = int(metric["meta"]["year"])
    if snap["year"] != year:
        raise StaffHistoryError("confronto non allineato all'anno pubblicato")
    t, i = snap["benchmarks"]["tuscany"], snap["benchmarks"]["italy"]
    pct = lambda x: _fmt(x * 100)
    n = lambda x: _fmt(x, 0)
    base = {"year": str(year), "sourceSnapshot": path}
    if key == AGE:
        label = metric["rows"][0]["parts"][0]["label"]
        a, b = t["age"], i["age"]
        metric["meta"]["benchmark"] = base | {
            "tuscany": a["shares"][0] if a["shares"] else None, "italy": b["shares"][0] if b["shares"] else None,
            "source": "Ragioneria Generale dello Stato — Conto Annuale, Anzianità per Ente", "url": snap["sources"]["age"]["url"],
            "part": label, "parts": {"tuscany": a["shares"], "italy": b["shares"]},
            "note": (f"Confronto riferito alla quota «{label}». Somma dei dipendenti per fascia dei Comuni del territorio in cui il totale per età "
                     f"coincide con il personale: Toscana {n(a['municipalities'])} Comuni su {n(a['municipalitiesTotal'])} ({pct(a['coverageShare'])}% "
                     f"dei residenti), Italia {n(b['municipalities'])} su {n(b['municipalitiesTotal'])} ({pct(b['coverageShare'])}%). Anche la quota "
                     "Versilia è calcolata sul totale dei dipendenti dei sette Comuni."),
        }
    elif key == TURNOVER:
        a, b = t["turnover"], i["turnover"]
        metric["meta"]["benchmark"] = base | {
            "tuscany": a["rate"], "italy": b["rate"],
            "source": "Ragioneria Generale dello Stato — Conto Annuale, Assunzioni e Cessazioni per causale", "url": snap["sources"]["turnover"]["url"],
            "note": (f"Saldo tra assunti e cessati al netto dei passaggi tra amministrazioni, sommato sui Comuni del territorio con causali "
                     f"riconciliate e rapportato al loro personale: Toscana {n(a['municipalities'])} Comuni su {n(a['municipalitiesTotal'])} "
                     f"({pct(a['coverageShare'])}% dei residenti), Italia {n(b['municipalities'])} su {n(b['municipalitiesTotal'])} "
                     f"({pct(b['coverageShare'])}%). Lo zero è ammesso solo quando il file Turnover dichiara zero assunti o cessati."),
        }
    elif key == TRAINING:
        label = metric["rows"][0]["parts"][0]["label"]
        a, b = t["training"], i["training"]
        ok = lambda e: e["meanTotalRgs"] if e["coverageShare"] >= MIN_COVERAGE else None
        metric["meta"]["benchmark"] = base | {
            "tuscany": ok(a), "italy": ok(b),
            "source": "Ragioneria Generale dello Stato — Conto Annuale, formazione", "url": snap["trainingPage"], "part": label,
            "note": (f"Confronto riferito alla «{label}», valore restituito dall'API RGS per il comparto Funzioni locali: Toscana selezionando "
                     f"i {n(a['institutions'])} Comuni toscani con personale ({pct(a['coverageShare'])}% dei residenti), Italia sull'insieme "
                     "dei Comuni. Si usa la riga Funzioni locali perché, con più comparti selezionati, la riga totale RGS somma le medie dei "
                     "comparti; per i sette Comuni le due righe coincidono."),
        }
    else:
        raise StaffHistoryError(f"metrica senza confronto: {key}")
