#!/usr/bin/env python3
"""Materializza Morosità ERP v1.25.0 da bilanci E.R.P. Lucca 2020–2024.

Il processo è completamente offline: conserva gli importi elementari pubblicati,
ricalcola le percentuali con una formula unica e versiona uno snapshot con SHA-256
dei cinque PDF sorgente verificati.
"""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data/site-data.json"
REGISTRY = ROOT / "data/source-registry.json"
STATE = ROOT / "data/source-monitor-state.json"
SNAPSHOT = ROOT / "data/source-snapshots/erp-lucca-arrears-2020-2024.json"
FINALIZER = ROOT / "scripts/finalize_catalog_release.py"
CATALOG_TEST = ROOT / "scripts/test_catalog_release_v116.py"
README = ROOT / "README.md"
APP00 = ROOT / "assets/app-parts/00.txt"
APP03 = ROOT / "assets/app-parts/03.txt"
APP05 = ROOT / "assets/app-parts/05.txt"
APPJS = ROOT / "assets/app.js"
UXH = ROOT / "assets/ux-history.js"
UXHC = ROOT / "assets/ux-history-core.js"
EXPORT = ROOT / "assets/export-v161.js"
SW = ROOT / "service-worker.js"
BUILD_SAFE = ROOT / "scripts/build_static_safe.py"
BUILD_BRAND = ROOT / "scripts/build_static_brand.py"
HISTORY = ROOT / "docs/copertura-serie-storiche.md"
COHERENCE = ROOT / "docs/coerenza-interfaccia.md"
WORKFLOW = ROOT / ".github/workflows/pages.yml"

