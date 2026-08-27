#!/usr/bin/env python3
"""Ripara storici e medie del lotto Cultura e biblioteche v1.21.0."""
from __future__ import annotations

import base64
import json
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/source-snapshots/regione-toscana-cultura-biblioteche-2024.json"
MATERIALIZER = ROOT / "scripts/materialize_cultura_biblioteche_v121.py"
DATA_TEST = ROOT / "scripts/test_cultura_biblioteche_v121.py"
APP = ROOT / "assets/app-parts/03.txt"
BROWSER_TEST = ROOT / "scripts/test_cultura_biblioteche_v121_browser.py"
HISTORY_DOC = ROOT / "docs/copertura-serie-storiche.md"

PAYLOAD = "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"


def write_snapshot() -> None:
    raw = zlib.decompress(base64.b64decode(PAYLOAD)).decode("utf-8")
    data = json.loads(raw)
    SNAPSHOT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_materializer() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    pattern = re.compile(r"def build_rows\(site: dict, snapshot: dict, metric_key: str, unit: str\) -> list\[dict\]:\n.*?\n    return rows\n", re.S)
    replacement = '''def build_rows(site: dict, snapshot: dict, metric_key: str, unit: str) -> list[dict]:
    series = snapshot["series"][metric_key]
    years = series["years"]
    values = series["values"]
    slug_by_code = {row["code"]: row["slug"] for row in site["metrics"]["population"]["rows"]}
    rows = []
    for town in site["towns"]:
        town_values = values[town["name"]]
        current = town_values[-1]
        pairs = [(year, value) for year, value in zip(years, town_values) if value is not None]
        row_series = {
            "years": [year for year, _ in pairs],
            "values": [value for _, value in pairs],
        } if pairs else None
        rows.append({
            "town": town["name"],
            "code": town["code"],
            "slug": slug_by_code[town["code"]],
            "value": current,
            "formatted": fmt(current, unit),
            "series": row_series,
            "normalized": None,
            "benchmarkValue": current,
        })
    return rows
'''
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("build_rows Cultura non trovato")
    replacements = {
        "Media ponderata per la popolazione 2024 dei cinque Comuni con indicatore disponibile; Massarosa e Stazzema sono esclusi perché n.d.": "Media aritmetica dei cinque Comuni con indicatore 2024 disponibile; Massarosa e Stazzema sono esclusi perché n.d.",
        "0,23 prestiti per residente": "0,34 prestiti per residente",
        "Valore pubblicato nel campo “Indice di prestito Comunale” (prestiti pro capite). Aggregato Versilia = somma(indice comunale × popolazione comunale) / somma(popolazione), sui soli Comuni con dato disponibile.": "Valore pubblicato nel campo “Indice di prestito Comunale” (prestiti pro capite). Aggregato Versilia = media aritmetica dei valori comunali disponibili; i Comuni n.d. non entrano né nel numeratore né nel divisore.",
        "Media ponderata per la popolazione 2024 dei cinque Comuni con indicatore disponibile. È un indice su 100 abitanti, non un conteggio di persone uniche della Versilia.": "Media aritmetica dei cinque Comuni con indicatore 2024 disponibile. È un indice su 100 abitanti, non un conteggio di persone uniche della Versilia.",
        "8,42 ogni 100": "7,89 ogni 100",
        "Valore pubblicato nel campo “Indice di impatto Comunale” = utenti attivi del servizio di prestito su 100 abitanti. Aggregato Versilia = somma(indice comunale × popolazione comunale) / somma(popolazione), sui soli Comuni con dato disponibile.": "Valore pubblicato nel campo “Indice di impatto Comunale” = utenti attivi del servizio di prestito su 100 abitanti. Aggregato Versilia = media aritmetica dei valori comunali disponibili; i Comuni n.d. non entrano né nel numeratore né nel divisore.",
        "Prestiti e impatto espongono la serie recente 2019–2024 e segnalano il 2020 come anno pandemico anomalo.": "Prestiti e impatto espongono l'intera serie ufficiale 1998–2024 dove disponibile e segnalano il 2020 come anno pandemico anomalo.",
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
        elif new not in text:
            raise RuntimeError(f"Pattern materializer non trovato: {old[:70]}")
    MATERIALIZER.write_text(text, encoding="utf-8")


def patch_data_test() -> None:
    text = DATA_TEST.read_text(encoding="utf-8")
    text = text.replace('"libraryLoansPerResident": 0.22957554282827833,', '"libraryLoansPerResident": 0.344,')
    text = text.replace('"libraryActiveBorrowersPer100": 8.421880566636212,', '"libraryActiveBorrowersPer100": 7.886,')
    text = text.replace('require(loans["046005"]["series"]["years"] == [2019, 2020, 2021, 2022, 2023, 2024], "Storico prestiti Camaiore inatteso")', 'require(loans["046005"]["series"]["years"][0] == 1999 and loans["046005"]["series"]["years"][-1] == 2024, "Storico prestiti Camaiore non completo")')
    text = text.replace('require(impact["046005"]["series"]["years"] == [2019, 2020, 2021, 2022, 2023, 2024], "Storico impatto Camaiore inatteso")', 'require(impact["046005"]["series"]["years"][0] == 1998 and impact["046005"]["series"]["years"][-1] == 2024, "Storico impatto Camaiore non completo")')
    anchor = '    require(opening["046005"]["series"]["years"] == [2022, 2023, 2024], "Apertura Camaiore deve partire dal 2022")\n'
    extra = anchor + '''    require(loans["046013"]["series"]["years"][0] == 1998, "Forte prestiti deve includere il 1998")\n    require(impact["046013"]["series"]["years"][0] == 1998, "Forte impatto deve includere il 1998")\n    for metric in (site["metrics"]["libraryLoansPerResident"], site["metrics"]["libraryActiveBorrowersPer100"], site["metrics"]["libraryWeeklyOpeningHours"]):\n        for row in metric["rows"]:\n            if row["series"] is not None:\n                require(all(value is not None for value in row["series"]["values"]), f"{metric['meta']['key']}/{row['town']}: storico contiene null che il renderer convertirebbe in zero")\n    for key in KEYS:\n        available = [row["value"] for row in site["metrics"][key]["rows"] if row["value"] is not None]\n        require(math.isclose(site["metrics"][key]["aggregate"]["value"], sum(available) / len(available), rel_tol=0, abs_tol=1e-12), f"{key}: la media non usa soltanto i Comuni con dato")\n    require("ponderata per la popolazione" not in site["metrics"]["libraryLoansPerResident"]["aggregate"]["note"].lower(), "Prestiti: media ancora ponderata")\n    require("ponderata per la popolazione" not in site["metrics"]["libraryActiveBorrowersPer100"]["aggregate"]["note"].lower(), "Impatto: media ancora ponderata")\n'''
    if 'la media non usa soltanto i Comuni con dato' not in text:
        if anchor not in text:
            raise RuntimeError("Anchor test storico non trovato")
        text = text.replace(anchor, extra, 1)
    DATA_TEST.write_text(text, encoding="utf-8")


def patch_app() -> None:
    text = APP.read_text(encoding="utf-8")
    function = r'''
  function libraryHistoryTableMarkup(metric) {
    const keys = new Set(['libraryLoansPerResident','libraryActiveBorrowersPer100','libraryWeeklyOpeningHours']);
    if (!keys.has(metric?.meta?.key)) return '';
    const rows = metric.rows || [];
    const years = [...new Set(rows.flatMap(row => row.series?.years || []))].sort((a,b)=>a-b);
    if (!years.length) return '';
    const maps = new Map(rows.map(row => [row.code, new Map((row.series?.years || []).map((year,index)=>[year,row.series.values[index]]))]));
    const tableRows = [...years].reverse().map(year => {
      const available = rows.map(row => maps.get(row.code)?.get(year)).filter(value => value !== null && value !== undefined);
      const mean = available.length ? available.reduce((sum,value)=>sum+Number(value),0) / available.length : null;
      const cells = rows.map(row => {
        const value = maps.get(row.code)?.get(year);
        return `<td>${value === null || value === undefined ? 'n.d.' : html(formatValue(value, metric.meta.unit))}</td>`;
      }).join('');
      return `<tr${year === 2020 ? ' class="library-pandemic-year"' : ''}><th scope="row">${html(String(year))}${year === 2020 ? ' *' : ''}</th>${cells}<td><b>${mean === null ? 'n.d.' : html(formatValue(mean, metric.meta.unit))}</b><small>${available.length}/7</small></td></tr>`;
    }).join('');
    const range = `${years[0]}–${years.at(-1)}`;
    const pandemic = years.includes(2020) ? ' * 2020: anno pandemico anomalo.' : '';
    return `<details class="detail-disclosure library-history-detail" open><summary><span>Serie storica completa</span><small>${html(range)} · valori ufficiali disponibili</small></summary><div class="indicator-table-scroll"><table class="library-history-table"><thead><tr><th>Anno</th>${rows.map(row=>`<th>${html(row.town)}</th>`).join('')}<th>Media comuni con dato</th></tr></thead><tbody>${tableRows}</tbody></table></div><p class="aggregate-note">La media di ogni anno è aritmetica e usa esclusivamente i Comuni con un valore disponibile; gli n.d. non entrano nel divisore.${html(pandemic)}</p></details>`;
  }
'''
    if 'function libraryHistoryTableMarkup(metric)' not in text:
        marker = '  function benchmarkMarkup(metric, aggregate, unit, localRow) {'
        if marker not in text:
            raise RuntimeError("Marker benchmarkMarkup non trovato")
        text = text.replace(marker, function + '\n' + marker, 1)
    old = '    tools.innerHTML = `${methodDisclosure(metric)}<div class="data-actions">'
    new = '    tools.innerHTML = `${libraryHistoryTableMarkup(metric)}${methodDisclosure(metric)}<div class="data-actions">'
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise RuntimeError("Inserimento storico nel compare non trovato")
    APP.write_text(text, encoding="utf-8")


def patch_browser_test() -> None:
    text = BROWSER_TEST.read_text(encoding="utf-8")
    anchor = '        assert_missing_rows(page.locator("#compare-bars .bar-row"), key)\n'
    extra = anchor + '''        history = page.locator(".library-history-detail")\n        assert history.count() == 1, f"{key}: storico completo non visibile nel confronto"\n        history_text = history.inner_text()\n        assert "Media comuni con dato" in history_text\n        if key in ("libraryLoansPerResident", "libraryActiveBorrowersPer100"):\n            assert "1998" in history_text and "2024" in history_text and "2020" in history_text\n        else:\n            assert "2022" in history_text and "2024" in history_text and "2021" not in history_text\n'''
    if 'storico completo non visibile nel confronto' not in text:
        if anchor not in text:
            raise RuntimeError("Anchor browser storico non trovato")
        text = text.replace(anchor, extra, 1)
    BROWSER_TEST.write_text(text, encoding="utf-8")


def patch_history_doc() -> None:
    text = HISTORY_DOC.read_text(encoding="utf-8")
    text = text.replace("Prestiti e impatto espongono la serie recente 2019–2024", "Prestiti e impatto espongono l'intera serie ufficiale 1998–2024 dove disponibile")
    if "media aritmetica dei soli Comuni con valore disponibile" not in text:
        text += "\nPer Cultura e biblioteche, le medie territoriali annuali sono medie aritmetiche dei soli Comuni con valore disponibile nell'anno; gli `n.d.` non entrano nel divisore.\n"
    HISTORY_DOC.write_text(text, encoding="utf-8")


def main() -> None:
    write_snapshot()
    patch_materializer()
    patch_data_test()
    patch_app()
    patch_browser_test()
    patch_history_doc()
    print("Riparazione Cultura pronta: storici completi e medie sui soli Comuni con dato.")


if __name__ == "__main__":
    main()
