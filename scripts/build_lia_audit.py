#!/usr/bin/env python3
"""Scarica e verifica le fonti ufficiali candidate per Lavoro, Istruzione e Abitare.

Non modifica il dataset del sito. Produce soltanto file di audit leggibili.
"""
from __future__ import annotations

import io
import json
import re
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

OUT = Path("lia-audit")
OUT.mkdir(exist_ok=True)
UA = "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)"
TOWNS = {
    "046005": "Camaiore",
    "046013": "Forte dei Marmi",
    "046018": "Massarosa",
    "046024": "Pietrasanta",
    "046028": "Seravezza",
    "046030": "Stazzema",
    "046033": "Viareggio",
}
TOWN_NAMES = set(TOWNS.values())


def norm(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def get(url: str, session: requests.Session | None = None, timeout: int = 180) -> requests.Response:
    s = session or requests
    response = s.get(url, timeout=timeout, allow_redirects=True, headers={"User-Agent": UA})
    response.raise_for_status()
    return response


def read_csv_bytes(raw: bytes) -> pd.DataFrame:
    last: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding=encoding, dtype=str)
        except Exception as exc:
            last = exc
    raise RuntimeError(f"CSV non leggibile: {last}")


def find_download(home_url: str, prefix: str, school_year: str = "202425") -> tuple[requests.Session, str]:
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    page = session.get(home_url, timeout=120)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, "html.parser")
    candidates: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        name = Path(href.split("?", 1)[0]).name
        if name.startswith(prefix) and school_year in name and name.lower().endswith(".csv"):
            candidates.append(urljoin(page.url, href))
    if not candidates:
        raise RuntimeError(f"Distribuzione {prefix} {school_year} non trovata in {home_url}")
    return session, sorted(set(candidates))[-1]


def download_mim(prefix: str, area: str, school_year: str = "202425") -> tuple[pd.DataFrame, str]:
    home = f"https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area={area}"
    session, url = find_download(home, prefix, school_year)
    response = session.get(
        url,
        timeout=240,
        headers={"User-Agent": UA, "Referer": home, "Accept": "text/csv,application/octet-stream,*/*;q=0.8"},
    )
    response.raise_for_status()
    ctype = response.headers.get("content-type", "").lower()
    if "html" in ctype or response.content.lstrip().startswith(b"<!DOCTYPE html"):
        raise RuntimeError(f"MIM ha restituito HTML invece del CSV per {prefix}: {url}")
    frame = read_csv_bytes(response.content)
    return frame, url


def column(frame: pd.DataFrame, *names: str) -> str:
    lookup = {norm(c): c for c in frame.columns}
    for name in names:
        if norm(name) in lookup:
            return lookup[norm(name)]
    raise KeyError(f"Colonna assente tra {names}; disponibili: {list(frame.columns)}")


def number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")


