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
    base = {r["town"]: [dict(code=z["code"], sale=z["sale"], rent=z["rent"]) for z in r["zones"]]
            for r in upd.load(upd.SITE)["metrics"]["omiResidential"]["rows"]}
    bumped = {t: [dict(z, sale=z["sale"] + 100, rent=round(z["rent"] + 0.5, 1)) for z in zs] for t, zs in base.items()}
    # Locazione del catalogo arrotondata al decimo, zona fonte senza abitazioni civili: replay ammesso.
    base["Camaiore"][0].update(rent=base["Camaiore"][0]["rent"] - 0.05, rentRounded=base["Camaiore"][0]["rent"])
    base["Viareggio"].append(dict(code="R3", residential=False))
    bumped["Viareggio"].append(dict(code="R3", residential=False))
    try:
        for sem in ("2025-S2", "2025-S1"):
            try:
                upd.update_omi_residential(sem, True, lambda p: base)
                raise AssertionError("semestre non successivo accettato")
            except upd.UpdateError:
                pass
        broken = copy.deepcopy(base); broken["Viareggio"][0]["sale"] += 1; broken["Seravezza"][0]["rent"] += 0.05
        try:
            upd.update_omi_residential("2026-S1", True, lambda p: broken if p == "2025-S2" else bumped)
            raise AssertionError("replay diverso accettato")
        except upd.UpdateError as error:
            assert "Viareggio" in str(error) and "Seravezza" in str(error) and "Camaiore" not in str(error)
        vz = broken["Viareggio"][0]["code"]; sz = broken["Seravezza"][0]["code"]
        for wrong in ([f"Viareggio {vz}"], [f"Viareggio {vz}", f"Seravezza {sz}", "Camaiore"]):
            try:
                upd.update_omi_residential("2026-S1", True, lambda p: broken if p == "2025-S2" else bumped, corrections=wrong)
                raise AssertionError("correzioni incomplete o superflue accettate")
            except upd.UpdateError:
                pass
        upd.update_omi_residential("2026-S1", True, lambda p: broken if p == "2025-S2" else bumped,
                                   corrections=[f"Viareggio {vz}", f"Seravezza {sz}"])
        # Zonizzazione di Stazzema corretta dalla fonte: zone ricostruite con etichette della fonte.
        rezoned = copy.deepcopy(base); rezoned["Stazzema"] = [dict(code="B1", sale=875.0, rent=3.35, sourceLabel="B1/Centrale/STAZZEMA"),
                                                             dict(code="E7", sale=925.0, rent=3.35, sourceLabel="E7/Suburbana/PONTE STAZZEMESE")]
        rebumped = copy.deepcopy(bumped); rebumped["Stazzema"] = [dict(z, sale=z["sale"] + 10) for z in rezoned["Stazzema"]]
        try:
            upd.update_omi_residential("2026-S1", True, lambda p: rezoned if p == "2025-S2" else rebumped)
            raise AssertionError("zonizzazione diversa accettata")
        except upd.UpdateError as error:
            assert "Stazzema" in str(error) and "fonte Stazzema E7" in str(error)
        upd.update_omi_residential("2026-S1", True, lambda p: rezoned if p == "2025-S2" else rebumped, corrections=["Stazzema"])
        before = upd.load(upd.SITE)["metrics"]["omiResidential"]
        changes = upd.update_omi_residential("2026-S1", False, lambda p: rezoned if p == "2025-S2" else rebumped, corrections=["Stazzema"])
        m = upd.load(upd.SITE)["metrics"]["omiResidential"]
        assert m["meta"]["year"] == "1° semestre 2026" and changes.lines
        staz = next(r for r in m["rows"] if r["town"] == "Stazzema")
        assert [(z["code"], z["label"], z["sale"]) for z in staz["zones"]] == [("B1", "Stazzema · centrale", 885.0), ("E7", "Ponte Stazzemese · suburbana", 935.0)]
        assert all(r["saleMean"] == next(b for b in before["rows"] if b["town"] == r["town"])["saleMean"] + 100 or r["town"] == "Stazzema"
                   for r in m["rows"])
        for r in m["rows"]:
            assert math.isclose(r["saleMean"], math.fsum(z["sale"] for z in r["zones"]) / len(r["zones"]), abs_tol=1e-12)
            assert r["value"] == r["saleMean"] == r["benchmarkValue"]
        snap = upd.load(tmp / f"data/source-snapshots/{omi.SNAPSHOT_PREFIX}2026-S1.json")
        assert snap["publishedReplayed"] == "2025-S2" and set(snap["zones"]) == set(omi.TOWNS.values())
        assert list(snap["catalogCorrections"]) == ["Stazzema"] and "--correction 'Stazzema'" in snap["acquisitionEvidence"]["script"]
        assert any(z["code"] == "R3" and not z["residential"] for z in snap["zones"]["046033"])
        assert all(z["code"] != "R3" for r in m["rows"] for z in r["zones"] if r["town"] == "Viareggio")
    finally:
        upd.SITE, upd.ROOT = real_site, real_root


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


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ars_cases(Path(tmp))
        mobility_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        asia_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        agcom_cases(Path(tmp))
    mef_probe_cases()
    with tempfile.TemporaryDirectory() as tmp:
        tourism_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        soil_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        aci_cases(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        omi_cases(Path(tmp))
    source_probe_cases(Path("."))
    print("Aggiornatori dalla fonte: ARS stesso export invariato, revisione e Toscana rilevate, periodo nuovo rifiutato; mobilità P2 ricostruita 7/7 identica, rigiro senza modifiche; ASIA-UL ricostruita 7/7 identica, anno nuovo accettato, Comune incompleto rifiutato; AGCOM FTTH ricostruita 7/7 identica, edizione nuova accettata, edizione vecchia e Comune mancante rifiutati; sonda MEF limitata agli atti DIMUNIC; capacità ricettiva pubblicata ricostruita identica, anno nuovo accettato con perimetro dichiarato, anno precedente rifiutato; consumo di suolo anno nuovo accettato con benchmark ufficiali, anno precedente rifiutato; parco ACI ricostruito 7/7 identico da un anno nuovo, anno pubblicato rifiutato; OMI al punto medio con semestre pubblicato rigiocato, replay diverso e semestre vecchio rifiutati; sonda generica dei fogli PASS")


if __name__ == "__main__":
    main()
