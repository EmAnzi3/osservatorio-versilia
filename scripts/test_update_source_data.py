#!/usr/bin/env python3
"""Aggiornatori dalla fonte: rifanno i valori pubblicati da file ufficiali ricostruiti e segnalano le revisioni."""
from __future__ import annotations

import io
import json
import math
import tempfile
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

import agcom_sources
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
    lu_lines, emp_lines = [ASIA_HEAD], [ASIA_HEAD]
    micro_counts: dict[str, dict[str, int]] = {}
    totals = {"ITE1": 0, "IT": 0}
    for row in site["localUnits"]["rows"]:
        values = row["series"]["values"] + ([row["series"]["values"][-1] + 10] if extra_year else [])
        e = emp[row["code"]] + ([emp[row["code"]][-1] + 5] if extra_year else [])
        for y, v, w in zip(range(years[0], year + 1), values, e):
            lu_lines.append(f"x,A,{row['code']},LU,0010,TOTAL,{y},{v}")
            emp_lines.append(f"x,A,{row['code']},LUEMPDAA,0010,TOTAL,{y},{w}")
        total = values[-1]
        micro_counts[row["code"]] = {"TOTAL": total, "W0_9": round(micro[row["code"]] * total / 100)}
        totals["ITE1"] += total
    for i in range(7800):
        code = f"{900000 + i}"
        for y in range(years[0], year + 1):
            lu_lines.append(f"x,A,{code},LU,0010,TOTAL,{y},10")
            emp_lines.append(f"x,A,{code},LUEMPDAA,0010,TOTAL,{y},30")
    totals["IT"] = totals["ITE1"] + 7800 * 10
    for area, total in totals.items():
        micro_counts[area] = {"TOTAL": total, "W0_9": round(total * 0.94)}
    head = "DATAFLOW,FREQ,REF_AREA,DATA_TYPE,ECON_ACTIVITY_NACE_2007,PERS_EMPL_SIZE_CLASS,TIME_PERIOD,OBS_VALUE,OBS_STATUS"
    flow = "IT1:183_1163_DF_DICA_ASIAULP_TERRIFDATA_7(1.0)"
    line = lambda area, size: f"{flow},A,{area},LU,0010,{size},{year},{micro_counts[area][size]},"
    micro_lines = [head] + [line(a, s) for a in micro_counts for s in ("TOTAL", "W0_9")]
    for area in micro_counts:
        (tmp / f"micro-{area}.csv").write_text("\n".join([head, line(area, "TOTAL"), line(area, "W0_9")]) + "\n", encoding="utf-8")
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


AGCOM_CSV = "https://geo.agcom.it/arcgis/sharing/rest/content/items/" + "a" * 32 + "/data"


