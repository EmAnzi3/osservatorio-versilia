#!/usr/bin/env python3
from urllib.request import Request, urlopen

urls = [
    "https://dati.istruzione.it/opendata/opendata/catalog/EDIANAGRAFESTA2021",
    "https://dati.istruzione.it/opendata/opendata/catalog/EDIANAGRAFESTA202120242520250806.csv",
]
needles = ("download", "202425", "20250806", "filename", "fileName", "onclick", "form", "catalog/download")
for url in urls:
    req = Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urlopen(req, timeout=60) as r:
        text = r.read().decode("iso-8859-1", errors="replace")
    print("\n===", url, "===")
    lines = text.splitlines()
    for i,line in enumerate(lines):
        low=line.lower()
        if any(n.lower() in low for n in needles):
            start=max(0,i-2); end=min(len(lines),i+3)
            print(f"--- lines {start+1}-{end} ---")
            for j in range(start,end):
                print(f"{j+1}: {lines[j][:3000]}")
