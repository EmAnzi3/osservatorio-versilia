#!/usr/bin/env python3
"""Audit riproducibile delle fonti comunali toscane e dei bilanci degli enti.

Lo script non modifica il sito. Scarica fonti ufficiali, filtra i sette Comuni
della Versilia, verifica la copertura 7/7 e documenta il livello di dettaglio
raggiungibile per i bilanci comunali tramite SIFAL e OpenBDAP.
"""
from __future__ import annotations

import io
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

OUT = Path("audit-toscana-comunali-bilanci")
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
NORM_TOWNS = {" ".join(v.upper().split()): v for v in TOWNS.values()}

INDICATOR_LABELS = {
    "ind01": "Variazione percentuale triennale della popolazione residente",
    "ind02": "Popolazione over 80 sul totale",
    "ind03": "Saldo naturale relativizzato",
    "ind04": "Giovani stranieri 0-19 anni sulla popolazione straniera",
    "ind05": "Giovani 15-24 anni in altra condizione professionale",
    "ind06": "Individui 25-49 anni con titolo terziario",
    "ind07": "Contribuenti sotto 10.000 euro",
    "ind08": "Reddito imponibile medio per contribuente",
    "ind09": "Persone in cerca di occupazione sulle forze di lavoro 15+",
    "ind10": "Ditte individuali con conduttore nato all'estero",
    "ind11": "Rischio ambientale",
    "ind12": "Suolo consumato",
    "ind13": "Pressione turistica per 1.000 abitanti",
    "ind14": "Tempo di risposta 118, 75° percentile",
    "ind15": "Organizzazioni sociali iscritte agli albi per 10.000 residenti",
    "ind16": "Persone 0-64 anni con disabilità per 1.000 residenti 0-64",
    "ind17": "Unità locali di assistenza sanitaria per 1.000 abitanti",
    "ind18": "Servizi comunali online al massimo livello",
    "ind19": "Imprese attive nei settori dell'innovazione",
    "ind20": "Superficie agricola utilizzata biologica",
}

PAGES = {
    "indicatori": "https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali",
    "statistiche": "https://www.regione.toscana.it/statistiche",
    "ckan": "https://dati.toscana.it/api/3/action/package_search",
    "sifal": "https://www.regione.toscana.it/-/sistema-informativo-della-finanza-delle-autonomie-locali-sifal-entrate-e-spese",
    "openbdap": "https://openbdap.rgs.mef.gov.it/it/FET/Analizza/",
}


