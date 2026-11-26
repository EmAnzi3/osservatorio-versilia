#!/usr/bin/env python3
"""Serie storica semestrale delle quotazioni residenziali OMI dei sette Comuni.

Stessa regola del semestre pubblicato (`update_omi`): per ogni zona il punto medio dell'intervallo
delle «Abitazioni civili» in stato NORMALE, compravendita in €/m² e locazione in €/m² al mese; la
media comunale è la media semplice delle zone con quella riga.

La media comunale è confrontabile nel tempo solo se le zone sono le stesse: per ogni Comune si
risale dal semestre pubblicato finché l'insieme delle zone e l'insieme delle zone con la riga
residenziale restano identici a quelli pubblicati; al primo semestre diverso la serie del Comune si
ferma. Il semestre pubblicato deve riprodurre esattamente i valori di zona del catalogo.
"""
from __future__ import annotations

import math
import time
from datetime import date
from typing import Any, Callable

import update_omi as omi

SNAPSHOT = "data/source-snapshots/omi-residential-serie.json"
METRIC = "omiResidential"


class OmiHistoryError(RuntimeError):
    pass


def read_town(session: Any, semester: str, co: str) -> list[dict[str, Any]]:
    """Zone di un Comune in un semestre, con la stessa lettura di `update_omi.read_semester`."""
    base = {"lingua": "IT", "pr": omi.PROVINCE, "co": co, "anno_semestre": omi.semester_code(semester)}
    page = session.post(omi.SEARCH, {**base, "level": "2"})
    zones = []
    for link, label in omi.options(page, "linkzonastrada"):
        dest = session.post(omi.SEARCH, {**base, "level": "4", "linkzonastrada": link})
        fields = omi.hidden(dest, "risultato.php")
        result = session.post(omi.RESULT, {**fields, "utilizzo": "Residenziale", "bt1": "Mostra valori"})
        zone = {"code": fields.get("codzona") or label.split("/")[0]}
        try:
            parsed = omi.parse_result(result, semester)
            zone.update(residential=True, sale=parsed["sale"], rent=parsed["rent"])
        except omi.OmiError as error:
            if "assente" not in str(error):
                raise
            zone.update(residential=False)
        zones.append(zone)
    return zones


def zone_codes(session: Any, semester: str, co: str) -> list[str]:
    page = session.post(omi.SEARCH, {"lingua": "IT", "pr": omi.PROVINCE, "co": co,
                                     "anno_semestre": omi.semester_code(semester), "level": "2"})
    return sorted(label.split("/")[0] for _, label in omi.options(page, "linkzonastrada"))


def town_series(reader: Callable[[str], list[dict[str, Any]]], codes: Callable[[str], list[str]], semesters: list[str],
                published: dict[str, dict[str, float]], last: str) -> tuple[list[dict[str, Any]], str | None]:
    """Semestri consecutivi (dal più recente) con le stesse zone pubblicate; `published`: zona → {sale, rent}."""
    want_all = sorted(published)
    points: list[dict[str, Any]] = []
    stop = None
    for semester in [s for s in semesters if s <= last]:
        if sorted(codes(semester)) != want_all:
            stop = f"{semester}: zone {sorted(codes(semester))} diverse da {want_all}"
            break
        zones = reader(semester)
        residential = {z["code"]: z for z in zones if z["residential"]}
        if sorted(residential) != want_all:
            stop = f"{semester}: zone residenziali {sorted(residential)} diverse da {want_all}"
            break
        if semester == last:
            for code, value in published.items():
                for field in ("sale", "rent"):
                    if not math.isclose(residential[code][field], value[field], rel_tol=0, abs_tol=1e-9):
                        raise OmiHistoryError(f"{last} {code} {field}: fonte {residential[code][field]} ≠ pubblicato {value[field]}")
        points.append({"semester": semester, "zones": {c: {"sale": z["sale"], "rent": z["rent"]} for c, z in sorted(residential.items())},
                       "saleMean": math.fsum(z["sale"] for z in residential.values()) / len(residential),
                       "rentMean": math.fsum(z["rent"] for z in residential.values()) / len(residential)})
    if not points or points[0]["semester"] != last:
        raise OmiHistoryError(f"semestre pubblicato {last} non letto")
    return points[::-1], stop


