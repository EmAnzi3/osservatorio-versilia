#!/usr/bin/env python3
"""TARI e IMU standardizzate al 2026 dallo snapshot `costi-fiscalita-2026.json`.

Lo snapshot è trascritto dalle delibere e dai prospetti 2026 raccolti dalla
sonda MEF (`data/source-probes/mef-fiscal-2026.json`). Il valore corrente passa
al 2026; la serie tiene anche il 2025 dello snapshot validato precedente.
L'addizionale IRPEF resta al 2025 finché il MEF non pubblica le righe 2026.
Idempotente: rieseguito sullo stesso snapshot non cambia il catalogo.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
SNAP = ROOT / "data" / "source-snapshots" / "costi-fiscalita-2026.json"
PRIOR = ROOT / "data" / "source-snapshots" / "costi-fiscalita-validated-2026-08.json"
TARI, IMU = "tariStandardHousehold", "municipalImuStandard"
TARI_FORMULA = "100 m² × quota fissa + quota variabile per 3 componenti; TEFA 5%; + 7,60 € di componenti perequative ARERA 2026."
IMU_FORMULA = "100.000 € × aliquota IMU 2026 della categoria «Altri fabbricati»."


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rates_text(towns: dict) -> str:
    groups: dict[float, list[str]] = {}
    for town, rec in towns.items():
        groups.setdefault(rec["ratePercent"], []).append(town)
    return "; ".join(f"{str(rate).replace('.', ',')}%: {', '.join(names)}" for rate, names in sorted(groups.items()))


def apply(data: dict, snap: dict, prior: dict) -> dict:
    tari, imu = snap["tari"], snap["imu"]
    assert tari["year"] == imu["year"] == 2026 and len(tari["towns"]) == len(imu["towns"]) == 7

    m = data["metrics"][TARI]
    for row in m["rows"]:
        rec = tari["towns"][row["town"]]
        old = prior["tari"]["towns"][row["town"]]["annualCost"]
        row.update(value=rec["annualCost"], benchmarkValue=rec["annualCost"], tariffDetail=rec,
                   series={"years": [2025, 2026], "values": [old, rec["annualCost"]]})
    m["meta"].update(year="2026", description="Spesa annua TARI per una stessa utenza domestica teorica residente di 3 componenti e 100 m², senza agevolazioni personali. Include TEFA e componenti perequative 2026.")
    m["method"].update(type="Elaborazione Osservatorio su tariffe ufficiali 2026", formula=TARI_FORMULA,
                       caveat="Nessuna riduzione personale. Tariffe dalle delibere comunali TARI 2026 depositate nel Portale del federalismo fiscale; Stazzema usa l’importo ufficiale pubblicato per 3 componenti / 100 m² come base.")
    m["aggregate"]["value"] = math.fsum(r["value"] for r in m["rows"]) / 7

    m = data["metrics"][IMU]
    for row in m["rows"]:
        rec = imu["towns"][row["town"]]
        old = prior["imu"]["towns"][row["town"]]["annualTax"]
        row.update(value=rec["annualTax"], benchmarkValue=rec["annualTax"], ratePercent=rec["ratePercent"],
                   series={"years": ["2025", "2026"], "values": [old, rec["annualTax"]]})
    extended = [t for t, rec in imu["towns"].items() if rec["basis"] != "prospetto 2026"]
    rates = rates_text(imu["towns"])
    m["meta"].update(year="2026", description=f"Imposta annua teorica su una seconda abitazione A/2 con base imponibile IMU identica di 100.000 €, usando l’aliquota 2026 «Altri fabbricati». Aliquote applicate: {rates}.")
    m["method"].update(formula=IMU_FORMULA,
                       caveat=f"La base imponibile è standardizzata per isolare l’effetto dell’aliquota comunale. {rates}. "
                              f"{', '.join(extended)}: nessun prospetto 2026 pubblicato entro il 28 ottobre, quindi valgono le aliquote 2025 (art. 1, comma 767, legge 160/2019).")
    m["aggregate"]["value"] = math.fsum(r["value"] for r in m["rows"]) / 7
    return data


def main() -> None:
    data = apply(load(DATA), load(SNAP), load(PRIOR))
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TARI e IMU 2026 materializzate (7/7).")


if __name__ == "__main__":
    main()