def audit_mim() -> dict:
    sources: dict[str, str] = {}
    data: dict[str, pd.DataFrame] = {}
    specs = {
        "registry_state": ("SCUANAGRAFESTAT", "Scuole"),
        "registry_private": ("SCUANAGRAFEPAR", "Scuole"),
        "classes_state": ("ALUCORSOINDCLASTA", "Studenti"),
        "classes_private": ("ALUCORSOINDCLAPAR", "Studenti"),
        "time_state": ("ALUTEMPOSCUOLASTA", "Studenti"),
        "time_private": ("ALUTEMPOSCUOLAPAR", "Studenti"),
    }
    for key, (prefix, area) in specs.items():
        frame, url = download_mim(prefix, area)
        data[key] = frame
        sources[key] = url
        print("MIM", key, frame.shape, url, flush=True)

    registry_parts = []
    for kind in ("state", "private"):
        frame = data[f"registry_{kind}"].copy()
        school = column(frame, "CODICESCUOLA")
        town = column(frame, "DESCRIZIONECOMUNE")
        order = column(frame, "DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA")
        subset = frame.loc[frame[town].map(norm).isin({norm(x) for x in TOWN_NAMES}), [school, town, order]].copy()
        subset.columns = ["school_code", "town", "school_order"]
        subset["sector"] = kind
        registry_parts.append(subset)
    registry = pd.concat(registry_parts, ignore_index=True).drop_duplicates(["school_code", "sector"])
    registry["town"] = registry["town"].str.title()
    registry.to_csv(OUT / "mim_registry_versilia.csv", index=False)

    class_parts = []
    for kind in ("state", "private"):
        frame = data[f"classes_{kind}"].copy()
        school = column(frame, "CODICESCUOLA")
        classes = column(frame, "CLASSI")
        male = column(frame, "ALUNNIMASCHI")
        female = column(frame, "ALUNNIFEMMINE")
        order = column(frame, "ORDINESCUOLA")
        part = frame[[school, order, classes, male, female]].copy()
        part.columns = ["school_code", "school_order", "classes", "male", "female"]
        part["classes"] = number(part["classes"])
        part["students"] = number(part["male"]).fillna(0) + number(part["female"]).fillna(0)
        part["sector"] = kind
        class_parts.append(part)
    classes = pd.concat(class_parts, ignore_index=True).merge(registry[["school_code", "sector", "town"]], on=["school_code", "sector"], how="inner")
    class_summary = classes.groupby("town", as_index=False).agg(students=("students", "sum"), classes=("classes", "sum"))
    class_summary["students_per_class"] = (class_summary["students"] / class_summary["classes"]).round(2)
    class_summary.to_csv(OUT / "mim_students_classes_versilia.csv", index=False)

    time_parts = []
    for kind in ("state", "private"):
        frame = data[f"time_{kind}"].copy()
        school = column(frame, "CODICESCUOLA")
        order = column(frame, "ORDINESCUOLA")
        time = column(frame, "TEMPOSCUOLA")
        male = column(frame, "ALUNNIMASCHI")
        female = column(frame, "ALUNNIFEMMINE")
        part = frame[[school, order, time, male, female]].copy()
        part.columns = ["school_code", "school_order", "school_time", "male", "female"]
        part["students"] = number(part["male"]).fillna(0) + number(part["female"]).fillna(0)
        part["sector"] = kind
        time_parts.append(part)
    times = pd.concat(time_parts, ignore_index=True).merge(registry[["school_code", "sector", "town"]], on=["school_code", "sector"], how="inner")
    primary = times[times["school_order"].map(norm).eq("SCUOLA PRIMARIA")].copy()
    primary["full_time_students"] = primary["students"].where(primary["school_time"].map(norm).eq("TEMPO PIENO"), 0)
    time_summary = primary.groupby("town", as_index=False).agg(primary_students=("students", "sum"), full_time_students=("full_time_students", "sum"))
    time_summary["full_time_share"] = (100 * time_summary["full_time_students"] / time_summary["primary_students"]).round(1)
    time_summary.to_csv(OUT / "mim_primary_full_time_versilia.csv", index=False)

    audit = class_summary.merge(time_summary, on="town", how="outer").sort_values("town")
    audit.to_csv(OUT / "mim_candidate_indicators.csv", index=False)
    return {"sources": sources, "rows": audit.to_dict(orient="records")}


def download_istat_extract() -> tuple[Path, Path, str]:
    url = "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip"
    with get(url, timeout=900) as response:
        raw = response.content
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        tuscany_name = next(n for n in archive.namelist() if "R09_Toscana" in n)
        layout_name = next(n for n in archive.namelist() if "TRACCIATO" in n.upper())
        tmp = Path(tempfile.mkdtemp(prefix="lia-istat-"))
        tuscany = tmp / "R09_Toscana_2023_sezioni.xlsx"
        layout = tmp / "TRACCIATO_FILE_REGIONALI.xlsx"
        tuscany.write_bytes(archive.read(tuscany_name))
        layout.write_bytes(archive.read(layout_name))
    return tuscany, layout, url