def build_snapshot(session: Any, site: dict[str, Any], previous: dict[str, Any] | None = None, deadline: float | None = None) -> dict[str, Any]:
    """Legge i Comuni mancanti; quelli già completi in `previous` (stesso semestre pubblicato) si riprendono.

    La consultazione rallenta dopo molte richieste: se un Comune non si legge o scade `deadline` (secondi),
    lo snapshot resta INCOMPLETE con i Comuni letti, e la corsa successiva riparte dagli altri.
    """
    started = time.monotonic()
    metric = site["metrics"][METRIC]
    last = omi.label_semester(metric["meta"]["year"])
    available = sorted(omi.semesters(session), reverse=True)
    if last not in available:
        raise OmiHistoryError(f"semestre pubblicato {last} assente dalla consultazione")
    cadastral = omi.town_codes(session)
    kept = previous["towns"] if previous and previous.get("lastSemester") == last else {}
    towns: dict[str, Any] = {}
    pending: list[str] = []
    for row in metric["rows"]:
        if row["code"] in kept:
            towns[row["code"]] = kept[row["code"]]
            continue
        if pending or (deadline is not None and time.monotonic() - started > deadline):
            pending.append(row["town"])
            continue
        co = cadastral[row["town"]]
        published = {z["code"]: {"sale": z["sale"], "rent": z["rent"]} for z in row["zones"]}
        try:
            points, stop = town_series(lambda s: read_town(session, s, co), lambda s: zone_codes(session, s, co), available, published, last)
        except omi.OmiError as error:
            if "non raggiungibile" not in str(error):
                raise
            pending.append(row["town"])
            continue
        towns[row["code"]] = {"town": row["town"], "semesters": [p["semester"] for p in points], "points": points, "stoppedAt": stop}
    if pending:
        return {"schemaVersion": 1, "metric": METRIC, "lastSemester": last, "retrieved": date.today().isoformat(), "towns": towns,
                "pending": pending, "qualityGate": {"status": "INCOMPLETE", "note": "Comuni da leggere: " + ", ".join(pending)}}
    common = sorted(set.intersection(*(set(t["semesters"]) for t in towns.values())))
    return {
        "schemaVersion": 1, "version": f"omi-residential-serie-{last}-v1", "retrieved": date.today().isoformat(),
        "metric": METRIC, "source": metric["meta"]["source"], "sourceUrl": omi.BASE + "ricerca.htm", "province": omi.PROVINCE,
        "lastSemester": last,
        "rule": ("Punto medio delle «Abitazioni civili» NORMALE per zona, media semplice delle zone; per ogni Comune solo i semestri "
                 "consecutivi con le stesse zone (e le stesse zone residenziali) del semestre pubblicato."),
        "commonSemesters": common, "towns": towns,
        "qualityGate": {"status": "PASS", "note": f"{last} identico ai valori di zona pubblicati per i 7 Comuni."},
    }


def label(semester: str) -> str:
    year, half = semester.split("-S")
    return f"{year} S{half}"


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    metric = metrics[METRIC]
    if omi.label_semester(metric["meta"]["year"]) != snapshot["lastSemester"]:
        raise OmiHistoryError("serie non allineata al semestre pubblicato")
    for row in metric["rows"]:
        town = snapshot["towns"][row["code"]]
        last = town["points"][-1]
        if not (math.isclose(last["saleMean"], row["saleMean"], rel_tol=0, abs_tol=1e-9)
                and math.isclose(last["rentMean"], row["rentMean"], rel_tol=0, abs_tol=1e-9)):
            raise OmiHistoryError(f"{row['town']}: media del semestre pubblicato diversa dal catalogo")
        years = [label(p["semester"]) for p in town["points"]]
        row["componentSeries"] = {"sale": {"years": years, "values": [p["saleMean"] for p in town["points"]]},
                                  "rent": {"years": years, "values": [p["rentMean"] for p in town["points"]]}}
        row["series"] = dict(row["componentSeries"]["sale"])
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    common = snapshot["commonSemesters"]
    longer = [t["town"] for t in snapshot["towns"].values() if len(t["semesters"]) > len(common)]
    note = (f"Media comunale per semestre con le stesse zone OMI del semestre pubblicato: per tutti e sette i Comuni dal "
            f"{omi.semester_label(common[0])}, quando l'Agenzia ha ridisegnato le zone di alcuni Comuni.")
    if longer:
        note += " Nelle schede di " + ", ".join(longer) + ", dove le zone non sono cambiate, la serie è più lunga."
    metric["method"]["historyNote"] = note
