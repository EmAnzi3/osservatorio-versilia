#!/usr/bin/env python3
from __future__ import annotations

import time
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://esploradati.istat.it/SDMXWS/rest"
FLOWS = {
    "lavoro": "DF_DCSS_ISTR_LAV_PEN_2_TV_3",
    "istruzione": "DF_DCSS_ISTR_LAV_PEN_2_TV_1",
}
RELEVANT = {"FREQ","REF_AREA","INDICATOR","GENDER","AGE_NOCLASS","CITIZENSHIP","EDU_ATTAIN","CUR_ACT_STAT","LOC_DEST","REAS_COMMUTING"}


def fetch(url: str, timeout: int = 150) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"OsservatorioVersilia/1.0","Accept":"application/xml"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lname(tag: str) -> str:
    return tag.rsplit('}',1)[-1]


def names(root: ET.Element) -> dict[tuple[str,str],str]:
    out = {}
    for cl in root.iter():
        if lname(cl.tag) != "Codelist":
            continue
        clid = cl.attrib.get("id","")
        for code in cl:
            if lname(code.tag) != "Code":
                continue
            cid = code.attrib.get("id","")
            label = ""
            for node in code:
                if lname(node.tag) == "Name" and (node.text or "").strip():
                    label = (node.text or "").strip()
                    if node.attrib.get("{http://www.w3.org/XML/1998/namespace}lang") in {"it","IT",None}:
                        break
            out[(clid,cid)] = label
    return out


def inspect(label: str, flow: str) -> None:
    url = f"{BASE}/dataflow/IT1/{flow}/1.0?references=all"
    raw = fetch(url)
    root = ET.fromstring(raw)
    print(f"\n######## {label.upper()} {flow} bytes={len(raw)} ########")
    clabels = names(root)
    dim_to_cl = {}
    for el in root.iter():
        if lname(el.tag) != "Dimension":
            continue
        dimid = el.attrib.get("id")
        if dimid not in RELEVANT:
            continue
        for sub in el.iter():
            if lname(sub.tag) == "Ref" and sub.attrib.get("class") == "Codelist":
                dim_to_cl[dimid] = sub.attrib.get("id")
                break
    print("DIM_TO_CL", dim_to_cl)
    # Stampa i valori effettivamente ammessi dal content constraint del dataflow.
    constraint_values: dict[str,set[str]] = {}
    for kv in root.iter():
        if lname(kv.tag) != "KeyValue":
            continue
        dimid = kv.attrib.get("id")
        if dimid not in RELEVANT:
            continue
        vals = constraint_values.setdefault(dimid,set())
        for child in kv:
            if lname(child.tag) == "Value" and child.text:
                vals.add(child.text.strip())
    for dimid in ["FREQ","INDICATOR","GENDER","AGE_NOCLASS","CITIZENSHIP","EDU_ATTAIN","CUR_ACT_STAT","LOC_DEST","REAS_COMMUTING"]:
        vals = sorted(constraint_values.get(dimid,set()))
        clid = dim_to_cl.get(dimid,"")
        rendered = [(v, clabels.get((clid,v),"")) for v in vals]
        print("CONSTRAINT", dimid, rendered)
    towns = constraint_values.get("REF_AREA",set())
    for code in ["046005","046013","046018","046024","046028","046030","046033"]:
        print("TOWN", code, "YES" if code in towns else "NO")


def main() -> None:
    for label, flow in FLOWS.items():
        try:
            inspect(label,flow)
        except Exception as exc:
            print("ERROR", label, type(exc).__name__, repr(exc))
        time.sleep(13)


if __name__ == "__main__":
    main()
