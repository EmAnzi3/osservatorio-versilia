#!/usr/bin/env python3
"""Aggiornatori dalla fonte: rifanno i valori pubblicati da file ufficiali ricostruiti e segnalano le revisioni."""
from __future__ import annotations

import io
import json
import math
import tempfile
import zipfile
from pathlib import Path

import update_source_data as upd

ROOT = Path(__file__).resolve().parents[1]
HEADER = "id_indicatore,anno,codice_geografia,geografia,den,num,misura_grezza,misura_standardizzata,liminf,limsup,sesso,strato1,strato2"
CODES = {v: k for k, v in upd.ars_legacy.TOWNS.items()}


def zipped(name: str, text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, text)
    return buffer.getvalue()


def ars_export(entry: dict, tuscany: float, override: dict | None = None) -> bytes:
    lines = [HEADER]
    for geo, values in entry["values"].items():
        for period, value in zip(entry["periods"], values):
            value = (override or {}).get((geo, period), value)
            text = str(value).replace(".", ",")
            lines.append(f'{entry["indicatorId"]},{period},{CODES[geo]},{geo},1,1,"{text}","{text}",0,0,totale,,')
            lines.append(f'{entry["indicatorId"]},{period},{CODES[geo]},{geo},1,1,"9,9","9,9",0,0,maschi,,')
    lines.append(f'{entry["indicatorId"]},{entry["periods"][-1]},090,Toscana,1,1,"{tuscany}","{tuscany}",0,0,totale,,')
    return zipped("dati.csv", "\n".join(lines) + "\n")


def ars_cases(tmp: Path) -> None:
    entry = json.loads(upd.ARS_LEGACY.read_text(encoding="utf-8"))["indicators"]["hospitalizedAll"]
    site = json.loads(upd.SITE.read_text(encoding="utf-8"))["metrics"]["hospitalizedAll"]
    tuscany = site["meta"]["benchmark"]["tuscany"]
    same = tmp / "same.zip"
    same.write_bytes(ars_export(entry, tuscany))
    assert upd.update_ars_legacy("hospitalizedAll", same, dry_run=True).lines == [], "lo stesso export non deve cambiare nulla"
    last = entry["periods"][-1]
    revised = tmp / "revised.zip"
    bumped = round(entry["values"]["Massarosa"][-1] + 0.5, 4)
    other_tuscany = round(tuscany + 0.3, 2)
    revised.write_bytes(ars_export(entry, other_tuscany, {("Massarosa", last): bumped}))
    lines = upd.update_ars_legacy("hospitalizedAll", revised, dry_run=True).lines
    assert any("catalogo Massarosa" in line and str(round(bumped, 2)) in line for line in lines), lines
    assert any("catalogo Toscana" in line and str(other_tuscany) in line for line in lines), lines
    newer = dict(entry, periods=entry["periods"] + ["2022-2026"], values={g: v + [1.0] for g, v in entry["values"].items()})
    ahead = tmp / "ahead.zip"
    ahead.write_bytes(ars_export(newer, tuscany))
    try:
        upd.update_ars_legacy("hospitalizedAll", ahead, dry_run=True)
        raise AssertionError("un periodo nuovo ARS non va applicato come revisione")
    except upd.UpdateError:
        pass


def p2_file(year: int) -> bytes:
    """P2 di tutti i Comuni ricostruito dai conteggi pubblicati e dal bilancio già congelato."""
    site = json.loads(upd.SITE.read_text(encoding="utf-8"))["metrics"]
    lotto = json.loads((upd.SNAP / "istat-demography-lotto-a-2026-08.json").read_text(encoding="utf-8"))["p02"]["towns"]
    head = ["Codice comune", "Comune", "Popolazione al 1° gennaio - Totale", "Popolazione al 31 dicembre - Totale",
            "Immigrati da altro comune - Totale", "Emigrati per altro comune - Totale",
            "Immigrati dall'estero - Totale", "Emigrati per l'estero - Totale"]
    lines = [f"Bilancio demografico {year}", ";".join(head)]
    for row in site[upd.MOBILITY[0]]["rows"]:
        p02 = upd.probes_one(lotto[row["town"]], year)
        internal = [p["count"] for p in row["parts"]]
        foreign = [p["count"] for p in next(r for r in site[upd.MOBILITY[1]]["rows"] if r["code"] == row["code"])["parts"]]
        lines.append(";".join(map(str, [row["code"], row["town"], p02["populationJan1"], p02["populationDec31"], internal[0], internal[1], foreign[0], foreign[1]])))
    lines.append("048017;Firenze;360000;361000;9000;8000;7000;2000")
    lines.append("058091;Roma;2750000;2752000;30000;31000;20000;9000")
    return zipped(f"P2_{year}.csv", "\n".join(lines) + "\n")


