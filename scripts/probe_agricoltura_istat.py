#!/usr/bin/env python3
"""Probe one-shot per chiudere l'acquisizione Istat del lotto agricoltura.

Non modifica dati canonici: stampa solo metadati e pochi record utili a fissare
query SDMX, codici delle dimensioni e formato di risposta.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

TOWNS = ["046005", "046013", "046018", "046024", "046028", "046030", "046033"]
FLOWS = [
    "DF_DCAT_CENSAGRIC2020_SURF_ALL",
    "DF_DCAT_CENSAGRIC2020_UA_CROPS_2",
    "DF_DCAT_CENSAGRIC2020_CROPS_ALL",
    "DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS",
]


def request(url: str, accept: str | None = None) -> tuple[int, str, bytes]:
    headers = {"User-Agent": "OsservatorioVersilia-agriculture-probe/1.0"}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, response.headers.get("Content-Type", ""), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()


def dbnomics_probe(flow: str) -> None:
    dimensions = urllib.parse.quote(json.dumps({"REF_AREA": TOWNS}, separators=(",", ":")))
    url = (
        f"https://api.db.nomics.world/v22/series/ISTAT/{flow}"
        f"?limit=60&offset=0&observations=1&facets=1&dimensions={dimensions}"
    )
    status, content_type, body = request(url)
    print(f"\n=== DBnomics {flow} ===\nstatus={status} type={content_type} bytes={len(body)}")
    if status != 200:
        print(body[:2000].decode("utf-8", errors="replace"))
        return
    payload = json.loads(body)
    print("top keys:", list(payload)[:20])
    dataset = payload.get("dataset", {})
    print("dataset keys:", list(dataset)[:30])
    print("dimensions_codes_order:", dataset.get("dimensions_codes_order"))
    print("dimensions_values_labels:", json.dumps(dataset.get("dimensions_values_labels", {}), ensure_ascii=False)[:5000])
    docs = payload.get("series", {}).get("docs") or payload.get("docs") or []
    print("series count returned:", len(docs))
    for doc in docs[:25]:
        print(json.dumps({
            "series_code": doc.get("series_code"),
            "series_name": doc.get("series_name"),
            "period": doc.get("period"),
            "value": doc.get("value"),
            "dimensions": doc.get("dimensions"),
        }, ensure_ascii=False))


def istat_probe() -> None:
    key = "A.046005.HO"
    bases = [
        f"https://esploradati.istat.it/SDMXWS/rest/data/DF_DCAT_CENSAGRIC2020_SURF_ALL/{key}/IT1?startPeriod=2020&endPeriod=2020",
        f"https://sdmx.istat.it/SDMXWS/rest/data/DF_DCAT_CENSAGRIC2020_SURF_ALL/{key}/IT1?startPeriod=2020&endPeriod=2020",
    ]
    accepts = [
        "application/vnd.sdmx.data+csv;version=1.0.0",
        "application/vnd.sdmx.data+csv;version=2.0.0",
        "application/vnd.sdmx.genericdata+xml;version=2.1",
        "application/xml",
        None,
    ]
    for url in bases:
        print(f"\n=== ISTAT endpoint {url.split('/SDMXWS/')[0]} ===")
        for accept in accepts:
            status, content_type, body = request(url, accept)
            print(f"accept={accept!r} status={status} type={content_type} bytes={len(body)}")
            print(body[:1200].decode("utf-8", errors="replace").replace("\n", " "))
            if status == 200:
                break


if __name__ == "__main__":
    istat_probe()
    for flow in FLOWS:
        dbnomics_probe(flow)
