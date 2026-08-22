#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.request

BASE = "https://esploradati.istat.it/SDMXWS/rest"
FLOWS = {
    "lavoro": "DF_DCSS_ISTR_LAV_PEN_2_TV_3",
    "istruzione": "DF_DCSS_ISTR_LAV_PEN_2_TV_1",
}
TOWN_CODES = {"046005","046013","046018","046024","046028","046030","046033"}


def fetch(url: str, accept: str = "application/vnd.sdmx.structure+json;version=1.0", timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia/1.0", "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def walk(obj, path=""):
    if isinstance(obj, dict):
        yield path, obj
        for k,v in obj.items():
            yield from walk(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            yield from walk(v, f"{path}/{i}")


def inspect(flow: str) -> None:
    print(f"\n######## {flow} ########")
    urls = [
        f"{BASE}/availableconstraint/{flow}/all/all?mode=available&format=jsonstructure",
        f"{BASE}/dataflow/IT1/{flow}/1.0?references=all&format=jsonstructure",
    ]
    for url in urls:
        try:
            raw = fetch(url)
        except Exception as exc:
            print("ERROR", url, type(exc).__name__, repr(exc))
            time.sleep(13)
            continue
        print("URL", url, "BYTES", len(raw))
        obj = json.loads(raw)
        text = raw.decode("utf-8", errors="replace")
        print("ROOT", list(obj.keys()))
        for needle in ["SEX", "SESSO", "AGE", "ETA", "ETÀ", "CITTAD", "OCCUP", "ISTRUZ", "ITTER107"]:
            if needle.lower() in text.lower():
                print("FOUND", needle)
        for code in sorted(TOWN_CODES):
            if code in text:
                print("FOUND_TOWN", code)
        shown = 0
        for path, node in walk(obj):
            s = json.dumps(node, ensure_ascii=False)
            if any(n in s.lower() for n in ["sesso","sex","eta","età","age","occup","istru","itter107","territorio"]):
                if len(s) <= 5000:
                    print("NODE", path, s[:1800])
                    shown += 1
                    if shown >= 60:
                        break
        time.sleep(13)


def main() -> None:
    for flow in FLOWS.values():
        inspect(flow)


if __name__ == "__main__":
    main()
