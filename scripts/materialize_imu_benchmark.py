#!/usr/bin/env python3
"""Aggiunge in build il confronto Toscana per l'IMU su una seconda casa vuota.

Legge `data/source-snapshots/mef-imu-benchmark-toscana-AAAA.json` (scritto da `update_source_data.py
mef-imu-benchmark`): aliquota per Comune dai prospetti MEF con la stessa regola dell'indicatore e media degli
importi su 100.000 € pesata per i residenti. Si applica solo se l'anno coincide, le sette aliquote lette in CI sono
identiche a quelle pubblicate e i Comuni letti coprono almeno il 90% dei residenti. L'Italia
(`mef-imu-benchmark-italia-AAAA.json`, unione dei quattro gruppi di regioni) si aggiunge con le stesse condizioni; senza
snapshot nazionale valido resta vuota.
"""
from __future__ import annotations

import json
from pathlib import Path

import imu_benchmarks as imb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
SOURCE = "Dipartimento delle Finanze — prospetti delle aliquote IMU · Istat (POSAS)"


def count(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def valid(snap: dict, year: int, rows: list) -> bool:
    b = snap["benchmark"]
    if snap["qualityGate"]["status"] != "PASS" or snap["year"] != year or b["value"] is None or b["populationShare"] < imb.MIN_SHARE:
        return False
    for row in rows:
        read = snap["versilia"][row["code"]]
        if read["status"] != "ok" or read["ratePercent"] != row["ratePercent"]:
            raise RuntimeError(f"Confronto IMU {snap['scope']}: {row['town']} letto {read.get('ratePercent')} ≠ pubblicato {row['ratePercent']}")
    return True


def coverage(b: dict) -> str:
    share = f"{b['populationShare'] * 100:.1f}".replace(".", ",")
    return f"letti {count(b['municipalities'])} Comuni su {count(b['municipalitiesTotal'])} ({share}% dei residenti)"


def apply(data: dict) -> bool:
    metric = data["metrics"].get(imb.METRIC)
    if not metric:
        return False
    year = int(metric["meta"]["year"])
    path = ROOT / imb.SNAPSHOT.format(scope="toscana", year=year)
    if not path.exists():
        return False
    snap = json.loads(path.read_text(encoding="utf-8"))
    if not valid(snap, year, metric["rows"]):
        return False
    b = snap["benchmark"]
    italy_path = ROOT / imb.SNAPSHOT.format(scope="italia", year=year)
    italy = json.loads(italy_path.read_text(encoding="utf-8")) if italy_path.exists() else None
    if italy is not None and not valid(italy, year, metric["rows"]):
        italy = None
    italy_note = (f"Italia: stessa regola, {coverage(italy['benchmark'])}; {imb.NOT_IMU_NOTE}. " if italy else "Italia in preparazione. ")
    metric["meta"]["benchmark"] = {
        "year": str(year), "tuscany": b["value"], "italy": italy["benchmark"]["value"] if italy else None, "source": SOURCE,
        "url": "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_imu/",
        "sourceSnapshot": imb.SNAPSHOT.format(scope="toscana", year=year),
        **({"italySourceSnapshot": imb.SNAPSHOT.format(scope="italia", year=year)} if italy else {}),
        "note": (f"Toscana: media degli importi comunali su 100.000 € pesata per i residenti al 1° gennaio {year}, con la stessa "
                 f"regola dei sette Comuni. {coverage(b)[0].upper() + coverage(b)[1:]}; esclusi i prospetti ambigui. {italy_note}"
                 "La media Versilia resta la media semplice dei sette Comuni."),
    }
    return True


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    done = apply(data)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Confronto IMU: " + ("applicato" if done else "snapshot assente o non valido, nessun confronto"))


if __name__ == "__main__":
    main()
