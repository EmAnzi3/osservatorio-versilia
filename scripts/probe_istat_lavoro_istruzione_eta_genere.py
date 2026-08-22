#!/usr/bin/env python3
from __future__ import annotations

import re
import time
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://esploradati.istat.it/SDMXWS/rest"
FLOWS = {
    "lavoro": "DF_DCSS_ISTR_LAV_PEN_2_TV_3",
    "istruzione": "DF_DCSS_ISTR_LAV_PEN_2_TV_1",
}


def fetch(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia/1.0", "Accept": "application/xml"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lname(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def first_ref(root: ET.Element, cls: str) -> dict | None:
    for el in root.iter():
        if lname(el.tag) == 'Ref' and el.attrib.get('class') == cls:
            return dict(el.attrib)
    return None


def inspect(flow: str) -> None:
    print(f"\n######## {flow} ########")
    flow_url = f"{BASE}/dataflow/IT1/{flow}/1.0?references=none"
    raw = fetch(flow_url)
    print("FLOW_BYTES", len(raw))
    root = ET.fromstring(raw)
    dsd_ref = first_ref(root, 'DataStructure')
    print("DSD_REF", dsd_ref)
    if not dsd_ref:
        print(raw.decode('utf-8', errors='replace')[:8000])
        return
    time.sleep(13)
    agency = dsd_ref.get('agencyID', 'IT1')
    dsd_id = dsd_ref['id']
    version = dsd_ref.get('version', '1.0')
    dsd_url = f"{BASE}/datastructure/{agency}/{dsd_id}/{version}?references=none"
    raw = fetch(dsd_url)
    print("DSD_BYTES", len(raw), "DSD", agency, dsd_id, version)
    droot = ET.fromstring(raw)
    dims = []
    for el in droot.iter():
        if lname(el.tag) in {'Dimension','TimeDimension','MeasureDimension'}:
            dim = {'id': el.attrib.get('id'), 'position': el.attrib.get('position')}
            for sub in el.iter():
                if lname(sub.tag) == 'Ref' and sub.attrib.get('class') == 'Codelist':
                    dim['codelist'] = sub.attrib.get('id')
                    dim['codelistAgency'] = sub.attrib.get('agencyID')
                    dim['codelistVersion'] = sub.attrib.get('version')
                    break
            dims.append(dim)
    print("DIMENSIONS", dims)
    text = raw.decode('utf-8', errors='replace')
    for needle in ['SEX','SESSO','AGE','ETA','CITTAD','OCCUP','ISTRUZ','ITTER107','TIME_PERIOD']:
        if needle.lower() in text.lower():
            print('FOUND_IN_DSD', needle)


def main() -> None:
    for flow in FLOWS.values():
        inspect(flow)
        time.sleep(13)


if __name__ == '__main__':
    main()
