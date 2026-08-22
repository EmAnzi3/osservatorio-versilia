#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://esploradati.istat.it/SDMXWS/rest"
FLOWS = {
    "lavoro": "DF_DCSS_ISTR_LAV_PEN_2_TV_3",
    "istruzione": "DF_DCSS_ISTR_LAV_PEN_2_TV_1",
}
CODELISTS = ["CL_SEXISTAT1", "CL_ETA1", "CL_TITOLO_STUDIO", "CL_FORZE_LAV", "CL_TIPO_DATO_CENS_POP", "CL_CITTADINANZA"]


def request(url: str, accept: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia/1.0", "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lname(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def codelist(code: str) -> None:
    url = f"{BASE}/codelist/IT1/{code}/1.0?references=none"
    raw = request(url, "application/xml")
    root = ET.fromstring(raw)
    print(f"\nCODELIST {code} bytes={len(raw)}")
    shown = 0
    for el in root.iter():
        if lname(el.tag) != "Code":
            continue
        cid = el.attrib.get("id")
        name = ""
        for sub in el:
            if lname(sub.tag) == "Name":
                name = (sub.text or "").strip()
                break
        if code == "CL_ETA1":
            # Tutte le età/classi sono utili, ma limitiamo la diagnostica a un output gestibile.
            if cid and (cid.isdigit() or any(x in name.lower() for x in ["totale", "anni", "oltre"])):
                print("CODE", cid, "=", name)
                shown += 1
        else:
            print("CODE", cid, "=", name)
            shown += 1
        if shown >= (130 if code == "CL_ETA1" else 100):
            break


def sample(flow_name: str, flow: str) -> None:
    key = ".".join(["A", "046018"] + [""] * 8)
    params = urllib.parse.urlencode({"startPeriod": "2024", "endPeriod": "2024", "format": "csvfile"})
    url = f"{BASE}/data/IT1,{flow},1.0/{key}/all?{params}"
    raw = request(url, "application/vnd.sdmx.data+csv;version=1.0.0", timeout=180)
    text = raw.decode("utf-8-sig", errors="replace")
    print(f"\nSAMPLE {flow_name} bytes={len(raw)} url={url}")
    lines = text.splitlines()
    for line in lines[:18]:
        print("ROW", line[:2400])
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    print("HEADER", reader.fieldnames)
    print("ROWS", len(rows))
    for col in ["FREQ","REF_AREA","INDICATOR","GENDER","AGE_NOCLASS","CITIZENSHIP","EDU_ATTAIN","CUR_ACT_STAT","LOC_DEST","REAS_COMMUTING","TIME_PERIOD"]:
        vals = sorted({str(r.get(col, "")) for r in rows})
        print("VALUES", col, len(vals), vals[:160])


def main() -> None:
    # Le codelist sono condivise dai due dataflow: una sola lettura ciascuna.
    for code in CODELISTS:
        try:
            codelist(code)
        except Exception as exc:
            print("CODELIST_ERROR", code, type(exc).__name__, repr(exc))
        time.sleep(13)
    for name, flow in FLOWS.items():
        try:
            sample(name, flow)
        except Exception as exc:
            print("SAMPLE_ERROR", name, type(exc).__name__, repr(exc))
        time.sleep(13)


if __name__ == "__main__":
    main()