def norm(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


def get(url: str, *, s: requests.Session | None = None, timeout: int = 180, **kwargs) -> requests.Response:
    client = s or requests
    headers = dict(kwargs.pop("headers", {}))
    headers.setdefault("User-Agent", UA)
    response = client.get(url, timeout=timeout, allow_redirects=True, headers=headers, **kwargs)
    response.raise_for_status()
    return response


def read_csv(raw: bytes) -> pd.DataFrame:
    last: Exception | None = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        for sep in (";", ",", "\t"):
            try:
                frame = pd.read_csv(io.BytesIO(raw), encoding=enc, sep=sep, dtype=str)
                if frame.shape[1] > 1:
                    return frame
            except Exception as exc:
                last = exc
    raise RuntimeError(f"CSV non leggibile: {last}")


def identify_town_rows(frame: pd.DataFrame) -> tuple[pd.DataFrame, str | None, str | None]:
    code_col = None
    name_col = None
    for col in frame.columns:
        n = norm(col)
        if code_col is None and ("COD" in n and ("COM" in n or "ISTAT" in n)):
            code_col = col
        if name_col is None and (n in {"COMUNE", "DENOMINAZIONE COMUNE", "NOME COMUNE"} or "DENOMINAZIONE" in n):
            name_col = col
    mask = pd.Series(False, index=frame.index)
    if code_col:
        codes = frame[code_col].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
        mask |= codes.isin(TOWNS)
    if name_col:
        mask |= frame[name_col].map(norm).isin({norm(v) for v in TOWNS.values()})
    selected = frame.loc[mask].copy()
    if code_col:
        selected["_codice_istat"] = selected[code_col].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
        selected["_comune_osservatorio"] = selected["_codice_istat"].map(TOWNS)
    elif name_col:
        selected["_comune_osservatorio"] = selected[name_col].map(lambda x: NORM_TOWNS.get(norm(x)))
    return selected, code_col, name_col


def audit_indicatori() -> dict:
    s = session()
    page = get(PAGES["indicatori"], s=s)
    soup = BeautifulSoup(page.text, "html.parser")
    year_links: dict[str, str] = {}
    metadata_url = None
    for anchor in soup.find_all("a", href=True):
        text = " ".join(anchor.get_text(" ", strip=True).split())
        href = urljoin(page.url, anchor["href"])
        match = re.search(r"Indicatori\s+(20(?:18|19|2[0-6]))", text, re.I)
        if match:
            year_links[match.group(1)] = href
        if "metadati" in text.lower():
            metadata_url = href
    result: dict[str, object] = {"page": page.url, "metadata": metadata_url, "years": {}}
    combined = []
    for year, url in sorted(year_links.items()):
        response = get(url, s=s)
        frame = read_csv(response.content)
        selected, code_col, name_col = identify_town_rows(frame)
        selected.insert(0, "_anno_file", year)
        selected.to_csv(OUT / f"indicatori_{year}_versilia.csv", index=False)
        combined.append(selected)
        indicator_cols = [c for c in frame.columns if norm(c).startswith("IND")]
        coverage = {}
        for col in indicator_cols:
            values = selected[col].astype(str).str.strip() if col in selected else pd.Series(dtype=str)
            available = (~values.str.lower().isin({"nd", "nan", "", "none"})).sum()
            code = norm(col).replace(" ", "").lower()
            coverage[code] = {
                "label": INDICATOR_LABELS.get(code, col),
                "available": int(available),
                "coverage": f"{int(available)}/7",
                "values": {
                    str(row.get("_comune_osservatorio")): row.get(col)
                    for _, row in selected.iterrows()
                },
            }
        result["years"][year] = {
            "url": response.url,
            "bytes": len(response.content),
            "shape": list(frame.shape),
            "columns": list(frame.columns),
            "code_column": code_col,
            "name_column": name_col,
            "town_rows": int(selected.shape[0]),
            "coverage": coverage,
        }
    if combined:
        pd.concat(combined, ignore_index=True).to_csv(OUT / "indicatori_2018_2024_versilia.csv", index=False)
    return result


def audit_ckan() -> dict:
    params = {
        "fq": "organization:regione-toscana groups:statistica",
        "rows": 1000,
        "start": 0,
    }
    response = get(PAGES["ckan"], params=params)
    payload = response.json()
    packages = payload.get("result", {}).get("results", [])
    inventory = []
    municipal = []
    keywords = ("comune", "comuni", "comunale", "municipal")
    high_value = ("bilanc", "lavor", "occup", "impres", "infortun", "bio", "sanitar", "disabil", "demograf", "migr", "turis", "social")
    for package in packages:
        resources = package.get("resources") or []
        text = " ".join([
            str(package.get("title", "")), str(package.get("notes", "")),
            " ".join(str(t.get("name", "")) for t in package.get("tags") or []),
            " ".join(str(r.get("name", "")) + " " + str(r.get("description", "")) for r in resources),
        ])
        row = {
            "name": package.get("name"),
            "title": package.get("title"),
            "url": "https://dati.toscana.it/dataset/" + str(package.get("name")),
            "modified": package.get("metadata_modified"),
            "formats": sorted({str(r.get("format", "")) for r in resources if r.get("format")}),
            "resources": [
                {"name": r.get("name"), "format": r.get("format"), "url": r.get("url")}
                for r in resources
            ],
        }
        inventory.append(row)
        low = norm(text).lower()
        if any(k in low for k in keywords):
            row["priority"] = sum(k in low for k in high_value)
            municipal.append(row)
    inventory.sort(key=lambda x: (str(x.get("title")) or "").lower())
    municipal.sort(key=lambda x: (-int(x.get("priority", 0)), (str(x.get("title")) or "").lower()))
    (OUT / "ckan_statistica_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "ckan_municipal_candidates.json").write_text(json.dumps(municipal, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame([{k: v for k, v in row.items() if k != "resources"} for row in municipal]).to_csv(OUT / "ckan_municipal_candidates.csv", index=False)
    return {"count": len(packages), "municipal_candidates": len(municipal), "top": municipal[:50]}


def audit_sifal() -> dict:
    page = get(PAGES["sifal"])
    soup = BeautifulSoup(page.text, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        text = " ".join(anchor.get_text(" ", strip=True).split())
        href = urljoin(page.url, anchor["href"])
        if any(term in (text + " " + href).lower() for term in ("sifal", "pentaho", "excel", "entrate", "spese", "indicator")):
            links.append({"text": text, "url": href})
    result = {
        "page": page.url,
        "links": links,
        "documented_flows": ["CCB", "CBP", "TRIB", "INDEB", "PDS", "PDSO", "CONSOLID", "CCBS", "CBPS"],
        "documented_exports": ["xls", "csv", "pdf"],
        "assessment": {
            "strengths": ["serie storica lunga", "dati certificati dei Comuni toscani", "indicatori pro capite precalcolati"],
            "limits": ["interfaccia Pentaho datata", "aggiornamento pubblico non chiaramente documentato", "schema meno standard e meno facilmente automatizzabile di OpenBDAP"],
        },
    }
    (OUT / "sifal_page.html").write_bytes(page.content)
    return result


def audit_openbdap_static() -> dict:
    page = get(PAGES["openbdap"])
    soup = BeautifulSoup(page.text, "html.parser")
    links = []
    scripts = []
    for tag in soup.find_all(["a", "script"]):
        value = tag.get("href") if tag.name == "a" else tag.get("src")
        if not value:
            continue
        absolute = urljoin(page.url, value)
        record = {"tag": tag.name, "text": " ".join(tag.get_text(" ", strip=True).split())[:200], "url": absolute}
        (scripts if tag.name == "script" else links).append(record)
    (OUT / "openbdap_page.html").write_bytes(page.content)
    return {
        "page": page.url,
        "links": links,
        "scripts": scripts,
        "documented_detail": {
            "spesa": ["missione", "programma", "titolo", "macroaggregato", "piano dei conti fino al massimo livello disponibile"],
            "entrata": ["titolo", "tipologia", "categoria", "piano dei conti fino al massimo livello disponibile"],
            "rendiconto_measures": ["previsioni definitive", "residui", "accertamenti", "impegni", "incassi", "pagamenti"],
            "documents": ["previsione", "rendiconto", "consolidato", "piano degli indicatori"],
            "series": "dal 2016 per i bilanci armonizzati; dati pre-armonizzazione separati per il periodo precedente",
        },
    }


def audit_openbdap_browser() -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"error": f"Playwright non disponibile: {exc!r}"}
    result: dict[str, object] = {"requests": [], "responses": [], "downloads": [], "dom_links": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True, locale="it-IT")
        page = context.new_page()
        page.on("request", lambda req: result["requests"].append(req.url) if any(x in req.url.lower() for x in ("fet", "download", "bilanc", "schema", "rendic")) else None)
        page.on("response", lambda res: result["responses"].append({"status": res.status, "url": res.url, "type": res.request.resource_type}) if any(x in res.url.lower() for x in ("fet", "download", "bilanc", "schema", "rendic")) else None)
        page.goto(PAGES["openbdap"], wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(5000)
        result["title"] = page.title()
        result["url"] = page.url
        result["dom_links"] = page.locator("a").evaluate_all("els => els.map(a => ({text:(a.innerText||'').trim(), href:a.href})).filter(x => x.text || x.href)")
        result["buttons"] = page.locator("button").evaluate_all("els => els.map(b => ({text:(b.innerText||'').trim(), id:b.id, cls:b.className}))")
        result["selects"] = page.locator("select").evaluate_all("els => els.map(s => ({id:s.id,name:s.name,options:[...s.options].map(o=>({text:o.text,value:o.value,selected:o.selected}))}))")
        result["html"] = page.content()[:2_000_000]
        (OUT / "openbdap_rendered.html").write_text(page.content(), encoding="utf-8")
        browser.close()
    result["requests"] = sorted(set(result["requests"]))
    unique_responses = {}
    for item in result["responses"]:
        unique_responses[item["url"]] = item
    result["responses"] = list(unique_responses.values())
    return result


def build_assessment(report: dict) -> dict:
    ind2024 = report.get("indicatori", {}).get("years", {}).get("2024", {}).get("coverage", {})
    strong = []
    partial = []
    for code, info in ind2024.items():
        row = {"code": code, **info}
        (strong if info.get("coverage") == "7/7" else partial).append(row)
    return {
        "municipal_indicators_2024": {
            "coverage_7_7": strong,
            "partial_or_missing": partial,
        },
        "budget_recommendation": {
            "primary_source": "OpenBDAP – bilanci armonizzati",
            "secondary_source": "SIFAL – indicatori regionali e serie storiche di controllo",
            "recommended_public_granularity": {
                "dashboard": [
                    "entrate correnti pro capite per titolo",
                    "spesa corrente pro capite per missione",
                    "spesa in conto capitale pro capite per missione",
                    "autonomia tributaria",
                    "capacità di riscossione",
                    "capacità di pagamento",
                    "debito pro capite",
                    "risultato di amministrazione pro capite",
                ],
                "detail_pages": [
                    "missione e programma per la spesa",
                    "titolo, tipologia e categoria per l'entrata",
                    "competenza e residui separati",
                    "impegni/accertamenti separati da pagamenti/incassi",
                ],
                "avoid": [
                    "mescolare competenza e cassa",
                    "confrontare previsione e rendiconto come se fossero equivalenti",
                    "pubblicare il massimo dettaglio del piano dei conti come elenco principale senza aggregazione leggibile",
                ],
            },
        },
    }


def main() -> None:
    report: dict[str, object] = {"sources": PAGES}
    for key, func in (
        ("indicatori", audit_indicatori),
        ("ckan", audit_ckan),
        ("sifal", audit_sifal),
        ("openbdap_static", audit_openbdap_static),
        ("openbdap_browser", audit_openbdap_browser),
    ):
        try:
            report[key] = func()
            print(key, "OK", flush=True)
        except Exception as exc:
            report[key] = {"error": repr(exc)}
            print(key, "ERROR", repr(exc), flush=True)
    report["assessment"] = build_assessment(report)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (OUT / "SUMMARY.md").write_text(
        "# Audit fonti comunali Toscana e bilanci\n\n"
        "Il report completo è in `report.json`. L'audit non modifica il dataset del sito.\n",
        encoding="utf-8",
    )
    print(json.dumps(report["assessment"], ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
