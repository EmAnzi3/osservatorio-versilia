#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import re
import unicodedata
from urllib.request import Request, urlopen

SOURCES = {
    "2018": "https://www.regione.toscana.it/documents/10180/479267/Indicatori%2B2018.csv/76a8ecdb-bfac-7280-28af-5ddfd9d16a3d?t=1711025218063",
    "2022": "https://www.regione.toscana.it/documents/10180/12228409/Indicatori%2B2022.csv/65f6cdca-8c07-b5a5-87b5-4870c2226692?t=1727340985500",
    "2024": "https://www.regione.toscana.it/documents/d/guest/indicatori-2024-1",
}
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
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def get_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 OsservatorioVersilia/1.0", "Accept": "text/csv,*/*"})
    with urlopen(req, timeout=90) as resp:
        raw = resp.read()
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def parse(url: str) -> dict[str, dict]:
    text = get_text(url)
    sample = text[:5000]
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=";,\t|").delimiter
    except csv.Error:
        delim = ";"
    rows = list(csv.DictReader(io.StringIO(text), delimiter=delim))

    def code_of(row: dict) -> str:
        for k, v in row.items():
            nk = norm(k)
            digits = re.sub(r"\D", "", str(v or ""))
            if ("cod" in nk or "istat" in nk) and 5 <= len(digits) <= 6:
                return digits.zfill(6)
        return ""

    def town_of(row: dict) -> str:
        for k, v in row.items():
            if norm(k) in {"comune", "denominazione comune", "denominazione"}:
                return str(v or "").strip()
        return ""

    out = {}
    for town, code in TOWNS.items():
        hits = [r for r in rows if code_of(r) == code]
        if not hits:
            hits = [r for r in rows if norm(town_of(r)) == norm(town)]
        if len(hits) != 1:
            raise RuntimeError(f"{town}: attesa una riga, trovate {len(hits)}")
        row = hits[0]
        value = row.get("ind18") or row.get("IND18") or row.get("Ind18")
        if value in (None, "", "nd", "ND"):
            raise RuntimeError(f"{town}: ind18 non disponibile")
        out[town] = {"ind18": value, "row": row}
    return out


def main() -> None:
    data = {year: parse(url) for year, url in SOURCES.items()}
    print("IND18_HISTORY_BEGIN")
    for town in TOWNS:
        vals = {year: data[year][town]["ind18"] for year in SOURCES}
        print(town, vals)
    print("IND18_HISTORY_END")

    # Il file 2024 deve riportare il definitivo 2022, non un falso dato 2024.
    def number(v: str) -> float:
        return float(str(v).replace(".", "").replace(",", "."))
    for town in TOWNS:
        if abs(number(data["2022"][town]["ind18"]) - number(data["2024"][town]["ind18"])) > 0.11:
            raise RuntimeError(f"{town}: il valore 2024 non replica il definitivo 2022")
    print("Confermata serie reale 2018 -> 2022 e carry-forward 2022 nel file 2024, copertura 7/7.")


if __name__ == "__main__":
    main()
