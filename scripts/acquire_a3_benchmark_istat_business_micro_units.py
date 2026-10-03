#!/usr/bin/env python3
"""Acquire native ASIA-UL size-class counts, with public municipal reconciliation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOW = "183_1163_DF_DICA_ASIAULP_TERRIFDATA_7"
BASE = "https://esploradati.istat.it/SDMXWS/rest/data"
SOURCE = f"https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0900ENT,1.0/DICA_ASIA/DICA_ASIAULP/{FLOW}"
TOWNS = {"046018", "046033", "046005", "046024", "046028", "046013", "046030"}
AREAS = TOWNS | {"IT", "ITE1"}
CLASSES = {"W0_9", "TOTAL"}
TUSCANY_PREFIXES = {"045", "046", "047", "048", "049", "050", "051", "052", "053", "100"}
PANEL_URL = f"{BASE}/IT1,{FLOW},1.0/A..LU.0010.W0_9+TOTAL?startPeriod=2023&endPeriod=2023"


def source_url(area):
    return f"{BASE}/IT1,{FLOW},1.0/A.{area}.LU.0010.W0_9+TOTAL?startPeriod=2023&endPeriod=2023"


def parse_csv(text, area):
    reader = csv.DictReader(io.StringIO(text))
    required = {"DATAFLOW", "FREQ", "REF_AREA", "DATA_TYPE", "ECON_ACTIVITY_NACE_2007",
                "PERS_EMPL_SIZE_CLASS", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS"}
    if not required.issubset(reader.fieldnames or []):
        raise RuntimeError("ASIA-UL: unexpected native schema")
    values = {}
    for row in reader:
        expected = {"DATAFLOW": f"IT1:{FLOW}(1.0)", "FREQ": "A", "REF_AREA": area,
                    "DATA_TYPE": "LU", "ECON_ACTIVITY_NACE_2007": "0010", "TIME_PERIOD": "2023"}
        if any(row.get(k) != v for k, v in expected.items()):
            raise RuntimeError("ASIA-UL: source period, area or measure mismatch")
        size = row.get("PERS_EMPL_SIZE_CLASS")
        raw = row.get("OBS_VALUE", "")
        if size not in CLASSES or size in values or not re.fullmatch(r"\d+", raw):
            raise RuntimeError("ASIA-UL: duplicate, missing or invalid size-class count")
        if row.get("OBS_STATUS", "").strip():
            raise RuntimeError("ASIA-UL: flagged observation requires separate audit")
        values[size] = int(raw)
    if set(values) != CLASSES or not 0 <= values["W0_9"] <= values["TOTAL"] or values["TOTAL"] <= 0:
        raise RuntimeError("ASIA-UL: incomplete or inconsistent numerator/denominator")
    return values


def parse_panel(body):
    reader = csv.DictReader(io.StringIO(body.decode("utf-8-sig")))
    grouped = {}
    for row in reader:
        area = row.get("REF_AREA", "")
        size = row.get("PERS_EMPL_SIZE_CLASS")
        if size in grouped.setdefault(area, {}):
            raise RuntimeError("ASIA-UL: duplicate full-panel observation")
        grouped[area][size] = row
    records = []
    for area, rows in sorted(grouped.items()):
        text = io.StringIO(newline="")
        writer = csv.DictWriter(text, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows.values())
        values = parse_csv(text.getvalue(), area)
        if re.fullmatch(r"\d{6}", area):
            records.append([area, values["W0_9"], values["TOTAL"]])
    return records, len(grouped)


def validate_panel(snapshot):
    panel = snapshot.get("municipalPanel", [])
    if not isinstance(panel, list) or len(panel) != 7900:
        raise RuntimeError("ASIA-UL: incomplete national municipal panel")
    seen = set()
    for row in panel:
        if not isinstance(row, list) or len(row) != 3:
            raise RuntimeError("ASIA-UL: invalid municipal panel record")
        area, numerator, denominator = row
        if not isinstance(area, str) or not re.fullmatch(r"\d{6}", area) or area in seen:
            raise RuntimeError("ASIA-UL: duplicate/invalid municipal panel code")
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (numerator, denominator)) or not 0 <= numerator <= denominator or denominator <= 0:
            raise RuntimeError("ASIA-UL: invalid municipal panel components")
        seen.add(area)
    tuscany = [r for r in panel if r[0][:3] in TUSCANY_PREFIXES]
    if len(tuscany) != 273:
        raise RuntimeError("ASIA-UL: incomplete Tuscany panel")
    for rows, area in ((panel, "IT"), (tuscany, "ITE1")):
        native = snapshot["records"][area]
        if sum(r[1] for r in rows) != native["W0_9"] or sum(r[2] for r in rows) != native["TOTAL"]:
            raise RuntimeError("ASIA-UL: municipal sums disagree with native aggregates")
    for area, numerator, denominator in panel:
        if area in TOWNS and snapshot["records"][area] != {"W0_9": numerator, "TOTAL": denominator}:
            raise RuntimeError("ASIA-UL: panel and municipal query disagree")


def validate_snapshot(metric, snapshot, local_units):
    if metric["meta"].get("year") != "2023" or metric["meta"].get("unit") != "percent":
        raise RuntimeError("ASIA-UL: public period/unit mismatch")
    sources = snapshot.get("sources", {})
    records = snapshot.get("records", {})
    if set(sources) != AREAS or set(records) != AREAS:
        raise RuntimeError("ASIA-UL: incomplete source perimeter")
    validate_panel(snapshot)
    for area in AREAS:
        source = sources[area]
        text = source.get("csv", "")
        if source.get("url") != source_url(area) or hashlib.sha256(text.encode()).hexdigest() != source.get("sha256"):
            raise RuntimeError("ASIA-UL: source lineage mismatch")
        native = parse_csv(text, area)
        record = records[area]
        if any(isinstance(v, bool) or not isinstance(v, int) for v in record.values()) or record != native:
            raise RuntimeError("ASIA-UL: frozen component mismatch")
    rows = metric.get("rows", [])
    units = {r["code"]: r["value"] for r in local_units.get("rows", [])}
    if len(rows) != 7 or {r["code"] for r in rows} != TOWNS or set(units) != TOWNS:
        raise RuntimeError("ASIA-UL: public municipal perimeter mismatch")
    for row in rows:
        record = records[row["code"]]
        public = row.get("value")
        if isinstance(public, bool) or not isinstance(public, (int, float)) or not math.isfinite(public):
            raise RuntimeError("ASIA-UL: invalid public percentage")
        expected = record["W0_9"] / record["TOTAL"] * 100
        if units[row["code"]] != record["TOTAL"] or not math.isclose(expected, public, rel_tol=0, abs_tol=.005000001):
            raise RuntimeError("ASIA-UL: municipal numerator/denominator reconciliation mismatch")
    benchmark = snapshot["benchmarks"]["microUnits"]
    if benchmark.get("year") != "2023" or benchmark.get("unit") != "percent":
        raise RuntimeError("ASIA-UL: benchmark period/unit mismatch")
    prior = json.loads((ROOT / "data/source-snapshots/a3-istat-business-benchmark-2023.json").read_text())
    for scope, area in (("tuscany", "ITE1"), ("italy", "IT")):
        record = records[area]
        if record["TOTAL"] != prior["benchmarks"]["localUnits"][scope]:
            raise RuntimeError("ASIA-UL: aggregate denominator disagrees with certified LU")
        value = benchmark.get(scope)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not math.isclose(
                value, record["W0_9"] / record["TOTAL"] * 100, rel_tol=0, abs_tol=1e-9):
            raise RuntimeError("ASIA-UL: aggregate count-ratio mismatch")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--input-panel", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = {}
    records = {}
    for area in sorted(AREAS):
        if args.input_dir:
            body = (args.input_dir / f"ov-asia-{area}.csv").read_bytes()
        else:
            request = urllib.request.Request(source_url(area), headers={
                "Accept": "application/vnd.sdmx.data+csv;version=1.0.0",
                "User-Agent": "OsservatorioVersilia-A3-ASIAUL-size-classes/1.0"})
            with urllib.request.urlopen(request, timeout=300) as response:
                body = response.read()
        text = body.decode("utf-8-sig")
        sources[area] = {"url": source_url(area), "csv": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}
        records[area] = parse_csv(text, area)
    benchmark = {"year": "2023", "unit": "percent", "formula": "unità locali con 0–9 addetti / unità locali totali × 100"}
    for scope, area in (("tuscany", "ITE1"), ("italy", "IT")):
        benchmark[scope] = records[area]["W0_9"] / records[area]["TOTAL"] * 100
    snapshot = {"schemaVersion": 1, "publisher": "Istat — ASIA Unità Locali", "sourceProfileId": "istat-business-annual",
                "status": "ACQUIRED_CANDIDATE", "sourceUrl": SOURCE, "sources": sources, "records": records,
                "benchmarks": {"microUnits": benchmark}, "qualityGate": {"status": "PASS", "errors": [],
                "candidateMetrics": ["microUnits"], "publicSnapshotReconciliation": "7/7, native LU W0_9 and TOTAL 2023; public rounding at two decimals"},
                "scope": {"note": "Rapporto tra conteggi ufficiali ASIA-UL 2023 W0_9 e TOTAL; aggregati nativi Toscana e Italia, stessa attività economica 0010. Non media delle quote comunali."}}
    if args.input_panel:
        body = args.input_panel.read_bytes()
    else:
        request = urllib.request.Request(PANEL_URL, headers={"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"})
        with urllib.request.urlopen(request, timeout=300) as response:
            body = response.read()
    snapshot["municipalPanel"], geographies = parse_panel(body)
    snapshot["panelSource"] = {"url": PANEL_URL, "sha256": hashlib.sha256(body).hexdigest(),
                              "bytes": len(body), "nativeGeographies": geographies,
                              "municipalities": len(snapshot["municipalPanel"]), "tuscanyMunicipalities": 273}
    site = json.loads((ROOT / "data/site-data.json").read_text())
    validate_snapshot(site["metrics"]["microUnits"], snapshot, site["metrics"]["localUnits"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "ACQUIRED_CANDIDATE", "municipalReconciliation": "7/7", "benchmarks": benchmark}))


if __name__ == "__main__":
    main()
