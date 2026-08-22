#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen

IPA_API = "https://indicepa.gov.it/ipa-dati/api/3/action/datastore_search"
IPA_RESOURCE = "7ecd6b8e-ede7-41c6-a16d-fe263ac6baf1"
PAD26 = "https://raw.githubusercontent.com/teamdigitale/padigitale2026-opendata/main/data/candidature_finanziate_141.csv"
TOWNS = {
    "Camaiore": "046005",
    "Forte dei Marmi": "046013",
    "Massarosa": "046018",
    "Pietrasanta": "046024",
    "Seravezza": "046028",
    "Stazzema": "046030",
    "Viareggio": "046033",
}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return value


def get_json(url: str, timeout: int = 60) -> dict:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 OsservatorioVersilia/1.0", "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def get_text(url: str, timeout: int = 60) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 OsservatorioVersilia/1.0", "Accept": "text/csv,*/*"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8-sig")


def ipa_rows(town: str) -> list[dict]:
    q = f"Comune di {town}"
    url = IPA_API + "?" + urlencode({"resource_id": IPA_RESOURCE, "limit": 500, "q": q})
    payload = get_json(url)
    records = payload["result"]["records"]
    exact_targets = {norm(f"Comune di {town}"), norm(f"Comune {town}")}
    exact = [r for r in records if norm(r.get("Denominazione_ente", "")) in exact_targets]
    if exact:
        return exact
    # fallback conservativo: nome comune + categoria comunale
    return [
        r for r in records
        if norm(town) in norm(r.get("Denominazione_ente", ""))
        and "comun" in norm(r.get("Nome_Categoria", ""))
    ]


def analyse_ipa() -> dict:
    out = {}
    for town in TOWNS:
        rows = ipa_rows(town)
        dates = sorted({r.get("Data_aggiornamento") for r in rows if r.get("Data_aggiornamento")})
        types = Counter(r.get("Tipologia_servizio") or "" for r in rows)
        urls = [r.get("Url_servizio") or "" for r in rows]
        duplicate_urls = {u: c for u, c in Counter(urls).items() if u and c > 1}
        out[town] = {
            "count": len(rows),
            "ipaCodes": sorted({r.get("Codice_IPA") for r in rows if r.get("Codice_IPA")}),
            "entityNames": sorted({r.get("Denominazione_ente") for r in rows if r.get("Denominazione_ente")}),
            "dates": dates,
            "latestDate": max(dates) if dates else None,
            "oldestDate": min(dates) if dates else None,
            "uniqueTypes": len(types),
            "typeCounts": dict(types.most_common()),
            "duplicateUrls": duplicate_urls,
            "rows": [
                {
                    "id": r.get("Id_servizio"),
                    "type": r.get("Tipologia_servizio"),
                    "description": r.get("Descrizione_servizio"),
                    "url": r.get("Url_servizio"),
                    "updated": r.get("Data_aggiornamento"),
                }
                for r in rows
            ],
        }
    return out


def analyse_pad26() -> dict:
    text = get_text(PAD26, timeout=90)
    rows = list(csv.DictReader(io.StringIO(text)))
    out = {}
    for town, code in TOWNS.items():
        matches = [
            r for r in rows
            if r.get("cod_comune") == code
            and norm(r.get("tipologia_ente", "")) == "comuni"
            and norm(r.get("misura", "")).startswith("1 4 1")
        ]
        out[town] = [
            {
                "codiceIpa": r.get("codice_ipa"),
                "ente": r.get("ente"),
                "avviso": r.get("avviso"),
                "importo": r.get("importo_finanziamento"),
                "stato": r.get("stato_candidatura"),
                "dataStato": r.get("data_stato_candidatura"),
                "cup": r.get("codice_cup"),
            }
            for r in matches
        ]
    return out


def main() -> None:
    result = {
        "ipaSource": IPA_API,
        "ipaResource": IPA_RESOURCE,
        "pad26Source": PAD26,
        "ipa": analyse_ipa(),
        "pad26": analyse_pad26(),
    }
    print("SERVIZI_DIGITALI_AUDIT_JSON_BEGIN")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("SERVIZI_DIGITALI_AUDIT_JSON_END")

    print("\nSUMMARY")
    for town in TOWNS:
        ipa = result["ipa"][town]
        p = result["pad26"][town]
        print(f"{town}: IPA={ipa['count']} servizi, tipi={ipa['uniqueTypes']}, date={ipa['oldestDate']}..{ipa['latestDate']}; PAD26 1.4.1 Comune={len(p)}")


if __name__ == "__main__":
    main()