def mobility_cases(tmp: Path) -> None:
    site = json.loads(upd.SITE.read_text(encoding="utf-8"))["metrics"]
    year = int(site[upd.MOBILITY[0]]["meta"]["year"])
    path = tmp / "p2.zip"
    path.write_bytes(p2_file(year))
    lines = upd.update_istat_mobility(year, path, dry_run=True).lines
    towns = [line for line in lines if "benchmark" not in line]
    bad = []
    for line in towns:
        label, change = line.split(": ", 1)
        old, new = (float(x) for x in change.split(" → "))
        if not math.isclose(old, new, rel_tol=0, abs_tol=1e-9):
            bad.append(line)
    assert not bad, f"i conteggi pubblicati devono ridare gli stessi tassi: {bad[:3]}"
    text = upd.composite_flow(upd.COMPOSITE.read_text(encoding="utf-8"), "Massarosa", year + 1, 500, 400)
    flows = json.loads(text)["raw"]["Massarosa"]["internalResidentialMobility"]
    assert flows[-1] == {"year": year + 1, "registeredIn": 500, "registeredOut": 400} and flows[-2]["year"] == year
    same = {"version": "x", "retrieved": "2026-11-07", "benchmarks": {"a": 1}}
    assert upd.keep_retrieved(same, dict(same, retrieved="2026-11-06"))["retrieved"] == "2026-11-06", "rigiro identico: data invariata"
    assert upd.keep_retrieved(dict(same, benchmarks={"a": 2}), dict(same, retrieved="2026-11-06"))["retrieved"] == "2026-11-07"
    assert upd.keep_retrieved(same, None)["retrieved"] == "2026-11-07"
    try:
        upd.composite_flow(text, "Massarosa", year + 3, 1, 1)
        raise AssertionError("anno non consecutivo accettato")
    except upd.UpdateError:
        pass


ASIA_HEAD = "DATAFLOW,FREQ,REF_AREA,DATA_TYPE,ECON_ACTIVITY_NACE_2007,PERS_EMPL_SIZE_CLASS,TIME_PERIOD,OBS_VALUE"


def asia_files(tmp: Path, extra_year: bool = False) -> int:
    """CSV SDMX ricostruiti dalle serie pubblicate (7 Comuni) più 7800 Comuni di riempimento."""
    site = json.loads(upd.SITE.read_text(encoding="utf-8"))["metrics"]
    years = site["localUnits"]["rows"][0]["series"]["years"]
    emp = {r["code"]: r["series"]["values"] for r in site["localEmployees"]["rows"]}
    micro = {r["code"]: r["value"] for r in site["microUnits"]["rows"]}
    year = years[-1] + (1 if extra_year else 0)
    lu_lines, emp_lines, micro_lines = [ASIA_HEAD], [ASIA_HEAD], [ASIA_HEAD]
    totals = {"ITE1": 0, "IT": 0}
    for row in site["localUnits"]["rows"]:
        values = row["series"]["values"] + ([row["series"]["values"][-1] + 10] if extra_year else [])
        e = emp[row["code"]] + ([emp[row["code"]][-1] + 5] if extra_year else [])
        for y, v, w in zip(range(years[0], year + 1), values, e):
            lu_lines.append(f"x,A,{row['code']},LU,0010,TOTAL,{y},{v}")
            emp_lines.append(f"x,A,{row['code']},LUEMPDAA,0010,TOTAL,{y},{w}")
        total = values[-1]
        micro_lines += [f"x,A,{row['code']},LU,0010,TOTAL,{year},{total}", f"x,A,{row['code']},LU,0010,W0_9,{year},{round(micro[row['code']] * total / 100)}"]
        totals["ITE1"] += total
    for i in range(7800):
        code = f"{900000 + i}"
        for y in range(years[0], year + 1):
            lu_lines.append(f"x,A,{code},LU,0010,TOTAL,{y},10")
            emp_lines.append(f"x,A,{code},LUEMPDAA,0010,TOTAL,{y},30")
    totals["IT"] = totals["ITE1"] + 7800 * 10
    for area, total in totals.items():
        micro_lines += [f"x,A,{area},LU,0010,TOTAL,{year},{total}", f"x,A,{area},LU,0010,W0_9,{year},{round(total * 0.94)}"]
    for name, lines in (("lu", lu_lines), ("emp", emp_lines), ("micro", micro_lines)):
        (tmp / f"{name}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return year


def asia_cases(tmp: Path) -> None:
    year = asia_files(tmp)
    lines = upd.update_istat_asia(year, tmp, dry_run=True).lines
    towns = [line for line in lines if "benchmark" not in line and "Versilia" not in line]
    bad = [line for line in towns if not math.isclose(*(float(x) for x in line.split(": ", 1)[1].split(" → ")), rel_tol=0, abs_tol=0.006)]
    assert not bad, f"le serie pubblicate devono ridare gli stessi valori: {bad[:3]}"
    year = asia_files(tmp, extra_year=True)
    lines = upd.update_istat_asia(year, tmp, dry_run=True).lines
    assert any(line.startswith("  localUnits Massarosa:") for line in lines), "anno nuovo: valori comunali aggiornati"
    (tmp / "lu.csv").write_text("\n".join(l for l in (tmp / "lu.csv").read_text().splitlines() if ",046030," not in l or f",{year}," not in l) + "\n")
    try:
        upd.update_istat_asia(year, tmp, dry_run=True)
        raise AssertionError("Comune senza l'anno nuovo accettato")
    except upd.UpdateError:
        pass


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ars_cases(Path(tmp))
        mobility_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        asia_cases(Path(tmp))
    print("Aggiornatori dalla fonte: ARS stesso export invariato, revisione e Toscana rilevate, periodo nuovo rifiutato; mobilità P2 ricostruita 7/7 identica, rigiro senza modifiche; ASIA-UL ricostruita 7/7 identica, anno nuovo accettato, Comune incompleto rifiutato PASS")


if __name__ == "__main__":
    main()