def agcom_files(tmp: Path, period: str, revision: str = "14/07/2026", drop: str | None = None) -> None:
    """report.js con un'edizione datata e CSV comunale: i 7 Comuni dai record pubblicati, più 7889 Comuni di riempimento."""
    native = json.loads((ROOT / agcom_sources.NATIVE).read_text(encoding="utf-8"))
    (tmp / "report.js").write_text(f'<h2>Consistenze rilevate al {period} (rev. del {revision})</h2><p>Dati Comunali <a href="{AGCOM_CSV}" target="_blank"><u>CSV</u></a></p>')
    header = ["c0", "c1", "comune", "pro_com"] + [f"c{i}" for i in range(4, 19)]
    lines = [";".join(header)]

    def line(code: str, name: str, raw: dict) -> str:
        cells = [""] * 19
        cells[2], cells[3] = name, code
        cells[13], cells[14], cells[15], cells[16], cells[18] = (raw[k] for k in ("famiglie_residenti", "famiglie_ftth", "famiglie_ftth_20m", "copertura_ftth_desi_pct", "copertura_ftth_20m_pct"))
        return ";".join(cells)

    for town in native["towns"]:
        if town["code"] != drop:
            lines.append(line(town["code"], town["town"], town["agcom"]["primaryOfficialCsv"]["raw"]))
    filler = dict(famiglie_residenti="1000", famiglie_ftth="800", famiglie_ftth_20m="700", copertura_ftth_desi_pct="80,0%", copertura_ftth_20m_pct="70,0%")
    for i in range(7889):
        lines.append(line(f"046{500 + i}" if i < 270 else f"{200000 + i}", f"Filler {i}", filler))
    (tmp / "comuni.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def agcom_cases(tmp: Path) -> None:
    published = json.loads((ROOT / agcom_sources.NATIVE).read_text(encoding="utf-8"))["agcomAudit"]["dataPeriod"]
    agcom_files(tmp, published)
    lines = upd.update_agcom_ftth(tmp, dry_run=True).lines
    towns = [line for line in lines if "benchmark" not in line and "Versilia" not in line]
    assert not towns, f"il CSV pubblicato deve ridare gli stessi valori comunali: {towns[:3]}"
    totals = [line for line in lines if "Versilia" in line]
    bad = [line for line in totals if not math.isclose(*(float(x) for x in line.split(": ", 1)[1].split(" → ")), rel_tol=1e-12)]
    assert not bad, f"aggregati Versilia diversi: {bad}"
    newer = min(datetime.strptime(published, "%d/%m/%Y").date() + timedelta(days=1), date.today()).strftime("%d/%m/%Y")
    agcom_files(tmp, newer, newer)
    assert upd.update_agcom_ftth(tmp, dry_run=True).lines, "edizione nuova: benchmark aggiornati"
    agcom_files(tmp, "31/03/2026")
    try:
        upd.update_agcom_ftth(tmp, dry_run=True)
        raise AssertionError("edizione precedente alla pubblicata accettata")
    except upd.UpdateError:
        pass
    agcom_files(tmp, newer, drop="046030")
    try:
        upd.update_agcom_ftth(tmp, dry_run=True)
        raise AssertionError("CSV senza un Comune della Versilia accettato")
    except upd.UpdateError:
        pass


def tourism_zip(tmp: Path, years: dict[int, int]) -> Path:
    """Archivio Istat sintetico dal pannello pubblicato più recente; `years` = anno → posti letto extra aggiunti a ogni Comune."""
    import zipfile
    from openpyxl import Workbook
    import acquire_a3_benchmark_istat_tourism_annual as capacity

    snap = upd.load(capacity.ROOT / capacity.latest_snapshot())
    wb = Workbook(); ws = wb.active; ws.title = "Capacità ricettiva"
    head = [[None] * 56 for _ in range(6)]
    head[2][54] = "TOTALE"; head[4][32] = "totale alberghi"; head[4][52] = "totale extra-alberghieri"
    head[5][0] = "Anno/Year"; head[5][7] = "Cod. Istat"
    for i in (33, 53, 55):
        head[5][i] = "Beds"
    for row in head:
        ws.append(row)
    for year, extra in sorted(years.items(), reverse=True):
        def line(code, region, province, label, hotel, other, structures):
            row = [None] * 56
            row[0], row[2], row[4], row[5], row[7] = year, region, province, label, code
            row[33], row[53], row[55], row[54] = hotel, other, hotel + other, structures
            ws.append(row)
        for code, region, hotel, other, _total, structures in snap["records"]:
            line(code, region, None, None, hotel, other + extra, structures)
        for province, region, hotel, other, _total, structures in snap["provinceTotals"]:
            n = sum(1 for r in snap["records"] if r[0][:3] == province)
            line(None, region, province, "TOTALE", hotel, other + extra * n, structures)
        nat = snap["officialNational"]
        line(None, None, None, None, nat["hotelBeds"], nat["otherBeds"] + extra * len(snap["records"]), nat["structures"])
    xlsx = tmp / "c.xlsx"; wb.save(xlsx)
    archive = tmp / "capacity.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.write(xlsx, "Capacità comunale 2002-2025.xlsx")
    return archive


def tourism_cases(tmp: Path) -> None:
    """Capacità ricettiva: anno pubblicato ricostruito identico; anno nuovo accettato con perimetro dichiarato; anno precedente rifiutato."""
    import acquire_a3_benchmark_istat_tourism_annual as capacity

    pub = int(capacity.latest_snapshot()[-9:-5]); new = pub + 1
    real_site, real_root = upd.SITE, upd.ROOT
    (tmp / "data/source-snapshots").mkdir(parents=True)
    upd.SITE, upd.ROOT = tmp / "data/site-data.json", tmp
    upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        archive = tourism_zip(tmp, {new: 10, pub: 0, pub - 1: 0})
        changes = upd.update_istat_tourism(pub, archive, dry_run=True)
        assert changes.lines == [], changes.lines
        upd.update_istat_tourism(new, archive, dry_run=False)
        site = upd.load(upd.SITE)
        snap = upd.load(tmp / f"data/source-snapshots/a3-istat-tourism-capacity-benchmark-{new}.json")
        old = upd.load(real_root / capacity.latest_snapshot())
        beds = site["metrics"]["tourismBeds"]
        by_old = {r[0]: r for r in old["records"]}
        for row in beds["rows"]:
            assert row["value"] == by_old[row["code"]][4] + 10
        assert beds["meta"]["year"] == str(new) and beds["aggregate"]["value"] == sum(r["value"] for r in beds["rows"])
        assert beds["meta"]["benchmark"]["italy"] == old["officialNational"]["beds"] + 10 * len(old["records"])
        assert "non sono confrontabili" in snap["scope"]["note"] and "municipalBedsHistory" not in snap
        rate = site["metrics"]["tourismBedsPer1000"]
        assert rate["meta"]["sourceMeta"]["snapshot"].endswith(f"-{new}.json") and str(new) in rate["method"]["formula"]
        try:
            upd.update_istat_tourism(pub - 1, archive, dry_run=True)
            raise AssertionError("anno precedente al pubblicato accettato")
        except upd.UpdateError:
            pass
    finally:
        upd.SITE, upd.ROOT = real_site, real_root


def soil_workbook(tmp: Path, new: int, extra: float) -> Path:
    """Edizione ISPRA sintetica: anni pubblicati dallo snapshot corrente più l'anno `new` (+`extra` ha a ogni Comune)."""
    from openpyxl import Workbook
    import update_ispra_soil as soil

    snap = upd.load(soil.SNAPSHOT)
    wb = Workbook(); wb.remove(wb.active)
    head = ["pro_com", "nome_comune", "csuolo1", "csuolo2", "csuolo4", "csuolo8", "csuolo10"]
    for y in soil.stock_years(new):
        ws = wb.create_sheet(f"Comuni_{y}"); ws.append(head)
        ws.append([1001, "Agliè", 100, 900, 10, 0, 0])
        for town, code in soil.CODES.items():
            item = snap["landUse"]["municipalities"][town]
            area = item["municipalAreaHa"]
            r = item["rows"].get(str(y)) or item["rows"][str(new - 1)]
            c = snap["landUseChange"]["municipalities"][town]["rows"].get(str(y)) or {"netHa": 0, "grossHa": 0}
            ha = r["consumedHa"] + (extra if y == new else 0)
            ws.append([int(code), town, ha, area - ha, r["consumedPct"] if y != new else ha / area * 100,
                       extra if y == new else c["netHa"], extra if y == new else c["grossHa"]])
    ws = wb.create_sheet(f"Regioni_{new}"); ws.append(["cod_reg", "nome_regione", "csuolo1", "csuolo2", "csuolo4", "csuolo8"])
    for code in range(1, 21):
        ws.append([code, "Toscana" if code == 9 else f"R{code}", 1, 9, 6.5 if code == 9 else 5, 300 if code == 9 else 1])
    ws = wb.create_sheet(f"Nazionale_{new}"); ws.append(["cod_naz", "nome_nazione", "csuolo1", "csuolo2", "csuolo4", "csuolo8"])
    ws.append([0, "Italia", 1, 9, 7.25, 9000])
    path = tmp / "soil.xlsx"; wb.save(path)
    return path


def soil_cases(tmp: Path) -> None:
    """Consumo di suolo: anno nuovo accettato con serie, benchmark ufficiali e snapshot; anno già pubblicato rifiutato."""
    import update_ispra_soil as soil

    real_site, real_root, real_snap = upd.SITE, upd.ROOT, soil.SNAPSHOT
    pub = upd.load(real_snap)["landUse"]["years"][-1]; new = pub + 1
    (tmp / "data/source-snapshots").mkdir(parents=True)
    upd.SITE, upd.ROOT, soil.SNAPSHOT = tmp / "data/site-data.json", tmp, tmp / "data/source-snapshots/territorio.json"
    upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
    soil.SNAPSHOT.write_text(real_snap.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        book = soil_workbook(tmp, new, 1.0)
        try:
            upd.update_ispra_soil(pub - 1, book, dry_run=True)
            raise AssertionError("anno precedente al pubblicato accettato")
        except upd.UpdateError:
            pass
        upd.update_ispra_soil(new, book, dry_run=False)
        snap, site = upd.load(soil.SNAPSHOT), upd.load(upd.SITE)
        old = upd.load(real_snap)
        assert snap["landUse"]["years"] == soil.stock_years(new) and snap["landUseChange"]["years"] == soil.change_years(new)
        for town in soil.TOWNS:
            a, b = old["landUse"]["municipalities"][town], snap["landUse"]["municipalities"][town]
            assert math.isclose(b["rows"][str(new)]["consumedHa"], a["rows"][str(pub)]["consumedHa"] + 1, abs_tol=1e-6)
            assert snap["landUseChange"]["municipalities"][town]["rows"][str(new)]["netHa"] == 1.0
        for key in ("protectedNaturalAreas", "reticulum", "roadNetworkProfile"):
            assert snap[key] == old[key], key
        bench = upd.load(tmp / f"data/source-snapshots/a3-ispra-soil-benchmark-{new}.json")
        assert bench["benchmarks"]["landUse"]["tuscany"] == 6.5 and bench["benchmarks"]["landUseChange"]["italy"] == 9000
        change = site["metrics"]["landUseChange"]
        assert change["meta"]["year"] == str(new) and all(r["value"] == 1.0 for r in change["rows"])
        assert change["meta"]["benchmark"]["sourceSnapshot"].endswith(f"-{new}.json")
        assert all(r["series"]["years"][-1] == new for r in change["rows"] if r.get("series"))
    finally:
        upd.SITE, upd.ROOT, soil.SNAPSHOT = real_site, real_root, real_snap


def aci_cases(tmp: Path) -> None:
    """Parco ACI: il foglio dell'edizione pubblicata, rietichettato come anno nuovo, ridà 7/7 gli stessi valori; anno pubblicato rifiutato."""
    import base64
    import acquire_a3_benchmark_aci_istat_annual as aci

    real_site, real_root = upd.SITE, upd.ROOT
    old = upd.load(aci.ROOT / aci.latest_snapshot())
    pub = old["referenceYear"]; new = pub + 1
    (tmp / "data/source-snapshots").mkdir(parents=True)
    upd.SITE, upd.ROOT = tmp / "data/site-data.json", tmp
    upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
    archive = tmp / f"Autoritratto{new}_Parco_veicolare.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(f"Circolante_Copert_{new}.xlsx", base64.b64decode(old["source"]["workbookBase64"]))
    try:
        try:
            upd.update_aci_vehicles(pub, archive, dry_run=True)
            raise AssertionError("anno già pubblicato accettato")
        except upd.UpdateError:
            pass
        before = upd.load(upd.SITE)["metrics"]
        changes = upd.update_aci_vehicles(new, archive, dry_run=False)
        assert changes.lines == [], changes.lines
        site = upd.load(upd.SITE)["metrics"]
        snap = upd.load(tmp / f"data/source-snapshots/{aci.SNAPSHOT_PREFIX}{new}.json")
        assert snap["panelSha256"] == old["panelSha256"] and snap["benchmarks"]["motorization"]["italy"] == old["benchmarks"]["motorization"]["italy"]
        for key in ("motorization", "pollutingCars"):
            m = site[key]
            assert m["meta"]["year"] == str(new) and m["meta"]["benchmark"]["sourceSnapshot"].endswith(f"-{new}.json")
            assert math.isclose(m["aggregate"]["value"], before[key]["aggregate"]["value"], rel_tol=1e-12)
        assert str(new) in site["motorization"]["method"]["formula"] and "1° gennaio 2026" in site["motorization"]["method"]["formula"]
    finally:
        upd.SITE, upd.ROOT = real_site, real_root


def omi_cases(tmp: Path) -> None:
    """OMI: riga «Abitazioni civili NORMALE» al punto medio; semestre pubblicato rigiocato identico, altrimenti rifiuto."""
    import copy
    import update_omi as omi

    page = ("<p>Risultato interrogazione: Anno 2025 - Semestre 2 Provincia: LUCCA Comune: CAMAIORE Codice di zona: B2 "
            "Tipologia prevalente: Abitazioni civili Destinazione: Residenziale</p><table><tr><td>Abitazioni civili</td><td>NORMALE</td>"
            "<td>1550</td><td>2300</td><td>L</td><td>5,7</td><td>8</td><td>L</td></tr><tr><td>Box</td><td>NORMALE</td><td>700</td>"
            "<td>1050</td><td>L</td></tr></table>")
    z = omi.parse_result(page, "2025-S2")
    assert (z["sale"], z["rent"], z["rentRounded"], z["saleMin"], z["rentMax"]) == (1925.0, 6.85, 6.9, 1550.0, 8.0), z
    try:
        omi.parse_result(page.replace("Abitazioni civili</td>", "Ville</td>"), "2025-S2")
        raise AssertionError("zona senza abitazioni civili accettata")
    except omi.OmiError as error:
        assert "assente" in str(error)
    for bad in ("2026-S1",):
        try:
            omi.parse_result(page, bad)
            raise AssertionError("semestre diverso accettato")
        except omi.OmiError:
            pass
    assert omi.label_semester("2° semestre 2025") == "2025-S2" and omi.semester_label("2026-S1") == "1° semestre 2026"
    real_site, real_root = upd.SITE, upd.ROOT
    (tmp / "data/source-snapshots").mkdir(parents=True)
    upd.SITE, upd.ROOT = tmp / "data/site-data.json", tmp
    upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
    # Semestri relativi al catalogo corrente: il test resta valido a ogni aggiornamento.
    pub = omi.label_semester(upd.load(upd.SITE)["metrics"]["omiResidential"]["meta"]["year"])
    y, h = pub.split("-S")
    nxt = f"{y}-S2" if h == "1" else f"{int(y) + 1}-S1"
    prev = f"{y}-S1" if h == "2" else f"{int(y) - 1}-S2"
    base = {r["town"]: [dict(code=z["code"], sale=z["sale"], rent=z["rent"]) for z in r["zones"]]
            for r in upd.load(upd.SITE)["metrics"]["omiResidential"]["rows"]}
    bumped = {t: [dict(z, sale=z["sale"] + 100, rent=round(z["rent"] + 0.5, 1)) for z in zs] for t, zs in base.items()}
    # Locazione del catalogo arrotondata al decimo, zona fonte senza abitazioni civili: replay ammesso.
    base["Camaiore"][0].update(rent=base["Camaiore"][0]["rent"] - 0.05, rentRounded=base["Camaiore"][0]["rent"])
    base["Viareggio"].append(dict(code="R3", residential=False))
    bumped["Viareggio"].append(dict(code="R3", residential=False))
    try:
        for sem in (pub, prev):
            try:
                upd.update_omi_residential(sem, True, lambda p: base)
                raise AssertionError("semestre non successivo accettato")
            except upd.UpdateError:
                pass
        broken = copy.deepcopy(base); broken["Viareggio"][0]["sale"] += 1; broken["Seravezza"][0]["rent"] += 0.05
        try:
            upd.update_omi_residential(nxt, True, lambda p: broken if p == pub else bumped)
            raise AssertionError("replay diverso accettato")
        except upd.UpdateError as error:
            assert "Viareggio" in str(error) and "Seravezza" in str(error) and "Camaiore" not in str(error)
        vz = broken["Viareggio"][0]["code"]; sz = broken["Seravezza"][0]["code"]
        for wrong in ([f"Viareggio {vz}"], [f"Viareggio {vz}", f"Seravezza {sz}", "Camaiore"]):
            try:
                upd.update_omi_residential(nxt, True, lambda p: broken if p == pub else bumped, corrections=wrong)
                raise AssertionError("correzioni incomplete o superflue accettate")
            except upd.UpdateError:
                pass
        upd.update_omi_residential(nxt, True, lambda p: broken if p == pub else bumped,
                                   corrections=[f"Viareggio {vz}", f"Seravezza {sz}"])
        # Zonizzazione di Stazzema corretta dalla fonte: zone ricostruite con etichette della fonte.
        rezoned = copy.deepcopy(base); rezoned["Stazzema"] = [dict(code="B1", sale=875.0, rent=3.35, sourceLabel="B1/Centrale/STAZZEMA"),
                                                             dict(code="E7", sale=925.0, rent=3.35, sourceLabel="E7/Suburbana/PONTE STAZZEMESE")]
        rebumped = copy.deepcopy(bumped); rebumped["Stazzema"] = [dict(z, sale=z["sale"] + 10) for z in rezoned["Stazzema"]]
        try:
            upd.update_omi_residential(nxt, True, lambda p: rezoned if p == pub else rebumped)
            raise AssertionError("zonizzazione diversa accettata")
        except upd.UpdateError as error:
            assert "Stazzema" in str(error) and "fonte Stazzema E7" in str(error)
        upd.update_omi_residential(nxt, True, lambda p: rezoned if p == pub else rebumped, corrections=["Stazzema"])
        before = upd.load(upd.SITE)["metrics"]["omiResidential"]
        changes = upd.update_omi_residential(nxt, False, lambda p: rezoned if p == pub else rebumped, corrections=["Stazzema"])
        m = upd.load(upd.SITE)["metrics"]["omiResidential"]
        assert m["meta"]["year"] == omi.semester_label(nxt) and changes.lines
        staz = next(r for r in m["rows"] if r["town"] == "Stazzema")
        assert [(z["code"], z["label"], z["sale"]) for z in staz["zones"]] == [("B1", "Stazzema · centrale", 885.0), ("E7", "Ponte Stazzemese · suburbana", 935.0)]
        assert all(r["saleMean"] == next(b for b in before["rows"] if b["town"] == r["town"])["saleMean"] + 100 or r["town"] == "Stazzema"
                   for r in m["rows"])
        for r in m["rows"]:
            assert math.isclose(r["saleMean"], math.fsum(z["sale"] for z in r["zones"]) / len(r["zones"]), abs_tol=1e-12)
            assert r["value"] == r["saleMean"] == r["benchmarkValue"]
        snap = upd.load(tmp / f"data/source-snapshots/{omi.SNAPSHOT_PREFIX}{nxt}.json")
        assert snap["publishedReplayed"] == pub and set(snap["zones"]) == set(omi.TOWNS.values())
        assert list(snap["catalogCorrections"]) == ["Stazzema"] and "--correction 'Stazzema'" in snap["acquisitionEvidence"]["script"]
        assert any(z["code"] == "R3" and not z["residential"] for z in snap["zones"]["046033"])
        assert all(z["code"] != "R3" for r in m["rows"] for z in r["zones"] if r["town"] == "Viareggio")
    finally:
        upd.SITE, upd.ROOT = real_site, real_root


def bdi_branches_cases(tmp: Path) -> None:
    """Sportelli Banca d'Italia: serie 2018–2025 ricostruita, riconciliazione Istat 2022 obbligatoria, anno aperto rifiutato."""
    import bank_branches as bb

    real_site, real_root = upd.SITE, upd.ROOT
    (tmp / "data/source-snapshots").mkdir(parents=True, exist_ok=True)
    upd.SITE, upd.ROOT = tmp / "data/site-data.json", tmp
    upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
    bench = "data/source-snapshots/a3-istat-demography-benchmark-2026.json"
    (tmp / bench).write_text((real_root / bench).read_text(encoding="utf-8"), encoding="utf-8")
    cabs = {"046005": "24600", "046013": "70150", "046018": "70170", "046024": "70220", "046028": "70240", "046030": "70250", "046033": "24800"}
    head = "ID_INT;ID_SEDE;DATA_I_OPER;DATA_F_OPER;DATA_I_VAL;DATA_F_VAL;CAB_COM_ITA;DES_COM_ITA;STATO;TIPO_SEDE"

    def archive(istat: dict[str, int], italy_extra: int = 20500) -> bytes:
        lines = [head]
        for code, n in istat.items():
            for i in range(n + 1):  # una sede in più, chiusa a metà 2021: conta fino al 2020
                close = "9999-12-31" if i < n else "2021-06-30"
                lines.append(f"1;{code}{i};2000-01-01;{close};2000-01-01;9999-12-31;{cabs[code]};{bb.TOWNS[code]};86;001")
        lines.append(f"1;rapp;2000-01-01;9999-12-31;2000-01-01;9999-12-31;24800;VIAREGGIO;86;005")  # ufficio di rappresentanza
        lines.append(f"2;0460330;2000-01-01;9999-12-31;2000-01-01;9999-12-31;24800;VIAREGGIO;86;001")  # stesso ID_SEDE, altra banca
        lines += [f"9;x{i};2000-01-01;9999-12-31;2000-01-01;9999-12-31;13700;LUCCA;86;001" for i in range(italy_extra)]
        return zipped("2026-11-16_SUCCURSALI_BANCHE.csv", "\n".join(lines) + "\n")

    loc_head = "CAB_COMUNE;DEN_COMUNE;DEN_PROVINCIA;DEN_REGIONE;STATO;DATA_I_VAL;DATA_F_VAL"
    loc = [loc_head] + [f"{cabs[c]};{n};LUCCA;TOSCANA;86;1936-12-31;9999-12-31" for c, n in bb.TOWNS.items()]
    loc += [f"{13700 + i};T{i};X;TOSCANA;86;1936-12-31;9999-12-31" for i in range(270)]
    folder = tmp / "bdi"
    folder.mkdir(exist_ok=True)
    (folder / "localita.zip").write_bytes(zipped("LOCALITA.csv", "\n".join(loc) + "\n"))
    istat = dict(bb.ISTAT_2022)
    istat["046033"] -= 1  # la seconda banca con lo stesso ID_SEDE completa Viareggio: 24
    try:
        (folder / "succursali.zip").write_bytes(archive(istat))
        changes = upd.update_bdi_branches(2025, folder, dry_run=False)
        site = upd.load(upd.SITE)
        assert bb.METRIC not in site["metrics"], "l'indicatore entra in build, non nel catalogo canonico"
        snap = upd.load(tmp / f"{bb.SNAPSHOT_PREFIX}2025.json")
        assert snap["branches"]["046033"] == [25, 25, 25, 24, 24, 24, 24, 24] and snap["years"][0] == 2018, snap["branches"]["046033"]
        assert snap["qualityGate"]["istat2022"] == bb.ISTAT_2022 and snap["scopes"]["tuscany"] > 20000
        import materialize_bank_branches as mat
        real_mat_root = mat.ROOT
        try:
            mat.ROOT = tmp
            registry = upd.load(real_root / "data/source-registry.json")
            metric = mat.apply(site, registry)
        finally:
            mat.ROOT = real_mat_root
        via = next(r for r in metric["rows"] if r["code"] == "046033")
        pop = next(r for r in site["metrics"]["population"]["rows"] if r["code"] == "046033")["value"]
        assert abs(via["value"] - 24 / pop * 1000) < 1e-12 and via["series"]["years"][-1] == 2025
        theme = site["themes"]["economia"]
        assert theme["metrics"].count(bb.METRIC) == 1 and next(s for s in theme["sections"] if s["key"] == "credito")["metrics"] == [bb.METRIC]
        assert registry["metricOverrides"][bb.METRIC]["profile"] == mat.PROFILE and registry["expectedMetricCount"] == len(site["metrics"])
        assert any("Viareggio" in line for line in changes.lines)
        assert not upd.update_bdi_branches(2025, folder, dry_run=True).lines, "rigiro identico: nessuna differenza"
        for bad, year in ((dict(istat, **{"046030": 2}), 2025), (istat, 2026)):
            (folder / "succursali.zip").write_bytes(archive(bad))
            try:
                upd.update_bdi_branches(year, folder, dry_run=True)
            except upd.UpdateError:
                pass
            else:
                raise AssertionError(f"sportelli accettati: {year}")
    finally:
        upd.SITE, upd.ROOT = real_site, real_root


def opencivitas_needs_cases(tmp: Path) -> None:
    """Fabbisogni standard OpenCivitas: annualità 2023 riconciliata con la sonda, aggregati sui valutabili, valori diversi o annualità assente rifiutati."""
    import io as _io
    from openpyxl import Workbook
    import opencivitas_needs as oc
    import materialize_opencivitas_needs as mat

    real_site, real_root = upd.SITE, upd.ROOT
    (tmp / "data/source-snapshots").mkdir(parents=True, exist_ok=True)
    upd.SITE, upd.ROOT = tmp / "data/site-data.json", tmp
    upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
    folder = tmp / "oc"
    (folder / "pages").mkdir(parents=True, exist_ok=True)
    (folder / "pages/3.html").write_text(
        '<a href="/portale/documents/20118/0/2023_Ind_TOT_01_IT.csv/1086db31-bf42">t</a>'
        '<a href="/portale/documents/20118/0/2022_Ind_TOT_01_IT.csv/aa11">v</a>'
        '<a href="/portale/documents/20118/0/Metadati_Enti_2023_IT.xlsx/9af2749a">e</a>', encoding="utf-8")
    wb = Workbook(); ws = wb.active
    ws.append(["USERNAME", "TIPOLOGIA_ENTE", "ENTE", "REGIONE_DES", "COMUNE_ISTAT_COD"])
    for code, user in oc.TOWNS.items():
        ws.append([user, "COMUNE", f"C{code}", "TOSCANA", code])
    for i in range(260):
        ws.append([f"TS{i}", "COMUNE", f"T{i}", "TOSCANA", f"09{i:04d}"])
    for i in range(6300):
        ws.append([f"IT{i}", "COMUNE", f"I{i}", "VENETO", f"05{i:04d}"])
    buf = _io.BytesIO(); wb.save(buf)
    (folder / "enti.xlsx").write_bytes(buf.getvalue())

    def it(x: float) -> str:
        return repr(x).replace(".", ",")

    def csv_bytes(probe: dict) -> bytes:
        lines = ["USERNAME;Indicatore/Determinante;Valore;Anomalia;Privacy"]
        for code, user in oc.TOWNS.items():
            v = probe[code]
            pop = 10000
            for field, value in (("SPESA_STORICA", v["spesaStorica"]), ("FST_RIPROPORZIONATO_BI", v["spesaStandard"]),
                                 ("SPESA_STORICA_PROAB", v["spesaStorica"] / pop), ("FST_RIPROPORZIONATO_BI_PROAB", v["spesaStandard"] / pop),
                                 ("DIFF_OUT_PERC_TOT", v["serviceGapPct"]), ("POSIZIONE_SPESA_PERC_TOT", 5), ("POSIZIONE_OUTPUT_PERC_TOT", 5),
                                 ("FL_NO_VALUTABILE", 0)):
                lines.append(f"{user};{field};{it(value)};;")
        for prefix, n, spesa in (("TS", 260, 110.0), ("IT", 6300, 100.0)):
            for i in range(n):
                lines += [f"{prefix}{i};SPESA_STORICA;{it(spesa)};;", f"{prefix}{i};FST_RIPROPORZIONATO_BI;100;;",
                          f"{prefix}{i};DIFF_OUT_PERC_TOT;{'10' if prefix == 'TS' else '0'};;", f"{prefix}{i};FL_NO_VALUTABILE;{'1' if i == 0 else '0'};;"]
        return ("\n".join(lines) + "\n").encode("utf-8")

    try:
        (folder / "totale.csv").write_bytes(csv_bytes(oc.PROBE_2023))
        changes = upd.update_opencivitas_needs(None, folder, dry_run=False)
        site = upd.load(upd.SITE)
        assert not set(oc.METRICS) & set(site["metrics"]), "gli indicatori entrano in build, non nel catalogo canonico"
        snap = upd.load(tmp / f"{oc.SNAPSHOT_PREFIX}2023.json")
        assert snap["year"] == 2023 and snap["availableYears"] == [2022, 2023] and snap["towns"]["046018"]["population"] == 10000
        assert snap["scopes"]["tuscany"]["evaluable"] == 266, snap["scopes"]["tuscany"]
        real_mat_root = mat.ROOT
        try:
            mat.ROOT = tmp
            registry = upd.load(real_root / "data/source-registry.json")
            metrics = mat.apply(site, registry)
        finally:
            mat.ROOT = real_mat_root
        spend, serv = metrics[oc.SPENDING], metrics[oc.SERVICE]
        fdm = next(r for r in spend["rows"] if r["code"] == "046013")
        assert abs(fdm["value"] - (23349412.38 / 10590362.97 - 1) * 100) < 1e-9 and fdm["formatted"].startswith("+120,")
        mas = next(r for r in serv["rows"] if r["code"] == "046018")
        assert mas["value"] == -6.115557831 and mas["formatted"] == "−6,1%"
        towns = snap["towns"]
        exp = sum(t["serviceGapPct"] * t["spesaStandard"] for t in towns.values()) / sum(t["spesaStandard"] for t in towns.values())
        assert abs(serv["aggregate"]["value"] - exp) < 1e-9
        tus = snap["scopes"]["tuscany"]
        assert abs(spend["meta"]["benchmark"]["tuscany"] - spending_gap_check(tus)) < 1e-9
        theme = site["themes"]["bilanci"]
        assert next(s for s in theme["sections"] if s["key"] == "fabbisogni-standard")["metrics"] == list(oc.METRICS)
        assert all(registry["metricOverrides"][k]["profile"] == mat.PROFILE for k in oc.METRICS) and registry["expectedMetricCount"] == len(site["metrics"])
        assert any("Massarosa" in line for line in changes.lines)
        assert not upd.update_opencivitas_needs(2023, folder, dry_run=True).lines, "rigiro identico: nessuna differenza"
        bad = {k: dict(v) for k, v in oc.PROBE_2023.items()}
        bad["046030"]["serviceGapPct"] = 3.0
        for probe, year in ((bad, 2023), (oc.PROBE_2023, 2024)):
            (folder / "totale.csv").write_bytes(csv_bytes(probe))
            try:
                upd.update_opencivitas_needs(year, folder, dry_run=True)
            except upd.UpdateError:
                pass
            else:
                raise AssertionError(f"fabbisogni accettati: {year}")
    finally:
        upd.SITE, upd.ROOT = real_site, real_root


def spending_gap_check(scope: dict) -> float:
    return (scope["spesaStorica"] / scope["spesaStandard"] - 1) * 100


def aci_vehicles_history_cases() -> None:
    """Serie ACI: foglio «AV per comune», province riempite in avanti, arrotondamento come il pubblicato, ultimo anno vincolato."""
    import io as _io
    from openpyxl import Workbook
    import vehicles_history as vh

    def archive(year: int, shift: int = 0) -> bytes:
        # Dal 2024 il foglio è «4 AV per Comune» e ha la colonna REGIONE in testa.
        lead = ["TOSCANA"] if year >= 2024 else []
        wb = Workbook(); ws = wb.active; ws.title = "4 AV per Comune " if year >= 2024 else "AV per comune "
        ws.append([f"Autovetture distinte per comune. Anno {year}"])
        ws.append(["REGIONE"] * bool(lead) + ["PROVINCIA", "COMUNE", "EURO 0", "EURO 1", "EURO 2", "EURO 3", "EURO 4", "EURO 5", "EURO 6", "Non contemplato", "Non definito", "Totale "])
        ws.append(lead + ["LUCCA", "ALTOPASCIO", 1, 1, 1, 1, 1, 1, 1, None, None, 7])
        for i, name in enumerate(vh.TOWNS.values()):
            ws.append([None] * len(lead) + [None, name, 100 + i, 50, 50, 50 + shift, 300, 300, 1000 + year, None, 2, 1852 + i + year + shift])
        ws.append(lead + ["MASSA-CARRARA", "MASSAROSA", 9, 9, 9, 9, 9, 9, 9, None, None, 63])
        b = _io.BytesIO(); wb.save(b)
        z = _io.BytesIO()
        with zipfile.ZipFile(z, "w") as f:
            f.writestr(f"Parco/Circolante_Copert_{year}.xlsx", b.getvalue())
            f.writestr(f"Parco/Parco_veicolare_{year}.xlsx", b"x")
        return z.getvalue()

    archives = {vh.BASE + p: archive(y) for y, p in vh.ARCHIVES.items()}
    population = {c: {y: 20000 + 100 * i for y in range(2019, 2027)} for i, c in enumerate(vh.TOWNS)}
    from decimal import Decimal
    def expect(code: str, i: int, year: int):
        total = 1852 + i + year
        return (vh.round1(Decimal(total) / Decimal(population[code][year + 1]) * 1000), vh.round1(Decimal(100 + i + 150) / Decimal(total) * 100))
    current = {"motorization": {c: expect(c, i, 2025)[0] for i, c in enumerate(vh.TOWNS)},
               "pollutingCars": {c: expect(c, i, 2025)[1] for i, c in enumerate(vh.TOWNS)}}
    snap = vh.build_snapshot(archives.__getitem__, population, current)
    assert snap["years"] == [2018, 2019, 2020, 2022, 2023, 2024, 2025] and snap["missingYears"] == [2021]
    assert snap["series"]["motorization"]["046018"][0] == expect("046018", 2, 2018)[0]
    assert snap["towns"]["046018"]["2019"]["total"] == 1852 + 2 + 2019, "Massarosa di Massa-Carrara ignorata"
    assert snap["towns"]["046018"]["2024"]["total"] == 1852 + 2 + 2024, "foglio «4 AV per Comune» con REGIONE non letto"
    metrics = {k: {"rows": [{"town": n.title(), "code": c, "value": current[k][c]} for c, n in vh.TOWNS.items()], "meta": {}, "method": {"caveat": "X."}} for k in current}
    vh.apply(metrics, snap, vh.SNAPSHOT)
    assert metrics["pollutingCars"]["rows"][0]["series"]["years"][-1] == 2025 and "2021" in metrics["motorization"]["method"]["caveat"]
    bad = {k: dict(v) for k, v in current.items()}; bad["pollutingCars"]["046030"] += 0.1
    try:
        vh.build_snapshot(archives.__getitem__, population, bad)
    except vh.VehiclesError:
        pass
    else:
        raise AssertionError("ultimo anno diverso dal pubblicato accettato")


def asia_micro_units_history_cases() -> None:
    """Micro unità: SDMX ASIA-UL per i 7 Comuni, totali = unità locali pubblicate, ultima quota = pubblicata."""
    import micro_units_history as mu

    head = "DATAFLOW,FREQ,REF_AREA,DATA_TYPE,ECON_ACTIVITY_NACE_2007,PERS_EMPL_SIZE_CLASS,TIME_PERIOD,OBS_VALUE,OBS_STATUS"
    totals = {c: {y: 1000 + 10 * i + y - 2018 for y in range(2018, 2025)} for i, c in enumerate(mu.TOWNS)}
    def body(drop=False):
        lines = [head]
        for c in mu.TOWNS:
            for y in range(2018, 2025):
                if drop and c == "046030" and y == 2020:
                    continue
                lines.append(f"IT1:{mu.FLOW}(1.0),A,{c},LU,0010,TOTAL,{y},{totals[c][y]},")
                lines.append(f"IT1:{mu.FLOW}(1.0),A,{c},LU,0010,W0_9,{y},{totals[c][y] - 50},")
        return "\n".join(lines).encode()
    current = {c: round((totals[c][2024] - 50) / totals[c][2024] * 100, 2) for c in mu.TOWNS}
    urls = []
    snap = mu.build_snapshot(lambda u: urls.append(u) or body(), current, totals, 2024)
    assert "046005+046013" in urls[0] and "startPeriod=2018&endPeriod=2024" in urls[0]
    assert snap["years"] == list(range(2018, 2025)) and snap["series"]["046018"][0] == round(970 / 1020 * 100, 2)
    for wrong, fetch in (({**totals, "046033": {**totals["046033"], 2019: 1}}, lambda u: body()), (totals, lambda u: body(drop=True))):
        try:
            mu.build_snapshot(fetch, current, wrong, 2024)
        except mu.MicroUnitsError:
            pass
        else:
            raise AssertionError("totale diverso dalle unità locali pubblicate o anno mancante accettato")


def mim_students_history_cases() -> None:
    """Serie MIM: anagrafe di ciascun anno, statali e paritarie, primaria e secondaria; ultimo anno vincolato al pubblicato."""
    import school_history as sh

    def csv_(head, rows):
        return ("\n".join([";".join(head)] + [";".join(map(str, r)) for r in rows])).encode()

    def fetch(url: str) -> bytes:
        name = url.rsplit("/", 1)[1]
        start = int(__import__("re").search(r"(20\d\d)\d\d20", name).group(1))
        shift = start - 2015
        if name.startswith("SCUANAGRAFE"):
            private = "PAR" in name[:16]
            rows = [(f"{'P' if private else 'S'}{i}", "TOSCANA", "LUCCA", n) for i, n in enumerate(sh.TOWNS.values())]
            rows.append((f"{'P' if private else 'S'}X", "TOSCANA", "MASSA-CARRARA", "MASSAROSA"))
            if start == 2017:
                assert name.endswith("20170901.csv"), name
            return csv_(["CODICESCUOLA", "REGIONE", "PROVINCIA", "DESCRIZIONECOMUNE"], rows)
        private = "PAR" in name
        p = "P" if private else "S"
        if name.startswith("ALUCORSOINDCLA"):
            rows = [(f"{p}{i}", "SCUOLA PRIMARIA", 10 + i + shift, 10, 1) for i in range(7)]
            rows += [(f"{p}{i}", "SCUOLA SECONDARIA I GRADO", 5, 5, 1) for i in range(7)]
            rows += [(f"{p}{i}", "SCUOLA INFANZIA", 99, 99, 9) for i in range(7)] + [(f"{p}X", "SCUOLA PRIMARIA", 99, 99, 9)]
            return csv_(["CODICESCUOLA", "ORDINESCUOLA", "ALUNNIMASCHI", "ALUNNIFEMMINE", "CLASSI"], rows)
        rows = [(f"{p}{i}", "SCUOLA PRIMARIA", "TEMPO PIENO", 4 + i, 4) for i in range(7)]
        rows += [(f"{p}{i}", "SCUOLA PRIMARIA", "27 ORE", 6 + shift, 6) for i in range(7)]
        rows += [(f"{p}{i}", "SCUOLA SECONDARIA I GRADO", "TEMPO PIENO", 50, 50) for i in range(7)]
        return csv_(["CODICESCUOLA", "ORDINESCUOLA", "TEMPOSCUOLA", "ALUNNIMASCHI", "ALUNNIFEMMINE"], rows)

    def counts(i, start):
        shift = start - 2015
        students = 2 * ((10 + i + shift) + 10 + 10)
        return students, students / 4, 100 * (2 * (8 + i)) / (2 * (8 + i + 12 + shift))
    current = {k: {c: counts(i, 2024)[j] for i, c in enumerate(sh.TOWNS)} for j, k in enumerate(sh.KEYS)}
    snap = sh.build_snapshot(fetch, current, 2024)
    assert snap["schoolYears"][0] == "2015/16" and snap["schoolYears"][-1] == "2024/25" and len(snap["schoolYears"]) == 10
    assert snap["towns"]["046018"]["2018/19"]["students"] == counts(2, 2018)[0], "Massarosa di Massa-Carrara e infanzia escluse"
    assert snap["archives"]["2017/18"]["registry_state"]["url"].endswith("SCUANAGRAFESTAT20171820170901.csv")
    metrics = {k: {"rows": [{"town": n.title(), "code": c, "value": current[k][c]} for c, n in sh.TOWNS.items()], "meta": {}, "method": {"caveat": "X."}} for k in sh.KEYS}
    sh.apply(metrics, snap, sh.SNAPSHOT)
    assert metrics["primaryFullTimeShare"]["rows"][2]["series"]["years"][0] == "2015/16"
    bad = {k: dict(v) for k, v in current.items()}; bad["studentsPerClass"]["046030"] += 0.01
    try:
        sh.build_snapshot(fetch, bad, 2024)
    except sh.SchoolError:
        pass
    else:
        raise AssertionError("ultimo anno diverso dal pubblicato accettato")


def mef_taxpayers_history_cases() -> None:
    """Contribuenti ogni 100 maggiorenni: MEF anno A su POSAS 18+ al 1° gennaio A+2, anni continui, ultimo anno vincolato al pubblicato."""
    import io as _io
    import taxpayers_history as tx

    def zipped(name: str, text: str) -> bytes:
        b = _io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr(name, text)
        return b.getvalue()

    def mef(year: int) -> bytes:
        lines = ["Anno di imposta;Codice catastale;Codice Istat Comune;Denominazione Comune;Sigla Provincia;Numero contribuenti"]
        lines.append(f"{year};A000;046001;Altopascio;LU;9999")
        for i, (code, name) in enumerate(tx.TOWNS.items()):
            lines.append(f"{year};X{i};{code};{name};LU;{1000 * (i + 1) + year}")
        return zipped(f"Redditi_{year}.csv", "\n".join(lines))

    def posas(year: int) -> bytes:
        lines = [f"Popolazione residente al 1° gennaio {year}", "Codice comune;Comune;Età;Totale maschi;Totale femmine;Totale"]
        for i, (code, name) in enumerate(tx.TOWNS.items()):
            ages = {0: 100, 17: 50, 18: 60 + i, 50: 900 + year - 2000, 100: 5}
            for age, n in ages.items():
                lines.append(f"{code};{name};{age};{n // 2};{n - n // 2};{n}")
            lines.append(f"{code};{name};999;0;0;{sum(ages.values())}")
        return zipped(f"POSAS_{year}.csv", "\n".join(lines))

    def fetch(url: str) -> bytes:
        year = int(next(m for m in __import__("re").findall(r"(20\d\d)", url)))
        if "posas" in url:
            if year < 2020:
                raise tx.Unavailable(url)
            return posas(year)
        return mef(year)

    adults = lambda i, y: 60 + i + 900 + y - 2000 + 5
    current = {c: {"taxpayers": 1000 * (i + 1) + 2024, "adultPopulation2026": adults(i, 2026),
                   "value": (1000 * (i + 1) + 2024) / adults(i, 2026) * 100} for i, c in enumerate(tx.TOWNS)}
    snap = tx.build_snapshot(fetch, current, 2024)
    assert snap["years"] == list(range(2018, 2025)), "anni con POSAS a due anni disponibile"
    assert snap["towns"]["046018"]["2018"] == {"taxpayers": 3000 + 2018, "adults": adults(2, 2020)}
    assert snap["archives"]["2018"]["posas"]["date"] == "2020-01-01"
    metric = {tx.METRIC: {"rows": [{"town": n, "code": c, **current[c]} for c, n in tx.TOWNS.items()], "meta": {}, "method": {"caveat": "X."}}}
    tx.apply(metric, snap, tx.SNAPSHOT)
    assert metric[tx.METRIC]["rows"][2]["series"]["values"][0] == (3000 + 2018) / adults(2, 2020) * 100
    bad = {c: dict(v) for c, v in current.items()}; bad["046030"]["adultPopulation2026"] += 1
    for wrong in (bad, ):
        try:
            tx.build_snapshot(fetch, wrong, 2024)
        except tx.TaxpayersError:
            pass
        else:
            raise AssertionError("maggiorenni diversi dal pubblicato accettati")
    try:
        tx.build_snapshot(lambda u: (_ for _ in ()).throw(tx.Unavailable(u)), current, 2024)
    except tx.TaxpayersError:
        pass
    else:
        raise AssertionError("anno corrente assente accettato")


def istat_famiglie_cases(tmp: Path) -> None:
    """Componenti per famiglia: serie comunale, aggregati come componenti/famiglie, Toscana riscontrata sulla riga pubblicata."""
    import io as _io
    from openpyxl import Workbook
    import household_size_history as hh

    years = [2018, 2019, 2020, 2021, 2022, 2023]
    towns = {c: n for c, n in zip(hh.TOWNS, ("Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"))}
    provinces = [("09", f"Prov{i}") for i in range(10)] + [(f"{r:02d}", f"P{r}-{i}") for r in range(1, 21) if r != 9 for i in range(5)]
    fam = {p: [1000.0 + 10 * j + k for j in range(6)] for k, p in enumerate(provinces)}
    size = {p: [2.0 + 0.01 * (k % 7) - 0.005 * j for j in range(6)] for k, p in enumerate(provinces)}

    def book(tus_shift: float = 0.0) -> bytes:
        wb = Workbook(); wb.remove(wb.active)
        for title, kind in (("Tav. 1.1 Comuni", "f"), ("Tav. 4.1 Comuni", "s")):
            ws = wb.create_sheet(title); ws.append([title]); ws.append(["INDICE"]); ws.append([])
            ws.append(["Ripartizione", "Codice regione", "Denominazione regione", "Provincia", "Capoluogo", "Denominazione comune", "Codice comune Istat", *years])
            ws.append(["Nord-ovest", "01", "Piemonte", "Torino", "0", "Agliè", "001001", *([3.0] * 6)])
            for i, (c, n) in enumerate(towns.items()):
                vals = [5000.0 + 100 * i + j for j in range(6)] if kind == "f" else [2.4 - 0.01 * i - 0.02 * j for j in range(6)]
                ws.append(["Centro", "09", "Toscana", "Lucca", "0", n, c, *vals])
        for title, data in (("Tav. 1.2 Province e regioni", fam), ("Tav. 4.2 Province e regioni", size)):
            ws = wb.create_sheet(title); ws.append([title]); ws.append(["INDICE"]); ws.append([])
            ws.append(["Ripartizione", "Codice regione", "Denominazione regione", "Provincia", *years])
            for p in provinces:
                ws.append(["X", p[0], "R", p[1], *data[p]])
            tus = [p for p in provinces if p[0] == "09"]
            tot = [sum(fam[p][j] for p in tus) for j in range(6)]
            row = tot if data is fam else [sum(fam[p][j] * size[p][j] for p in tus) / tot[j] + tus_shift for j in range(6)]
            ws.append(["Centro", "09", "Toscana", "TOTALE", *row])
        b = _io.BytesIO(); wb.save(b); return b.getvalue()

    snap = hh.build_snapshot(book())
    assert snap["years"] == years and snap["provinceCount"] == len(provinces)
    assert snap["towns"]["046018"]["size"][-1] == 2.4 - 0.02 - 0.1
    v = snap["scopes"]["versilia"][-1]
    exp = sum((5000.0 + 100 * i + 5) * (2.4 - 0.01 * i - 0.1) for i in range(7)) / sum(5000.0 + 100 * i + 5 for i in range(7))
    assert abs(v["value"] - exp) < 1e-12
    it = snap["scopes"]["italy"][0]
    assert abs(it["value"] - sum(fam[p][0] * size[p][0] for p in provinces) / sum(fam[p][0] for p in provinces)) < 1e-12
    metric = {"rows": [{"town": n, "code": c, "value": 0} for c, n in towns.items()], "meta": {"year": "2023"}, "method": {}}
    hh.apply(metric, snap, "data/source-snapshots/istat-famiglie-serie-2023.json")
    assert metric["rows"][2]["series"]["years"] == years and metric["rows"][2]["formatted"] == "2,28" and metric["meta"]["benchmark"]["italy"] is not None
    try:
        hh.build_snapshot(book(tus_shift=0.01))
    except hh.HouseholdError:
        pass
    else:
        raise AssertionError("riga toscana pubblicata diversa dall'aggregato accettata")
    upd_file = tmp / "3-Famiglie.xlsx"; upd_file.write_bytes(book())
    real_root = upd.ROOT
    try:
        upd.ROOT = tmp; (tmp / "data/source-snapshots").mkdir(parents=True, exist_ok=True)
        changes = upd.update_istat_famiglie(upd_file, dry_run=False)
        assert (tmp / f"{hh.SNAPSHOT_PREFIX}2023.json").exists() and any("Massarosa" in l for l in changes.lines)
    finally:
        upd.ROOT = real_root


def openbdap_benchmarks_cases() -> None:
    """Confronto bilanci: aggregato sui Comuni che hanno trasmesso, soglia 90% dei residenti, riconciliazione 7/7 obbligatoria."""
    import io as _io
    import urllib.error
    import openbdap_benchmarks as ob

    towns = {"046005": "Camaiore", "046013": "Forte dei Marmi", "046018": "Massarosa", "046024": "Pietrasanta",
             "046028": "Seravezza", "046030": "Stazzema", "046033": "Viareggio"}
    tus = [f"0{p}{i:03d}" for p in (45, 47, 48, 49, 50) for i in range(1, 50)] + list(towns)          # 252 Comuni toscani
    other = [f"0{p:02d}{i:03d}" for p in range(1, 25) for i in range(1, 310)]
    pop = {c: 1000 + int(c[-3:]) for c in tus + other}
    p2 = ["Bilancio demografico", "Codice comune;Comune;Popolazione al 1° gennaio - Totale;Popolazione al 31 dicembre - Totale"]
    p2 += [f"{c};X;{pop[c]};{pop[c]}" for c in pop]
    zp = _io.BytesIO()
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("P2_2025_it_Comuni.csv", "\n".join(p2))

    def region_zip(codes: list[str], reg: str, skip: str | None = None, zone: str = "TOSCANA") -> bytes:
        hdr = "Codice Tipologia Soggetto;Codice Regione;Codice Provincia;Codice Comune"
        e, sp, m, r = ([hdr + ";Codice Titolo;Accertamenti;Riscossioni in C/Competenza"], [hdr + ";Codice Titolo;Impegni;Pagamenti in C/Competenza"],
                       [hdr + ";Codice Missione;Impegni"], [hdr + ";Cod Voce Ris Amm Rend;Totale di Gestione"])
        for c in codes:
            k = int(c[-3:]); pre = f"ELCOMU;{reg};{c[:3]};{c[3:]}"
            for t in ("01", "02", "03"):
                e.append(f"{pre};{t};{100 * k + int(t)};{80 * k}")
            for t in ("01", "02"):
                sp.append(f"{pre};{t};{90 * k + int(t)};{70 * k}")
            for mi in ("01", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14"):
                if not (c == skip and mi == "04"):
                    m.append(f"{pre};{mi};{k * int(mi)}")
            for v in ("0491", "0495", "0502"):
                r.append(f"{pre};{v};{k * 3}")
        b = _io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            for name, lines in ((ob.MEMBERS["entrate"], e), (ob.MEMBERS["spese"], sp), (ob.MEMBERS["missioni"], m), (ob.MEMBERS["risultato"], r)):
                z.writestr(f"Bilanci di {name}_{zone}.csv", "\n".join(lines))
            z.writestr("Rendiconto SDB Entrate Riepilogo Titoli.pdf", "doc")
        return b.getvalue()

    def fetcher_for(regions: dict[str, bytes]):
        def fetch(url: str) -> bytes:
            if "P2_2025" in url:
                return zp.getvalue()
            for name, raw in regions.items():
                if url == ob.archive_url(2025, name):
                    return raw
            raise urllib.error.HTTPError(url, 404, "nf", {}, None)
        return fetch

    # Toscana senza un Comune (non trasmesso) e Piemonte+Lombardia con tutto il resto d'Italia: copertura alta.
    regions = {"TOSCANA": region_zip([c for c in tus if c != "045001"], "09", skip="047002"), "PIEMONTE": region_zip(other, "01", zone="PIEMONTE")}
    tables = None
    published = {}
    for metric in ob.METRICS:
        published[metric] = {}
        for c in towns:
            k = int(c[-3:])
            n, d = {"currentRevenueAccruedPerResident": (300 * k + 6, None), "currentExpenditureCommittedPerResident": (90 * k + 1, None),
                    "capitalExpenditureCommittedPerResident": (90 * k + 2, None), "ownRevenueShare": (200 * k + 4, 300 * k + 6),
                    "currentCollectionCapacity": (240 * k, 300 * k + 6), "currentPaymentCapacity": (70 * k, 90 * k + 1)}.get(metric, (None, None))
            if metric in ob.RESULTS:
                n = 3 * k
            if metric in ob.MISSIONS:
                n = sum(k * int(mi) for mi in ob.MISSIONS[metric])
            published[metric][c] = n / d * 100 if d else n / pop[c]
    snap = ob.build_snapshot(2025, fetcher_for(regions), published, towns)
    b = snap["benchmarks"]
    t = b["currentRevenueAccruedPerResident"]["tuscany"]
    assert t["municipalities"] == len(tus) - 1 and t["value"] is not None and 0.9 <= t["populationShare"] < 1
    codes = [c for c in tus if c != "045001"]
    assert abs(t["value"] - sum(300 * int(c[-3:]) + 6 for c in codes) / sum(pop[c] for c in codes)) < 1e-9
    edu = b["educationMissionExpenditurePerResident"]["tuscany"]
    assert edu["municipalities"] == len(tus) - 1, "missione assente dal riepilogo: zero, Comune incluso"
    assert abs(edu["numerator"] - sum(4 * int(c[-3:]) for c in codes if c != "047002")) < 1e-9
    own = b["ownRevenueShare"]["italy"]
    assert own["value"] is not None and abs(own["value"] - own["numerator"] / own["denominator"] * 100) < 1e-12
    assert set(snap["missingRegions"]) == set(ob.REGIONS) - {"01", "09"} and snap["towns"]["046018"]["population"] == pop["046018"]
    # Senza il Piemonte l'Italia scende sotto il 90%: valore non pubblicato, copertura dichiarata.
    low = ob.build_snapshot(2025, fetcher_for({"TOSCANA": regions["TOSCANA"]}), published, towns)["benchmarks"]["fcdePerResident"]["italy"]
    assert low["value"] is None and "soglia" in low["reason"]
    # Un valore pubblico diverso esclude quell'indicatore dal confronto (motivo dichiarato); se sono molti, si ferma tutto.
    bad = {k: dict(v) for k, v in published.items()}
    bad["fcdePerResident"]["046030"] += 0.01
    one = ob.build_snapshot(2025, fetcher_for(regions), bad, towns)
    assert one["benchmarks"]["fcdePerResident"]["tuscany"]["value"] is None and "Stazzema" in one["blocked"]["fcdePerResident"][0]
    assert one["benchmarks"]["ownRevenueShare"]["tuscany"]["value"] is not None
    for key in list(bad)[:12]:
        bad[key]["046033"] += 1
    try:
        ob.build_snapshot(2025, fetcher_for(regions), bad, towns)
    except ob.BenchmarkError:
        pass
    else:
        raise AssertionError("riconciliazione 7/7 non applicata")


def source_probe_cases(tmp: Path) -> None:
    """Sonda generica: un foglio Excel riporta intestazioni e righe dei Comuni della Versilia."""
    import io as _io
    from openpyxl import Workbook
    import probe_source_files as probe

    wb = Workbook(); ws = wb.active
    for row in (["PRO_COM", "Nome"], [1001, "Agliè"], ["046018", "Massarosa"]):
        ws.append(row)
    buf = _io.BytesIO(); wb.save(buf)
    sheets = probe.workbook(buf.getvalue())["sheets"]
    assert sheets[0]["head"][2] == ["046018", "Massarosa"] and sheets[0]["rows"] == 3
    table = probe.csv_table("COD;Comune;Val\n001001;Agliè;1\n46033;VIAREGGIO;2\n".encode())
    assert table["separator"] == ";" and table["rows"] == 3 and table["hits"] == [[3, ["46033", "VIAREGGIO", "2"]]]
    assert probe.csv_table("U;V\nLU033X;1\nPE007Y;2\n".encode(), r"^LU0(05|13|18|24|28|30|33)")["hits"] == [[2, ["LU033X", "1"]]]


def sdmx_probe_cases() -> None:
    """Sonda SDMX: dimensioni in ordine con i nomi dei codici, righe dei Comuni della Versilia separate."""
    import probe_sdmx as probe

    xml = (b'<m:Structure xmlns:m="m" xmlns:s="s" xmlns:c="c"><s:Codelists><s:Codelist id="CL_AREA">'
           b'<s:Code id="046033"><c:Name xml:lang="it">Viareggio</c:Name></s:Code></s:Codelist></s:Codelists>'
           b'<s:DataStructures><s:DimensionList><s:Dimension id="REF_AREA" position="1"><s:LocalRepresentation>'
           b'<s:Enumeration><Ref id="CL_AREA" class="Codelist"/></s:Enumeration></s:LocalRepresentation></s:Dimension>'
           b'<s:TimeDimension id="TIME_PERIOD" position="2"/></s:DimensionList></s:DataStructures></m:Structure>')
    st = probe.structure(xml)
    assert [d["id"] for d in st["dimensions"]] == ["REF_AREA", "TIME_PERIOD"] and st["codelists"]["CL_AREA"]["046033"] == "Viareggio"
    raw = b"DATAFLOW,REF_AREA,TIME_PERIOD,OBS_VALUE\nX,001001,2024,3\nX,046033,2024,41\n"
    out = probe.summarise(raw, st["codelists"], st["dimensions"])
    assert out["rows"] == 2 and out["versilia"] == [{"DATAFLOW": "X", "REF_AREA": "046033", "TIME_PERIOD": "2024", "OBS_VALUE": "41"}]
    assert {"code": "046033", "rows": 1, "name": "Viareggio"} in out["distinct"]["REF_AREA"]
    listing = (b'<m:Structure xmlns:m="m" xmlns:s="s" xmlns:c="c"><s:Dataflows>'
               b'<s:Dataflow id="117_1035_DF_DCAT_SERVBANC_COM_1" agencyID="IT1" version="1.0"><c:Name xml:lang="it">Servizi bancari - comuni</c:Name></s:Dataflow>'
               b'<s:Dataflow id="22_289_DF_DCIS_POPRES1_1" agencyID="IT1" version="1.0"><c:Name xml:lang="it">Popolazione</c:Name></s:Dataflow>'
               b'</s:Dataflows></m:Structure>')
    assert [f["id"] for f in probe.flows(listing, "bancar")] == ["117_1035_DF_DCAT_SERVBANC_COM_1"]


def bdi_branches_probe_cases() -> None:
    """Sportelli Banca d'Italia: conta le sedi operative nella versione valida al giorno, per Comune e tipo."""
    import probe_bdi_branches as probe

    def r(sede, town, cab, i_op, f_op, i_val="1900-01-01", f_val="9999-12-31", kind="SUCCURSALE"):
        return {"ID_SEDE": sede, "DES_COM_ITA": town, "CAB_COM_ITA": cab, "STATO": "86", "DATA_I_OPER": i_op,
                "DATA_F_OPER": f_op, "DATA_I_VAL": i_val, "DATA_F_VAL": f_val, "DES_TIPO_SEDE": kind}
    table = [r("1", "VIAREGGIO", "24800", "2000-01-01", "9999-12-31", "2000-01-01", "2016-06-30"),
             r("1", "VIAREGGIO", "24800", "2000-01-01", "9999-12-31", "2016-07-01", "9999-12-31"),
             r("2", "VIAREGGIO", "24800", "2000-01-01", "2018-03-01"), r("3", "LUCCA", "13700", "2000-01-01", "9999-12-31")]
    out = probe.count(table, {"24800", "13700"})
    assert out["2017-12-31"]["VIAREGGIO"]["tutte"] == 2 and out["2018-12-31"]["VIAREGGIO"]["tutte"] == 1
    assert out["2018-12-31"]["tuscany"]["tutte"] == 2 and out["2018-12-31"]["italy"]["SUCCURSALE"] == 2


def mef_probe_cases() -> None:
    """Sonda MEF: solo atti comunali DIMUNIC, link con la riga della tabella, testo PDF separato."""
    import probe_mef_fiscal as probe

    page = ('<table><tr><td>46 27-06-2026 TARI</td><td><a href="download_lib.php?key=1&amp;nome=442024_DIMUNIC-16lu26f035d-at2.pdf">'
            'tariffe</a></td></tr><tr><td><a href="download_lib.php?key=2&amp;nome=403132_CIMUNIC-16lu26i622d.pdf">regolamento</a></td></tr></table>'
            '<a href="/export/legenda-note_IMU_TARI.pdf">legenda</a>')
    found = probe.links(page, probe.BASE + "nuova_at/risultato.htm")
    docs = [l for l in found if probe.is_doc(l)]
    assert len(found) == 3 and len(docs) == 1, found
    assert docs[0]["url"].endswith("key=1&nome=442024_DIMUNIC-16lu26f035d-at2.pdf") and docs[0]["row"].startswith("46 27-06-2026 TARI")
    ctx = probe.context("Aree fabbricabili 1,06% Altri fabbricati (fabbricati diversi) 1,14%", r"Altri\s+fabbricati", 0, 60)
    assert ctx and "1,14%" in ctx[0]


def erp_cases(tmp: Path) -> None:
    """Morosità ERP: esercizio nuovo dal prospetto (righe e percentuali riconciliate); esercizio non successivo, riga mancante e percentuale incoerente rifiutati."""
    real_site, real_root, real_text = upd.SITE, upd.ROOT, upd.erp_pdf_text
    (tmp / "data/source-snapshots").mkdir(parents=True)
    upd.SITE, upd.ROOT = tmp / "data/site-data.json", tmp
    upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
    path = upd.load(upd.SITE)["metrics"]["erpArrears"]["meta"]["sourceMeta"]["snapshot"]
    (tmp / path).write_text((real_root / path).read_text(encoding="utf-8"), encoding="utf-8")
    last = upd.load(tmp / path)["scope"]["years"][-1]
    year = last + 1
    rows = ("Camaiore 5.039.222,44 385.582,55 7,65%\nForte Dei Marmi 4.151.908,56 303.196,97 7,30%\nMassarosa 2.184.259,17 73.162,83 3,35%\n"
            "Pietrasanta 7.185.201,31 474.515,31 6,60%\nSeravezza 5.650.196,60\n235.104,29 4,16%\nStazzema 1.074.168,22 47.012,01 4,38%\n"
            "Viareggio 27.984.513,43 2.912.512,45 10,41%")
    text = f"Somme non ancora incassate ...\nCOMUNI EMESSO dal 1/4/2004 al 31/12/{year} MOROSITA’ %\n{rows}\nAltro testo 1.000,00"
    pdf = tmp / "bilancio.pdf"
    pdf.write_bytes(b"%PDF-fixture")
    try:
        upd.erp_pdf_text = lambda body: text
        changes = upd.update_erp_arrears(year, pdf, dry_run=False)
        assert any("Viareggio" in line and "10.41%" in line for line in changes.lines), changes.lines
        site = upd.load(upd.SITE)
        metric = site["metrics"]["erpArrears"]
        new_path = metric["meta"]["sourceMeta"]["snapshot"]
        snap = upd.load(tmp / new_path)
        assert new_path.endswith(f"-{year}.json") and snap["scope"]["years"][-1] == year and metric["meta"]["year"] == str(year)
        assert next(r for r in metric["rows"] if r["code"] == "046030")["value"] == 4.38 and metric["aggregate"]["value"] == 8.32
        assert snap["sourceDocuments"][-1]["sha256"] == upd.hashlib.sha256(b"%PDF-fixture").hexdigest()
        import materialize_erp_arrears_v125 as erp
        assert metric == erp.build_metric(snap)
        upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
        for bad_text, bad_year in ((text, year + 1), (text.replace("Stazzema 1.074.168,22 47.012,01 4,38%", ""), year),
                                   (text.replace("4,38%", "5,38%"), year), (text.replace(f"31/12/{year}", f"31/12/{last}"), year)):
            upd.erp_pdf_text = lambda body, t=bad_text: t
            try:
                upd.update_erp_arrears(bad_year, pdf, dry_run=True)
                raise AssertionError("prospetto ERP non valido accettato")
            except upd.UpdateError:
                pass
    finally:
        upd.SITE, upd.ROOT, upd.erp_pdf_text = real_site, real_root, real_text


def gaia_cases(tmp: Path) -> None:
    """Acqua GAIA: semestre pubblicato ricostruito identico; semestre nuovo accettato; periodo, parametro e semestre precedente rifiutati."""
    real_site, real_root = upd.SITE, upd.ROOT
    (tmp / "data/source-snapshots").mkdir(parents=True)
    upd.SITE, upd.ROOT = tmp / "data/site-data.json", tmp
    upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        metric = upd.load(upd.SITE)["metrics"]["drinkingWaterQuality"]
        defs = metric["parameterDefinitions"]
        published = metric["meta"]["year"]
        half, year = published.split("° semestre ")
        current = f"{year}-S{half}"
        following = f"{int(year) + 1}-S1" if half == "2" else f"{year}-S2"

        def pages(name: str, label: str, bump: bool = False, unit: str | None = None,
                  second: dict[str, str] | None = None, extra: bool = False) -> Path:
            folder = tmp / name
            folder.mkdir()
            second = second or {}
            buttons = []
            for row in metric["rows"]:
                for loc in row["localities"]:
                    code2 = second.get(loc["sampleCode"], loc["sampleCode2"])
                    buttons.append(f'<a class="btn btn_localita" data-codice_comune="{upd.GAIA_TOWN[loc["townCode"]]}" '
                                   f'data-codice_prelievo="{loc["sampleCode"]}" data-codice_prelievo1="{code2}" data-codice_area="1">x</a>')
                    cells = "".join(
                        f'<tr><td><span title="{d["description"]}">{d["name"]}</span></td><td>{unit if unit and i == 7 else d["unit"]}</td>'
                        f'<td>{("9.9" if bump and i == 7 else v)}</td><td>{d["reference"]}</td></tr>'
                        for i, (d, v) in enumerate(zip(defs, loc["values"])))
                    # id «campioni» sul contenitore, come nel selettore «#campioni tbody tr» dell'acquisizione storica,
                    # e una tabella estranea dopo che non va letta.
                    html = (f'<main><h4>{loc["title"]}</h4><h6>Periodo di riferimento: {label}</h6>'
                            f'<div id="campioni"><table><thead><tr><th>P</th><th>U</th><th>V</th><th>L</th></tr></thead><tbody>{cells}</tbody></table></div>'
                            f'<table><tr><td>a</td><td>b</td><td>c</td><td>d</td></tr></table></main>')
                    (folder / f"{loc['sampleCode']}_{code2}.html").write_text(html, encoding="utf-8")
            if extra:
                buttons.append('<a class="btn_localita" data-codice_comune="6" data-codice_prelievo="07Z99K99" data-codice_prelievo1="0" data-codice_area="1">x</a>')
            buttons.append('<a class="btn_localita" data-codice_comune="31" data-codice_prelievo="33A02K14" data-codice_prelievo1="0" data-codice_area="4">altro gestore</a>')
            (folder / "index.html").write_text("".join(buttons), encoding="utf-8")
            return folder

        same = upd.update_gaia_water(current, pages("same", published.replace("semestre", "Semestre")), dry_run=True)
        assert same.lines == [], same.lines
        new_label = upd.gaia_label(following).replace("semestre", "Semestre")
        changes = upd.update_gaia_water(following, pages("new", new_label, bump=True, second={"07A07K06": "07A07K99"}), dry_run=False)
        assert any("secondo codice" in line and "07A07K99" in line for line in changes.lines), changes.lines
        assert sum("Nitrato" in line for line in changes.lines) >= 1, changes.lines
        site = upd.load(upd.SITE)
        m2 = site["metrics"]["drinkingWaterQuality"]
        path = upd.GAIA_SNAPSHOT.format(period=following)
        assert m2["meta"]["year"] == upd.gaia_label(following) and m2["meta"]["sourceMeta"]["snapshot"] == m2["method"]["snapshot"] == path
        snap = upd.load(tmp / path)["drinkingWaterQuality"]
        assert [l for r in m2["rows"] for l in r["localities"]] == snap["localities"] and len(snap["localities"]) == 70
        assert all(l["period"] == new_label and l["values"][7] == "9.9" for l in snap["localities"])
        torcigliano = next(l for l in snap["localities"] if l["sampleCode"] == "07A07K06")
        assert torcigliano["sampleCode2"] == "07A07K99" and torcigliano["url"].endswith("/campioni/07A07K06/07A07K99")
        fluoride = next(d for d in defs if d["name"] == "Fluoruro")
        assert upd.gaia_unit_fix("102", fluoride) == "0.102" and upd.gaia_unit_fix("0.105", fluoride) is None
        assert upd.gaia_unit_fix("3.0", fluoride) is None and upd.gaia_unit_fix("5000", fluoride) is None  # superamento vero o incoerente: resta
        upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
        for bad in (lambda: upd.update_gaia_water(following, pages("stale", published.replace("semestre", "Semestre")), dry_run=True),
                    lambda: upd.update_gaia_water(following, pages("unit", new_label, unit="(g/L)"), dry_run=True),
                    lambda: upd.update_gaia_water(f"{int(year) - 1}-S1", pages("old", "1° Semestre " + str(int(year) - 1)), dry_run=True),
                    lambda: upd.gaia_label("2026-S3"),
                    lambda: upd.update_gaia_water(following, pages("extra", new_label, extra=True), dry_run=True),
                    lambda: upd.gaia_parse(b'<h4>-</h4><h6>Periodo di riferimento: 1\xc2\xb0 Semestre 2026</h6><b>Notice</b>',
                                           "1° semestre 2026", defs, "sessione")):
            try:
                bad()
                raise AssertionError("pagine GAIA non valide accettate")
            except upd.UpdateError:
                pass
    finally:
        upd.SITE, upd.ROOT = real_site, real_root


def mim_cases(tmp: Path) -> None:
    """Sedi scolastiche: a.s. pubblicato ricostruito identico; a.s. nuovo accettato; a.s. precedente, altro anno e Comune mancante rifiutati."""
    real_site, real_root = upd.SITE, upd.ROOT
    (tmp / "data/source-snapshots").mkdir(parents=True)
    upd.SITE, upd.ROOT = tmp / "data/site-data.json", tmp
    upd.SITE.write_text(real_site.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        site = upd.load(upd.SITE)
        metric = site["metrics"]["schoolSites"]
        pub = int(metric["meta"]["year"])
        head = "ANNOSCOLASTICO;AREAGEOGRAFICA;REGIONE;PROVINCIA;CODICESCUOLA;DESCRIZIONECOMUNE"

        def registry(year: int, delta: int = 0, drop: str | None = None, other_year: bool = False) -> Path:
            tag = f"{year}{(year + 1) % 100:02d}"
            lines = [head]
            for row in metric["rows"]:
                if row["town"] == drop:
                    continue
                n = row["value"] + (delta if row["town"] == "Viareggio" else 0)
                lines += [f"{tag};CENTRO;TOSCANA;LUCCA;LU{row['code']}{i:03d};{row['town'].upper()}" for i in range(n)]
                lines.append(f"{tag};CENTRO;TOSCANA;LUCCA;LU{row['code']}000;{row['town'].upper()}")  # duplicato
            lines += [f"{tag};CENTRO;TOSCANA;FIRENZE;FI{i:05d};FIRENZE" for i in range(5)]
            lines += [f"{tag};NORD;LOMBARDIA;MILANO;MI{i:05d};MILANO" for i in range(7)]
            if other_year:
                lines.append(f"{year - 1}{year % 100:02d};NORD;LOMBARDIA;MILANO;MIX;MILANO")
            path = tmp / f"SCUANAGRAFESTAT{tag}{year}0901.csv"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return path

        assert upd.update_mim_schools(pub, registry(pub), dry_run=True).lines == []
        import sys as _sys
        argv = _sys.argv
        _sys.argv = ["update_source_data.py", "mim-schools", "--year", str(pub), "--file", str(registry(pub)), "--dry-run"]
        try:
            assert upd.main() == 0
        finally:
            _sys.argv = argv
        changes = upd.update_mim_schools(pub + 1, registry(pub + 1, delta=-1), dry_run=False)
        assert any("Viareggio" in line for line in changes.lines), changes.lines
        site = upd.load(upd.SITE)
        metric2 = site["metrics"]["schoolSites"]
        vi = next(r for r in metric2["rows"] if r["town"] == "Viareggio")
        old = next(r for r in metric["rows"] if r["town"] == "Viareggio")
        assert vi["value"] == old["value"] - 1 and metric2["meta"]["year"] == str(pub + 1)
        assert metric2["aggregate"]["value"] == sum(r["value"] for r in metric2["rows"])
        snap = upd.load(tmp / f"data/source-snapshots/mim-school-sites-{pub + 1}.json")
        assert snap["tuscany"] == sum(snap["municipal"].values()) + 5 and snap["italy"] == snap["tuscany"] + 7
        for bad in (lambda: upd.update_mim_schools(pub, registry(pub), dry_run=True),
                    lambda: upd.update_mim_schools(pub + 1, registry(pub + 1, drop="Stazzema"), dry_run=True),
                    lambda: upd.update_mim_schools(pub + 1, registry(pub + 1, other_year=True), dry_run=True)):
            try:
                bad()
                raise AssertionError("anagrafe non valida accettata")
            except upd.UpdateError:
                pass
        assert upd.mim_registry_name(2026, b'x SCUANAGRAFESTAT20262720260901.csv SCUANAGRAFESTAT20252620250901.csv') == "SCUANAGRAFESTAT20262720260901.csv"
    finally:
        upd.SITE, upd.ROOT = real_site, real_root


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ars_cases(Path(tmp))
        mobility_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        asia_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        agcom_cases(Path(tmp))
    mef_probe_cases()
    sdmx_probe_cases()
    bdi_branches_probe_cases()
    with tempfile.TemporaryDirectory() as tmp:
        tourism_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        soil_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        aci_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        omi_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        mim_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        gaia_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        erp_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        bdi_branches_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        opencivitas_needs_cases(Path(tmp))
    aci_vehicles_history_cases()
    mef_taxpayers_history_cases()
    mim_students_history_cases()
    asia_micro_units_history_cases()
    with tempfile.TemporaryDirectory() as tmp:
        istat_famiglie_cases(Path(tmp))
    openbdap_benchmarks_cases()
    source_probe_cases(Path("."))
    print("Aggiornatori dalla fonte: ARS stesso export invariato, revisione e Toscana rilevate, periodo nuovo rifiutato; mobilità P2 ricostruita 7/7 identica, rigiro senza modifiche; ASIA-UL ricostruita 7/7 identica, anno nuovo accettato, Comune incompleto rifiutato; AGCOM FTTH ricostruita 7/7 identica, edizione nuova accettata, edizione vecchia e Comune mancante rifiutati; sonda MEF limitata agli atti DIMUNIC; capacità ricettiva pubblicata ricostruita identica, anno nuovo accettato con perimetro dichiarato, anno precedente rifiutato; consumo di suolo anno nuovo accettato con benchmark ufficiali, anno precedente rifiutato; parco ACI ricostruito 7/7 identico da un anno nuovo, anno pubblicato rifiutato; OMI al punto medio con semestre pubblicato rigiocato, replay diverso e semestre vecchio rifiutati; sonda generica dei fogli; morosità ERP esercizio nuovo riconciliato e prospetti incoerenti rifiutati; acqua GAIA 70 località ricostruite identiche, semestre nuovo accettato, periodo vecchio, parametro cambiato e semestre precedente rifiutati; sedi scolastiche MIM ricostruite 7/7 identiche, a.s. nuovo accettato, a.s. precedente, Comune mancante e altro anno rifiutati; sportelli Banca d'Italia: serie 2018–2025 ricostruita con chiave banca + sede, riconciliazione Istat 2022 obbligatoria, anno aperto rifiutato; fabbisogni standard OpenCivitas 2023 riconciliati con la sonda, aggregati sui Comuni valutabili, valori diversi e annualità assente rifiutati; serie dei componenti per famiglia con aggregati componenti/famiglie e riscontro toscano; serie ACI del parco autovetture con ultimo anno vincolato al pubblicato; serie dei contribuenti con POSAS a due anni e ultimo anno vincolato; serie MIM con anagrafe di ciascun anno e ultimo anno vincolato; serie ASIA-UL delle micro unità con totali vincolati alle unità locali PASS")


if __name__ == "__main__":
    main()