VERSION = "v1.25.0"
UPDATED = "30 agosto 2026"
SOURCE_URL = "https://at.erplucca.it/default?path=75&t=1"
PROFILE = "erp-lucca-annual-balance-sheet"
KEY = "erpArrears"
YEARS = [2020, 2021, 2022, 2023, 2024]
TOWNS = OrderedDict([
    ("046005", ("Camaiore", "camaiore")),
    ("046013", ("Forte dei Marmi", "forte-dei-marmi")),
    ("046018", ("Massarosa", "massarosa")),
    ("046024", ("Pietrasanta", "pietrasanta")),
    ("046028", ("Seravezza", "seravezza")),
    ("046030", ("Stazzema", "stazzema")),
    ("046033", ("Viareggio", "viareggio")),
])
# (emesso cumulato, morosità cumulata), valori in euro letti dai prospetti pubblicati.
DATA = {
    "046005": [(3582792.37,247063.23),(3854507.54,267712.42),(4132419.89,296554.22),(4402239.72,308511.54),(4721245.44,348067.19)],
    "046013": [(2949206.99,172475.09),(3192864.58,194717.67),(3429308.68,225193.13),(3459825.27,246056.52),(3911358.57,272869.37)],
    "046018": [(1656939.53,62971.17),(1755764.28,61148.91),(1860507.25,64950.49),(3164988.55,64990.36),(2078965.36,72398.09)],
    "046024": [(5363800.69,412828.20),(5709770.82,417031.70),(6081755.16,447394.65),(6136480.16,463131.42),(6812489.99,478114.18)],
    "046028": [(4117358.99,216108.44),(4409130.00,208201.92),(4709525.63,211210.84),(4720359.45,219836.25),(5346600.17,235874.51)],
    "046030": [(825116.56,28883.37),(887449.32,28598.67),(947137.77,35187.95),(1259681.08,36132.36),(1036145.57,41967.92)],
    "046033": [(20275358.16,2333819.91),(21713625.62,2401763.10),(23257105.59,2558637.44),(23303630.28,2712346.75),(26379101.73,2855639.38)],
}
DOCUMENTS = [
    {"year":2020,"file":"estratto assemblea Bilancio_2020(1).pdf","sha256":"0362d001246832bc66040c533a14b503ed9e6e3416d11a870638b56ccc3199bd"},
    {"year":2021,"file":"estratto assemblea Soci Bilancio_2021.pdf","sha256":"52d476f097066a3807099202ca508e961c6c61c5efe452a9861df538c980f757"},
    {"year":2022,"file":"estratto assemblea Soci Bilancio_2022.pdf","sha256":"831ba0712eb026ec955e45763831fe12ab6a941bc6f7940c585b888371ff872a"},
    {"year":2023,"file":"estratto assemblea Soci Bilancio_2023.pdf","sha256":"de36675ef97245b818bee99caec598f334166884e61c300c2be28c5d13902983"},
    {"year":2024,"file":"estratto assemblea Soci Bilancio_2024.pdf","sha256":"ca00f1a212d6fa29bdfa688ebc949ee5d9fb3c708342d36f07832add8b495422"},
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rate(issued: float, arrears: float) -> float:
    return arrears / issued * 100.0


def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Pattern non trovato in {path}: {old[:120]}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")


def build_snapshot() -> dict:
    rows = {}
    for code, pairs in DATA.items():
        rows[code] = {
            "town": TOWNS[code][0],
            "values": [
                {"year": year, "issued": issued, "arrears": arrears, "rate": round(rate(issued, arrears), 4)}
                for year, (issued, arrears) in zip(YEARS, pairs)
            ],
        }
    aggregate = []
    for index, year in enumerate(YEARS):
        issued = round(sum(DATA[code][index][0] for code in TOWNS), 2)
        arrears = round(sum(DATA[code][index][1] for code in TOWNS), 2)
        aggregate.append({"year":year,"issued":issued,"arrears":arrears,"rate":round(rate(issued, arrears),4)})
    return {
        "schemaVersion": 1,
        "retrieved": "2026-08-30",
        "publisher": "E.R.P. Lucca S.r.l.",
        "sourcePageUrl": SOURCE_URL,
        "metric": {
            "key": KEY,
            "label": "Morosità ERP",
            "definition": "Rapporto percentuale tra somme non ancora incassate dagli assegnatari per fitti e spese accessorie e importi emessi cumulati per gli alloggi ERP gestiti da E.R.P. Lucca S.r.l.",
            "formula": "morosita_cumulata / emesso_cumulato * 100",
        },
        "scope": {"years": YEARS, "coverage":"7/7", "townCodes":list(TOWNS)},
        "sourceDocuments": DOCUMENTS,
        "rows": rows,
        "aggregate": {"method":"sum_then_ratio", "label":"Versilia · 7 Comuni", "values":aggregate},
        "anomalies": [
            {
                "year": 2022,
                "type": "published_header_date_mismatch",
                "note": "Intestazione tabella riportata come 31/12/2021 nel bilancio 2022; valori riferiti all’esercizio 2022.",
            },
            {
                "year": 2023,
                "type": "published_percentage_inconsistency",
                "note": "Nel prospetto 2023 la colonna percentuale stampata ripete i valori del 2022 e non riconcilia con gli importi elementari pubblicati. L'Osservatorio conserva gli importi pubblicati e ricalcola tutte le percentuali con la formula canonica.",
            },
            {
                "year": 2023,
                "townCode": "046018",
                "town": "Massarosa",
                "type": "source_elementary_discontinuity",
                "note": "Il prospetto 2023 pubblica emesso cumulato 3.164.988,55 € e morosità 64.990,36 €. Il denominatore è conservato senza correzioni, interpolazioni o ricostruzioni; il rapporto ricalcolato è circa 2,05%.",
            },
        ],
    }


def build_metric(snapshot: dict) -> dict:
    rows = []
    for code, (name, slug) in TOWNS.items():
        values = snapshot["rows"][code]["values"]
        current = values[-1]
        rows.append({
            "town": name,
            "code": code,
            "slug": slug,
            "value": round(current["rate"], 2),
            "formatted": f"{current['rate']:.2f}%".replace(".", ","),
            "series": {"years":YEARS, "values":[round(item["rate"],2) for item in values]},
            "accounting": {"year":2024,"issued":current["issued"],"arrears":current["arrears"]},
            "accountingSeries": {
                "years": YEARS,
                "issued": [item["issued"] for item in values],
                "arrears": [item["arrears"] for item in values],
            },
            "normalized": None,
            "benchmarkValue": None,
        })
    aggregate_values = snapshot["aggregate"]["values"]
    current_aggregate = aggregate_values[-1]
    return {
        "meta": {
            "key": KEY,
            "theme": "abitare",
            "label": "Morosità ERP",
            "shortLabel": "Morosità ERP",
            "description": "Quota degli importi emessi cumulati per gli alloggi ERP che risulta ancora non incassata dagli assegnatari per fitti e spese accessorie.",
            "unit": "%",
            "comparisonReference": "aggregate",
            "comparisonLabel": "valore Versilia",
            "comparisonOverline": "Rispetto alla Versilia",
            "comparisonNote": "Il riferimento è il rapporto calcolato sulla somma della morosità e degli importi emessi dei sette Comuni, non la media semplice delle percentuali comunali.",
            "year": "2024",
            "source": "E.R.P. Lucca S.r.l. — Bilanci d’esercizio",
            "polarity": "neutral",
            "context": "ERP e fragilità abitativa",
            "searchTerms": ["morosità erp","edilizia residenziale pubblica","erp lucca","affitti erp","canoni non incassati","assegnatari"],
            "sourceMeta": {
                "snapshot": "data/source-snapshots/erp-lucca-arrears-2020-2024.json",
                "note": "Percentuali ricalcolate dagli importi elementari pubblicati. Nel 2023 le percentuali stampate nel prospetto non vengono utilizzate perché non riconciliano con gli importi.",
            },
        },
        "sourceUrl": SOURCE_URL,
        "rows": rows,
        "aggregate": {
            "value": round(current_aggregate["rate"], 2),
            "formatted": f"{current_aggregate['rate']:.2f}%".replace(".", ","),
            "label": "Versilia · 7 Comuni",
            "note": "Rapporto tra la somma della morosità cumulata e la somma degli importi emessi cumulati dei sette Comuni; non è la media delle percentuali comunali.",
            "series": {"years":YEARS,"values":[round(item["rate"],2) for item in aggregate_values]},
            "accounting": {"year":2024,"issued":current_aggregate["issued"],"arrears":current_aggregate["arrears"]},
            "accountingSeries": {
                "years": YEARS,
                "issued": [item["issued"] for item in aggregate_values],
                "arrears": [item["arrears"] for item in aggregate_values],
            },
        },
        "normalizedAggregate": None,
        "history": {
            "years": YEARS,
            "coverage": "7/7",
            "source": "E.R.P. Lucca S.r.l. — Bilanci d’esercizio",
            "aggregateType": "sum-then-ratio",
            "aggregateLabel": "Versilia · 7 Comuni",
            "note": "Serie 2020–2024 ricalcolata dagli importi elementari pubblicati per ciascun Comune.",
        },
        "method": {
            "type": "Ricalcolo da valori contabili pubblicati",
            "formula": "Morosità cumulata / importi emessi cumulati × 100.",
            "caveat": "Il prospetto 2023 contiene percentuali stampate incoerenti con gli importi elementari e coincidenti con quelle del 2022. Sono quindi usati esclusivamente gli importi pubblicati. Per Massarosa 2023 l’emesso cumulato pubblicato è 3.164.988,55 €: il valore è mantenuto senza interpolazioni o correzioni e produce un rapporto ricalcolato di circa 2,05%.",
            "coverage": "7/7 · 2020–2024",
            "snapshot": "data/source-snapshots/erp-lucca-arrears-2020-2024.json",
        },
    }


def apply_site(site: dict, snapshot: dict) -> None:
    expected_codes = set(TOWNS)
    actual_codes = {town["code"] for town in site.get("towns", [])}
    if actual_codes != expected_codes:
        raise RuntimeError(f"Perimetro comunale inatteso: {actual_codes}")
    metric = build_metric(snapshot)
    rebuilt = OrderedDict()
    inserted = False
    for key, value in site["metrics"].items():
        if key == KEY:
            continue
        rebuilt[key] = value
        if key == "omiResidential":
            rebuilt[KEY] = metric
            inserted = True
    if not inserted:
        rebuilt[KEY] = metric
    site["metrics"] = rebuilt

    theme = site["themes"]["abitare"]
    sections = [section for section in theme.get("sections", []) if section.get("key") != "erp-fragilita-abitativa"]
    section = {
        "key": "erp-fragilita-abitativa",
        "label": "ERP e fragilità abitativa",
        "description": "Morosità degli assegnatari ERP ricostruita dai bilanci del gestore pubblico, con serie storica e valori contabili di base.",
        "metrics": [KEY],
    }
    market_index = next((index for index, item in enumerate(sections) if item.get("key") == "mercato-immobiliare"), -1)
    sections.insert(market_index + 1 if market_index >= 0 else 0, section)
    theme["sections"] = sections
    theme["metrics"] = [metric_key for item in sections for metric_key in item.get("metrics", [])]
    theme["description"] = "Mercato immobiliare, patrimonio, abitazioni non occupate, ERP, struttura familiare e coabitazione."
    site["version"] = VERSION
    site["updated"] = UPDATED


def apply_registry(registry: dict) -> None:
    registry.setdefault("sourceProfiles", {})[PROFILE] = {
        "publisher": "E.R.P. Lucca S.r.l.",
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Dopo l’approvazione del bilancio d’esercizio",
        "acquisitionMethod": "Lettura dei prospetti comunali nei bilanci d’esercizio; importi elementari conservati nello snapshot con SHA-256 dei PDF e percentuali ricalcolate offline.",
        "licenseName": "Condizioni indicate da E.R.P. Lucca S.r.l.",
        "licenseUrl": "https://www.erplucca.it/",
    }
    registry.setdefault("sourceProfileByUrl", {})[SOURCE_URL] = PROFILE
    registry.setdefault("sourceUrlProfiles", {})[SOURCE_URL] = PROFILE
    registry.setdefault("metricOverrides", {})[KEY] = {"profile": PROFILE}
    registry["expectedMetricCount"] = 166
    registry["expectedInlineMetricCount"] = 162
    registry["expectedExternalMetricCount"] = 4


def apply_state(state: dict) -> None:
    checked = state.get("checkedAt") or "2026-08-30T15:54:00+00:00"
    sources = state.setdefault("sources", {})
    current = sources.get(SOURCE_URL, {})
    current.update({
        "url": SOURCE_URL,
        "ok": True,
        "status": 200,
        "finalUrl": SOURCE_URL,
        "contentType": current.get("contentType", "text/html"),
        "contentLength": current.get("contentLength"),
        "etag": current.get("etag", ""),
        "lastModified": current.get("lastModified", ""),
        "contentSha256": current.get("contentSha256", ""),
        "hashTruncated": False,
        "error": "",
        "metrics": [KEY],
        "roles": ["primary"],
        "profileIds": [PROFILE],
        "frequencies": ["annual"],
    })
    sources[SOURCE_URL] = current
    state.setdefault("metrics", {})[KEY] = {
        "publishedPeriod": "2024",
        "checkedAt": checked,
        "observedLatestPeriod": "2024",
        "status": "current",
    }


def patch_ui() -> None:
    text = APP00.read_text(encoding="utf-8")
    synonym_marker = "    cohabitingHouseholds: ['famiglie coabitanti', 'coabitazione', 'disagio abitativo'],"
    synonym_line = "    erpArrears: ['morosità erp', 'edilizia residenziale pubblica', 'erp lucca', 'affitti erp', 'canoni non incassati'],"
    if synonym_line not in text:
        if synonym_marker not in text:
            raise RuntimeError("Marker sinonimi Abitare non trovato")
        text = text.replace(synonym_marker, synonym_marker + "\n" + synonym_line, 1)
    percent_marker = "      case 'percent': return `${number1.format(v)}%`;"
    percent_precise_line = "      case '%': return `${number2.format(v)}%`;"
    if percent_precise_line not in text:
        if percent_marker not in text:
            raise RuntimeError("Marker format percent non trovato")
        text = text.replace(percent_marker, percent_marker + "\n" + percent_precise_line, 1)
    APP00.write_text(text, encoding="utf-8")

    app = APP03.read_text(encoding="utf-8")
    view_marker = "    container.dataset.theme = themeKey;"
    view_line = "    container.classList.toggle('erp-arrears-view', metricKey === 'erpArrears');"
    if view_line not in app:
        if view_marker not in app:
            raise RuntimeError("Marker vista comunale ERP non trovato")
        app = app.replace(view_marker, view_marker + "\n" + view_line, 1)
    helper_marker = "  function compositePartLegend(metric) {"
    helper = r'''  function erpArrearsDetailMarkup(metric, row) {
    if (metric?.meta?.key !== 'erpArrears' || !row?.accounting) return '';
    const detail = row.accounting;
    return `<details class="detail-disclosure erp-arrears-detail"><summary><span>Dettaglio contabile ${html(String(detail.year))}</span><small>valori cumulati · E.R.P. Lucca</small></summary><div class="composite-town-detail"><div><span>Importi emessi cumulati</span><b>${html(formatValue(detail.issued,'currency2'))}</b><small>denominatore del rapporto</small></div><div><span>Morosità cumulata</span><b>${html(formatValue(detail.arrears,'currency2'))}</b><small>somme non ancora incassate</small></div></div><p class="aggregate-note">La percentuale è ricalcolata dagli importi sopra indicati; non viene usata la percentuale stampata nel prospetto sorgente quando non riconcilia.</p></details>`;
  }

'''
    if "function erpArrearsDetailMarkup" not in app:
        if helper_marker not in app:
            raise RuntimeError("Marker helper APP03 non trovato")
        app = app.replace(helper_marker, helper + helper_marker, 1)
    call = "      ${deepDiveMarkup(data, town, themeKey, metricKey)}"
    replacement = call + "\n      ${erpArrearsDetailMarkup(metric,row)}"
    if "${erpArrearsDetailMarkup(metric,row)}" not in app:
        if call not in app:
            raise RuntimeError("Hook dettaglio comunale non trovato")
        app = app.replace(call, replacement, 1)
    APP03.write_text(app, encoding="utf-8")

    history_core = UXHC.read_text(encoding="utf-8")
    precise_percent = "      case '%': return `${formatNumber(number, 2)}%`;"
    percent_line = "      case 'percent': return `${formatNumber(number, 1)}%`;"
    if precise_percent not in history_core:
        if percent_line not in history_core:
            raise RuntimeError("Formatter percent storico non trovato")
        history_core = history_core.replace(percent_line, precise_percent + "\n" + percent_line, 1)
    old_delta = "    if (unit === 'percent' || unit === 'percentagePoints') {"
    new_delta = "    if (unit === '%' || unit === 'percent' || unit === 'percentagePoints') {"
    if new_delta not in history_core:
        if old_delta not in history_core:
            raise RuntimeError("Delta percent storico non trovato")
        history_core = history_core.replace(old_delta, new_delta, 1)
    UXHC.write_text(history_core, encoding="utf-8")



def patch_release_contract() -> None:
    text = FINALIZER.read_text(encoding="utf-8")
    replacements = {
        'release v1.24.0': 'release v1.25.0',
        'VERSION = "v1.24.0"': 'VERSION = "v1.25.0"',
        'UPDATED = "29 agosto 2026"': 'UPDATED = "30 agosto 2026"',
        'EXPECTED_METRICS = 165': 'EXPECTED_METRICS = 166',
        'EXPECTED_INLINE = 161': 'EXPECTED_INLINE = 162',
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
    FINALIZER.write_text(text, encoding="utf-8")

    test = CATALOG_TEST.read_text(encoding="utf-8")
    test = test.replace('release v1.24.0', 'release v1.25.0')
    test = test.replace(
        'assert "2026.08.29-v1.24.0" in app and "2026.08.28-v1.23.0" in app and "165 indicatori complessivi" in app',
        'assert "2026.08.30-v1.25.0" in app and "2026.08.29-v1.24.0" in app and "166 indicatori complessivi" in app',
    )
    test = test.replace('**v1.24.0** — 29 agosto 2026', '**v1.25.0** — 30 agosto 2026')
    test = test.replace('"165 indicatori" in readme and "161 con valori incorporati" in readme', '"166 indicatori" in readme and "162 con valori incorporati" in readme')
    test = test.replace('UX_ASSET_VERSION = "20260830-v124-water-ui3"', 'UX_ASSET_VERSION = "20260830-v125-erp-arrears"')
    test = test.replace('HISTORY_ASSET_VERSION = "20260830-v124-water-ui3"', 'HISTORY_ASSET_VERSION = "20260830-v125-erp-arrears"')
    test = test.replace('APP_BUNDLE_ASSET_VERSION = "20260830-v124-water-ui3"', 'APP_BUNDLE_ASSET_VERSION = "20260830-v125-erp-arrears"')
    test = test.replace('PWA_JS_REVISION = "catalog-v124"', 'PWA_JS_REVISION = "catalog-v125"')
    test = test.replace('20260830-v124" in development_loader', '20260830-v125-erp-arrears" in development_loader')
    test = test.replace("const VERSION = '20260830-v124-water-ui3';", "const VERSION = '20260830-v125-erp-arrears';")
    test = test.replace('ov-pwa-20260830-v124" in service_worker', 'ov-pwa-20260830-v125-erp-arrears" in service_worker')
    CATALOG_TEST.write_text(test, encoding="utf-8")


def patch_project_copy() -> None:
    readme = README.read_text(encoding="utf-8")
    readme = readme.replace('Versione dati corrente: **v1.24.0** — 29 agosto 2026.', 'Versione dati corrente: **v1.25.0** — 30 agosto 2026.')
    readme = readme.replace('165 indicatori', '166 indicatori').replace('161 con valori incorporati', '162 con valori incorporati').replace('161 pagine canoniche', '162 pagine canoniche')
    README.write_text(readme, encoding="utf-8")

    versions = APP05.read_text(encoding="utf-8")
    marker = "      ['2026.08.29-v1.24.0','29 agosto 2026','165 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto Acqua e bonifiche: perdite della rete idrica Istat, qualità dell’acqua potabile GAIA per 70 località e procedimenti SISBON attivi/chiusi, senza proxy per fognatura o depurazione.'],"
    line = "      ['2026.08.30-v1.25.0','30 agosto 2026','166 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunta Morosità ERP: serie 2020–2024 dai bilanci E.R.P. Lucca, percentuali ricalcolate dagli importi elementari e dettaglio contabile 2024 per ciascun Comune.'],"
    if line not in versions:
        if marker not in versions:
            raise RuntimeError("Marker changelog v1.24.0 non trovato")
        versions = versions.replace(marker, line + "\n" + marker, 1)
    APP05.write_text(versions, encoding="utf-8")

    for path in (APPJS, UXH, EXPORT, BUILD_SAFE, BUILD_BRAND):
        replace_all(path, "20260830-v124-water-ui3", "20260830-v125-erp-arrears")
    replace_all(SW, "ov-pwa-20260830-v124-water-ui3", "ov-pwa-20260830-v125-erp-arrears")
    replace_all(BUILD_BRAND, 'PWA_JS_REVISION = "catalog-v124"', 'PWA_JS_REVISION = "catalog-v125"')


def patch_docs() -> None:
    history_marker = "## Morosità ERP v1.25.0"
    history = HISTORY.read_text(encoding="utf-8")
    if history_marker not in history:
        history += (
            "\n\n## Morosità ERP v1.25.0\n\n"
            "L’indicatore `erpArrears` usa i prospetti comunali contenuti nei bilanci E.R.P. Lucca dal 2020 al 2024. "
            "Per ogni anno e Comune conserva importi emessi cumulati e morosità cumulata e calcola `morosità / emesso × 100`. "
            "L’aggregato Versilia è ottenuto sommando prima i due importi dei sette Comuni e calcolando poi il rapporto, non mediando le percentuali. "
            "Nel prospetto 2023 le percentuali stampate non riconciliano con gli importi e coincidono con il 2022: non vengono quindi utilizzate. "
            "Gli importi elementari pubblicati, inclusa la discontinuità 2023 di Massarosa, sono mantenuti senza stime o interpolazioni.\n"
        )
        HISTORY.write_text(history, encoding="utf-8")

    coherence_marker = "### Morosità ERP v1.25.0"
    coherence = COHERENCE.read_text(encoding="utf-8")
    if coherence_marker not in coherence:
        coherence += (
            "\n\n### Morosità ERP v1.25.0\n\n"
            "`erpArrears` resta una metrica percentuale canonica nel tema Abitare. Il confronto usa la grammatica grafica scalare esistente; "
            "le schede comunali riusano serie storica, fonte, metodo e un disclosure con i due importi contabili 2024. "
            "Non vengono introdotti ranking, proxy, punteggi o metriche ERP aggiuntive. La visualizzazione usa due decimali perché le differenze tra Comuni sono contenute.\n"
        )
        COHERENCE.write_text(coherence, encoding="utf-8")


def patch_workflow() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    test_line = "          python scripts/test_erp_arrears_v125.py"
    if test_line not in text:
        anchor = "          python scripts/test_ambiente_acqua_v124_ui.py"
        if anchor not in text:
            raise RuntimeError("Anchor test ambiente non trovato")
        text = text.replace(anchor, anchor + "\n" + test_line, 1)
    json_line = "          python -m json.tool data/source-snapshots/erp-lucca-arrears-2020-2024.json > /dev/null"
    if json_line not in text:
        anchor = "          python -m json.tool data/source-snapshots/costa-mare-v123.json > /dev/null"
        if anchor not in text:
            raise RuntimeError("Anchor json snapshots non trovato")
        text = text.replace(anchor, anchor + "\n" + json_line, 1)
    browser_block = """      - name: Validate Morosità ERP\n        run: |\n          mkdir -p reports/erp-arrears-v125-browser\n          python scripts/test_erp_arrears_v125_browser.py --base http://127.0.0.1:8123/ --screenshots-dir reports/erp-arrears-v125-browser\n\n"""
    if "Validate Morosità ERP" not in text:
        anchor = "      - name: Validate Investimenti e opere\n"
        if anchor not in text:
            raise RuntimeError("Anchor browser Investimenti non trovato")
        text = text.replace(anchor, browser_block + anchor, 1)
    compile_anchor = "            scripts/materialize_ambiente_acqua_v124.py \\\n"
    if "scripts/materialize_erp_arrears_v125.py" not in text:
        if compile_anchor in text:
            text = text.replace(compile_anchor, compile_anchor + "            scripts/materialize_erp_arrears_v125.py \\\n            scripts/test_erp_arrears_v125.py \\\n            scripts/test_erp_arrears_v125_browser.py \\\n", 1)
        else:
            # Il blocco py_compile può non elencare il materializzatore acqua: inserisci prima del finalizer.
            anchor = "            scripts/finalize_catalog_release.py \\\n"
            if anchor not in text:
                raise RuntimeError("Anchor py_compile finalizer non trovato")
            text = text.replace(anchor, "            scripts/materialize_erp_arrears_v125.py \\\n            scripts/test_erp_arrears_v125.py \\\n            scripts/test_erp_arrears_v125_browser.py \\\n" + anchor, 1)
    text = text.replace("osservatorio-versilia-v124-acqua-bonifiche-preview", "osservatorio-versilia-v125-morosita-erp-preview")
    WORKFLOW.write_text(text, encoding="utf-8")


def main() -> None:
    snapshot = build_snapshot()
    save(SNAPSHOT, snapshot)
    site = load(SITE)
    registry = load(REGISTRY)
    state = load(STATE)
    apply_site(site, snapshot)
    apply_registry(registry)
    apply_state(state)
    save(SITE, site)
    save(REGISTRY, registry)
    save(STATE, state)
    patch_ui()
    patch_release_contract()
    patch_project_copy()
    patch_docs()
    patch_workflow()
    print("Morosità ERP v1.25.0 materializzata: 7/7 Comuni, serie 2020–2024, 166 indicatori.")


if __name__ == "__main__":
    main()
