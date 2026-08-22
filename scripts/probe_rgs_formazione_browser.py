#!/usr/bin/env python3
from __future__ import annotations

import json
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

PAGE_URL = "https://contoannuale.rgs.mef.gov.it/web/sicosito/assenze-e-turnover/formazione-acc"
API = "https://contoannuale.rgs.mef.gov.it/o/sico-rest-APIs/sicoAPI"
YEARS = tuple(range(2019, 2025))
TOWNS = {
    "Camaiore": "1348",
    "Forte dei Marmi": "3135",
    "Massarosa": "4177",
    "Pietrasanta": "5461",
    "Seravezza": "7010",
    "Stazzema": "7266",
    "Viareggio": "7967",
}


def total_row(payload: dict) -> dict:
    for group in payload.get("ripartizione", []):
        if "TOTALE" in group and group["TOTALE"]:
            row = group["TOTALE"][0]
            return {
                "totalDays": int(row["totale"]),
                "menDays": int(row["uomini"]),
                "womenDays": int(row["donne"]),
                "meanMen": float(row["media_uomini"]),
                "meanWomen": float(row["media_donne"]),
                "meanTotalRgs": float(row["media_totale"]),
            }
    raise RuntimeError(f"TOTALE non trovato: {payload}")


def main() -> None:
    with sync_playwright() as pw:
        request = pw.request.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36",
            extra_http_headers={"Accept": "application/json,text/plain,*/*", "Referer": PAGE_URL},
        )

        def get_training(year: int, codes: str) -> dict:
            params = {
                "anno": str(year),
                "tipoIstituzioneFilters": "C",
                "istituzioneFilters": codes,
            }
            url = f"{API}/formazione?{urlencode(params)}"
            response = request.get(url, timeout=60000)
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}: {url}")
            payload = response.json()
            if str(payload.get("anno")) != str(year):
                raise RuntimeError(f"Anno inatteso per {url}: {payload.get('anno')}")
            return total_row(payload)

        out = {
            "source": PAGE_URL,
            "api": f"{API}/formazione",
            "years": list(YEARS),
            "towns": {},
            "versilia": {},
        }
        for town, code in TOWNS.items():
            out["towns"][town] = {
                "institutionCode": code,
                "series": {str(year): get_training(year, code) for year in YEARS},
            }
        combined_codes = ",".join(TOWNS.values())
        out["versilia"] = {
            "institutionCodes": list(TOWNS.values()),
            "series": {str(year): get_training(year, combined_codes) for year in YEARS},
        }

        # Il backend espone una "Media Totale" che è la media aritmetica delle
        # medie Uomini e Donne. La verifichiamo esplicitamente, senza attribuirle
        # un significato diverso da quello pubblicato da RGS.
        for scope in [*out["towns"].values(), out["versilia"]]:
            for year, row in scope["series"].items():
                expected = (row["meanMen"] + row["meanWomen"]) / 2
                if abs(row["meanTotalRgs"] - expected) > 1e-9:
                    raise RuntimeError(f"Media Totale RGS non riconciliata {year}: {row}")
                if row["menDays"] + row["womenDays"] != row["totalDays"]:
                    raise RuntimeError(f"Giornate per genere non riconciliate {year}: {row}")

        print("RGS_FORMATION_HISTORY_JSON_BEGIN")
        print(json.dumps(out, ensure_ascii=False, sort_keys=True))
        print("RGS_FORMATION_HISTORY_JSON_END")
        request.dispose()


if __name__ == "__main__":
    main()