def audit_istat() -> dict:
    tuscany_path, layout_path, source_url = download_istat_extract()
    layout_sheets = pd.read_excel(layout_path, sheet_name=None, dtype=str)
    data_sheets = pd.read_excel(tuscany_path, sheet_name=None, dtype=str)
    overview = {
        "layout_sheets": {k: {"shape": list(v.shape), "columns": list(v.columns)} for k, v in layout_sheets.items()},
        "data_sheets": {k: {"shape": list(v.shape), "columns": list(v.columns)} for k, v in data_sheets.items()},
    }
    (OUT / "istat_workbook_overview.json").write_text(json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8")

    for name, frame in layout_sheets.items():
        frame.to_csv(OUT / f"istat_layout_{norm(name).lower().replace(' ', '_')}.csv", index=False)

    data_name, data = max(data_sheets.items(), key=lambda item: item[1].shape[0])
    code_candidates = [c for c in data.columns if norm(c) in {"PROCOM", "COD PROCOM", "CODICE COMUNE", "CODICECOMUNE", "PRO COM"}]
    if not code_candidates:
        code_candidates = [c for c in data.columns if "PROCOM" in norm(c).replace(" ", "") or "COMUNE" in norm(c)]
    code_col = code_candidates[0]
    codes = data[code_col].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
    selected = data.loc[codes.isin(TOWNS)].copy()
    selected.insert(0, "town", codes[codes.isin(TOWNS)].map(TOWNS))
    selected.insert(1, "municipality_code", codes[codes.isin(TOWNS)])
    selected.to_csv(OUT / "istat_sections_versilia_raw.csv", index=False)

    layout_text = pd.concat(layout_sheets.values(), ignore_index=True).astype(str)
    candidate_words = re.compile(r"occup|disoccup|attiv|lavor|titolo|istruz|diplom|laure|abitaz|allogg|propriet|affitt|superfic|famigl", re.I)
    candidate_layout = layout_text[layout_text.apply(lambda row: row.str.contains(candidate_words, na=False).any(), axis=1)]
    candidate_layout.to_csv(OUT / "istat_candidate_variables.csv", index=False)

    numeric = selected.drop(columns=["town", "municipality_code"], errors="ignore").copy()
    for col in numeric.columns:
        numeric[col] = pd.to_numeric(numeric[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    aggregate = pd.concat([selected[["town", "municipality_code"]].reset_index(drop=True), numeric.reset_index(drop=True)], axis=1)
    aggregate.groupby(["town", "municipality_code"], as_index=False).sum(numeric_only=True).to_csv(OUT / "istat_sections_versilia_aggregated.csv", index=False)
    return {"source": source_url, "sheet": data_name, "code_column": code_col, "section_rows": int(selected.shape[0]), "candidate_variables": int(candidate_layout.shape[0])}


def audit_tourism() -> dict:
    page_url = "https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0"
    page = get(page_url)
    soup = BeautifulSoup(page.text, "html.parser")
    links: dict[str, str] = {}
    for anchor in soup.find_all("a", href=True):
        text = norm(anchor.get_text(" ", strip=True))
        if "LOCAZIONI" in text:
            links["rentals"] = urljoin(page.url, anchor["href"])
        elif "CONSISTENZA" in text and "STRUTTURE" in text:
            links["supply"] = urljoin(page.url, anchor["href"])
    result: dict[str, object] = {"page": page.url, "files": links, "matches": {}}
    for label, url in links.items():
        raw = get(url).content
        sheets = pd.read_excel(io.BytesIO(raw), sheet_name=None, engine="odf", dtype=str)
        result["matches"][label] = {}
        for sheet_name, frame in sheets.items():
            mask = frame.apply(lambda row: row.map(norm).isin({norm(x) for x in TOWN_NAMES}).any(), axis=1)
            matches = frame.loc[mask].copy()
            if not matches.empty:
                safe = norm(sheet_name).lower().replace(" ", "_") or "sheet"
                matches.to_csv(OUT / f"tourism_{label}_{safe}.csv", index=False)
                result["matches"][label][sheet_name] = matches.to_dict(orient="records")
        result[f"{label}_sheets"] = {k: {"shape": list(v.shape), "columns": list(v.columns)} for k, v in sheets.items()}
    return result


def main() -> None:
    report: dict[str, object] = {}
    tasks = (("mim", audit_mim), ("istat", audit_istat), ("tourism", audit_tourism))
    for label, task in tasks:
        try:
            report[label] = task()
        except Exception as exc:
            report[label] = {"error": repr(exc)}
            print(label, "ERROR", repr(exc), flush=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
