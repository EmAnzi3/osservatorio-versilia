#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Pattern non trovato: {label}")
    return text.replace(old, new, 1)


def patch_snapshot() -> None:
    path = ROOT / "data/source-snapshots/istat-agricoltura-territorio-2020.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    src = data["sources"]["localizedCrops"]
    src["query"] = src["query"].replace(
        "ARU.ALL+ARLAND+OLIVOOILTR+VINEY+PGRAPM.TOT",
        "ARU.ALL+ARLAND+OLIVOOILTR+OLIVTTR+VINEY+PGRAPM.TOT",
    )
    data["definitions"]["OLIVTTR"] = "Olivo per produzione di olive da tavola"
    data["coveragePolicy"]["exceptions"] = {
        "OLIVTTR": "Olive da tavola: pubblicazione approvata con copertura 4/7; riga assente = n.d., non zero."
    }
    values = {
        "046005": 0.30,
        "046013": None,
        "046018": 0.23,
        "046024": 0.10,
        "046028": 1.00,
        "046030": None,
        "046033": None,
    }
    for code, value in values.items():
        data["towns"][code]["cropsHa"]["OLIVTTR"] = value
    data["derivations"]["comparisonReference"] = (
        "Nei confronti grafici e nelle schede comunali il riferimento Versilia è la media semplice "
        "dei valori comunali disponibili; i totali territoriali restano distinti e sono usati solo quando esplicitamente indicati."
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_materializer() -> None:
    rel = "scripts/materialize_agricoltura_territorio_v120.py"
    text = read(rel)
    text = replace_once(
        text,
        '    ("OLIVOOILTR", "Olivo da olio"),\n    ("VINEY", "Vite"),',
        '    ("OLIVOOILTR", "Olivo da olio"),\n    ("OLIVTTR", "Olive da tavola"),\n    ("VINEY", "Vite"),',
        "CROP_PARTS olive da tavola",
    )
    text = replace_once(
        text,
        '        minimum = 6\n        if present < minimum:',
        '        minimum = 4 if crop == "OLIVTTR" else 6\n        if present < minimum:',
        "eccezione copertura OLIVTTR",
    )
    text = replace_once(
        text,
        '    towns = site["towns"]\n\n    def item(town: dict) -> dict:',
        '    towns = site["towns"]\n    slug_by_code = {row["code"]: row["slug"] for row in site["metrics"]["population"]["rows"]}\n\n    def item(town: dict) -> dict:',
        "slug canonici",
    )
    text = text.replace(
        '"town": t["name"], "code": t["code"],',
        '"town": t["name"], "code": t["code"], "slug": slug_by_code[t["code"]],',
    )
    text = replace_once(
        text,
        '"normalized": {"value": share, "year": 2020},',
        '"normalized": {"label": "Quota della superficie comunale occupata da SAU", "value": share, "unit": "percent", "year": 2020},',
        "label/unit quota SAU",
    )
    text = replace_once(
        text,
        '            "value": sum(present) if len(present) == 7 else None,',
        '            "value": sum(present) if present else None,',
        "totale colture su comuni disponibili",
    )
    text = replace_once(
        text,
        '            "note": "Per categorie con copertura incompleta il totale Versilia resta n.d.; la somma dei soli Comuni disponibili è conservata come dato tecnico nello snapshot/materializzazione.",',
        '            "note": "Il totale di ciascuna coltura è la somma dei Comuni con dato disponibile; la copertura è sempre dichiarata e i Comuni senza riga restano n.d.",',
        "nota aggregato colture",
    )
    text = text.replace(
        'ARLAND, OLIVOOILTR, VINEY, PGRAPM.',
        'ARLAND, OLIVOOILTR, OLIVTTR, VINEY, PGRAPM.',
    )
    text = replace_once(
        text,
        '            "caveat": "Una riga assente non è interpretata come zero. Vite: 6/7 (Forte dei Marmi n.d.). Non sono pubblicate sottodimensioni con copertura inferiore a 6/7.",',
        '            "caveat": "Una riga assente non è interpretata come zero. Vite: 6/7 (Forte dei Marmi n.d.). Olive da tavola: eccezione esplicitamente approvata 4/7; Forte dei Marmi, Stazzema e Viareggio restano n.d.",',
        "caveat colture",
    )
    text = replace_once(
        text,
        '            "coverage": "7/7 seminativi, olivo da olio e prati/pascoli; 6/7 vite",',
        '            "coverage": "7/7 seminativi, olivo da olio e prati/pascoli; 6/7 vite; 4/7 olive da tavola (eccezione approvata)",',
        "coverage colture",
    )
    text = replace_once(
        text,
        '"normalized": {"value": item(t)["irrigatedAreaHa"] / item(t)["sauCenterHa"] * 100, "year": 2020}',
        '"normalized": {"label": "Quota di SAU irrigata", "value": item(t)["irrigatedAreaHa"] / item(t)["sauCenterHa"] * 100, "unit": "percent", "year": 2020}',
        "label/unit irrigazione",
    )
    write(rel, text)


def patch_app_parts() -> None:
    rel = "assets/app-parts/01.txt"
    text = read(rel)
    text = replace_once(
        text,
        '      const href = route(`comuni/${row.slug}/?${query}`);',
        '      const rowSlug = row.slug || normalize(row.town).replaceAll(\' \', \'-\');\n      const href = route(`comuni/${rowSlug}/?${query}`);',
        "fallback slug barRows",
    )
    text = text.replace('row.slug === selectedTown', 'rowSlug === selectedTown')
    write(rel, text)

    rel = "assets/app-parts/03.txt"
    text = read(rel)
    text = replace_once(
        text,
        "    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = metric.aggregate?.parts?.[index] || {};\n      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}`, note:metric.aggregate?.note };\n    }",
        "    if (metric.meta.compositeType === 'agricultureProfile') {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = metric.aggregate?.parts?.[index] || {};\n      const values = metric.rows.map(row => row.parts?.[index]?.value).filter(value => value !== null && value !== undefined && Number.isFinite(Number(value))).map(Number);\n      return { value:values.length ? values.reduce((sum,value)=>sum+value,0)/values.length : null, unit:part.unit || metric.meta.unit, label:`Media comuni Versilia · ${part.label || metric.meta.label}`, note:`Media semplice dei ${values.length} comuni con dato disponibile.` };\n    }\n    if (metric.meta.compositeType === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = metric.aggregate?.parts?.[index] || {};\n      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}`, note:metric.aggregate?.note };\n    }",
        "media agricultureProfile",
    )
    text = replace_once(
        text,
        '    const definitionControls = metric.meta.detailGroup === \'tpl\' ? \'\' : controls;\n    const chartScaleControls = metric.meta.detailGroup === \'tpl\' ? controls : \'\';',
        "    const definitionControls = '';\n    const chartScaleControls = controls;",
        "switch vicino al grafico",
    )
    text = text.replace(
        "`<div class=\"topic-bars\">${chartScaleControls ? `<div class=\"tpl-chart-toolbar\">${chartScaleControls}</div>` : ''}<div class=\"comparison-bars\">${barRows(data,metricKey,{normalized})}</div></div>`",
        "`<div class=\"topic-bars\">${chartScaleControls ? `<div class=\"compare-chart-toolbar scale-toolbar\">${chartScaleControls}</div>` : ''}<div class=\"comparison-bars\">${barRows(data,metricKey,{normalized})}</div></div>`",
    )
    text = replace_once(
        text,
        '      const href=route(`comuni/${row.slug}/?${query}`);',
        '      const rowSlug=row.slug || normalize(row.town).replaceAll(\' \',\'-\');\n      const href=route(`comuni/${rowSlug}/?${query}`);',
        "fallback slug composite",
    )
    write(rel, text)


def patch_visual_grammar() -> None:
    rel = "assets/visual-grammar.js"
    text = read(rel)
    text = replace_once(
        text,
        "    if (token === 'eurperresident' || token === '€/ab' || token === '€/ab.') return 'eurperresident';\n    return token;",
        "    if (token === 'eurperresident' || token === '€/ab' || token === '€/ab.') return 'eurperresident';\n    if (token === 'hectares' || token === 'ha') return 'hectares';\n    if (token === 'hectaresperfarm' || token === 'ha/azienda') return 'hectares-per-farm';\n    return token;",
        "unità ettari visual grammar",
    )
    text = replace_once(
        text,
        "  function aggregateFor(metric, normalized) {\n    return normalized && metric.normalizedAggregate ? metric.normalizedAggregate : metric.aggregate;\n  }",
        "  function aggregateFor(metric, normalized) {\n    const values = (metric?.rows || []).map(row => valueFor(row, metric, normalized)).map(finite).filter(value => value !== null);\n    if (!values.length) return normalized && metric.normalizedAggregate ? metric.normalizedAggregate : metric.aggregate;\n    const value = values.reduce((sum,item) => sum + item, 0) / values.length;\n    return { value, label:`Media semplice dei ${values.length} comuni`, note:'Ogni comune con dato disponibile pesa allo stesso modo.' };\n  }",
        "riferimento media semplice",
    )
    text = replace_once(
        text,
        "    if (kind === 'eurm2') return `${formatted} €/m²`;\n    if (kind === 'rentm2') return `${formatted} €/m²/mese`;",
        "    if (kind === 'eurm2') return `${formatted} €/m²`;\n    if (kind === 'rentm2') return `${formatted} €/m²/mese`;\n    if (kind === 'hectares') return `${formatted} ha`;\n    if (kind === 'hectares-per-farm') return `${formatted} ha/azienda`;",
        "format ettari visual grammar",
    )
    old_pop = """    const key = metricKey || metric?.meta?.key || '';
    if (key === 'population') {
      if (aggregate <= 0) {
        return { headline: 'n.d.', direction: 'quota non disponibile', compact: 'quota non disponibile', overline: 'Quota sulla Versilia' };
      }
      const share = local / aggregate * 100;
      const formattedShare = number1.format(share);
      return {
        headline: `${formattedShare}%`,
        direction: 'della popolazione versiliese',
        compact: `${formattedShare}% della popolazione versiliese`,
        overline: 'Quota sulla Versilia',
        note: 'Quota dei residenti del comune sul totale della popolazione dei sette comuni.',
      };
    }

"""
    if old_pop in text:
        text = text.replace(old_pop, "    const key = metricKey || metric?.meta?.key || '';\n\n", 1)
    text = replace_once(
        text,
        "    const aggregate = finite(distribution && metric?.aggregate?.summaryValue !== undefined ? metric.aggregate.summaryValue : metric?.aggregate?.value);",
        "    const meanReference = aggregateFor(metric, false);\n    const aggregate = finite(distribution ? (metric?.rows || []).map(item => finite(item?.summaryValue)).filter(value => value !== null).reduce((sum,value,_,arr) => sum + value / arr.length, 0) : meanReference?.value);",
        "delta vs media",
    )
    text = text.replace("direction: diff > 0 ? 'sopra la Versilia' : 'sotto la Versilia'", "direction: diff > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia'")
    text = text.replace("compact: `${sign}${abs} p.p. vs Versilia`", "compact: `${sign}${abs} p.p. vs media Versilia`")
    text = text.replace("direction: diff === 0 ? 'in linea' : diff > 0 ? 'sopra la Versilia' : 'sotto la Versilia'", "direction: diff === 0 ? 'in linea' : diff > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia'")
    text = text.replace("direction: relative > 0 ? 'sopra la Versilia' : 'sotto la Versilia'", "direction: relative > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia'")
    text = text.replace("compact: `${sign}${abs}% vs Versilia`", "compact: `${sign}${abs}% vs media Versilia`")
    text = text.replace("'in linea con Versilia'", "'in linea con la media Versilia'")
    text = replace_once(
        text,
        "    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown'].includes(type)) return null;",
        "    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile'].includes(type)) return null;",
        "selection agriculture profile",
    )
    text = replace_once(
        text,
        "    if (type === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = row?.parts?.[index] || {};\n      return { value: part.value, unit: part.unit || metric?.meta?.unit || '' };\n    }",
        "    if (type === 'securityMeasures' || type === 'agricultureProfile') {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = row?.parts?.[index] || {};\n      return { value: part.value, unit: part.unit || metric?.meta?.unit || '' };\n    }",
        "selection part agriculture",
    )
    text = replace_once(
        text,
        "    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown'].includes(type)) return null;",
        "    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile'].includes(type)) return null;",
        "aggregate agriculture profile",
    )
    text = replace_once(
        text,
        "    if (type === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = metric.aggregate?.parts?.[index] || {};\n      return { value: part.value, label:`Versilia · ${part.label || metric.meta.label}`, unit:part.unit || metric?.meta?.unit || '' };\n    }",
        "    if (type === 'agricultureProfile') {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = metric.aggregate?.parts?.[index] || {};\n      const values = (metric.rows || []).map(row => finite(row?.parts?.[index]?.value)).filter(value => value !== null);\n      return { value: values.length ? values.reduce((sum,value) => sum + value,0) / values.length : null, label:`Media semplice dei ${values.length} comuni · ${part.label || metric.meta.label}`, unit:part.unit || metric?.meta?.unit || '' };\n    }\n    if (type === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);\n      const part = metric.aggregate?.parts?.[index] || {};\n      return { value: part.value, label:`Versilia · ${part.label || metric.meta.label}`, unit:part.unit || metric?.meta?.unit || '' };\n    }",
        "aggregate mean agriculture",
    )
    text = text.replace("const overlineText = delta.overline || 'Rispetto alla Versilia';", "const overlineText = delta.overline || 'Rispetto alla media Versilia';")
    text = text.replace("'Il confronto con la Versilia descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.'", "'Il confronto con la media dei Comuni della Versilia descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.'")
    write(rel, text)


def patch_css() -> None:
    rel = "assets/chart-surfaces.css"
    text = read(rel)
    addition = """

/* v1.20 review — i controlli di scala appartengono al grafico, non alla definizione laterale. */
#compare-bars .compare-chart-toolbar.scale-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  min-width: 0;
  margin: 0 0 18px;
}
#compare-bars .compare-chart-toolbar.scale-toolbar .scale-switch {
  width: min(100%, 430px);
  margin: 0;
}
@media (max-width: 1000px) {
  #compare-bars .compare-chart-toolbar.scale-toolbar { justify-content: stretch; }
  #compare-bars .compare-chart-toolbar.scale-toolbar .scale-switch { width: 100%; }
}
"""
    if "v1.20 review — i controlli di scala" not in text:
        text += addition
    write(rel, text)


def patch_tests() -> None:
    rel = "scripts/test_agricoltura_territorio_v120.py"
    text = read(rel)
    text = replace_once(
        text,
        'assert {p["key"] for p in crop_rows["046005"]["parts"]} == {"ARLAND", "OLIVOOILTR", "VINEY", "PGRAPM"}',
        'assert {p["key"] for p in crop_rows["046005"]["parts"]} == {"ARLAND", "OLIVOOILTR", "OLIVTTR", "VINEY", "PGRAPM"}',
        "test crop keys",
    )
    text = replace_once(
        text,
        'assert set(agg_parts) == {"ARLAND", "OLIVOOILTR", "VINEY", "PGRAPM"}\nassert agg_parts["VINEY"]["value"] is None and agg_parts["VINEY"]["coverage"] == "6/7"',
        'assert set(agg_parts) == {"ARLAND", "OLIVOOILTR", "OLIVTTR", "VINEY", "PGRAPM"}\nassert math.isclose(agg_parts["VINEY"]["value"], sum(part(code, "VINEY")["value"] for code in crop_rows if part(code, "VINEY")["value"] is not None), rel_tol=1e-12)\nassert agg_parts["VINEY"]["coverage"] == "6/7"\nassert math.isclose(agg_parts["OLIVTTR"]["value"], 1.63, rel_tol=1e-12) and agg_parts["OLIVTTR"]["coverage"] == "4/7"\nassert part("046013", "OLIVTTR")["value"] is None\nassert part("046030", "OLIVTTR")["value"] is None\nassert part("046033", "OLIVTTR")["value"] is None',
        "test crop aggregate",
    )
    text = text.replace('assert all(int(p["coverage"].split("/")[0]) >= 6 for p in agg_parts.values())', 'assert all(int(p["coverage"].split("/")[0]) >= 6 for key,p in agg_parts.items() if key != "OLIVTTR")')
    insert_after = 'assert "centro aziendale" in irr["method"]["caveat"]\n'
    extra = '''\nfor key in KEYS:\n    assert all(row.get("slug") for row in site["metrics"][key]["rows"]), key\nfor metric_key in ("agriculturalUsedArea", "irrigatedAgriculturalArea"):\n    for row in site["metrics"][metric_key]["rows"]:\n        assert row["normalized"]["unit"] == "percent"\n        assert row["normalized"]["label"]\n\n'''
    if extra not in text:
        text = text.replace(insert_after, insert_after + extra, 1)
    text = replace_once(
        text,
        'assert "a.displayValue===null||a.displayValue===undefined" in app03',
        'assert "a.displayValue===null||a.displayValue===undefined" in app03\nassert "const definitionControls = \'\';" in app03\nassert "compare-chart-toolbar scale-toolbar" in app03\nassert "Media comuni Versilia" in app03\nvisual = (ROOT / "assets/visual-grammar.js").read_text(encoding="utf-8")\nassert "agricultureProfile" in visual\nassert "Media semplice dei ${values.length} comuni" in visual\nassert "hectares-per-farm" in visual',
        "test UX review",
    )
    text = text.replace(
        'print("Agricoltura e territorio v1.20.0 verificata: 5 indicatori; tutte le sottodimensioni pubblicate hanno copertura almeno 6/7.")',
        'print("Agricoltura e territorio v1.20.0 verificata: 5 indicatori; media Versilia nei confronti; Vite 6/7 e olive da tavola 4/7 come eccezione approvata.")',
    )
    write(rel, text)


def main() -> None:
    patch_snapshot()
    patch_materializer()
    patch_app_parts()
    patch_visual_grammar()
    patch_css()
    patch_tests()
    print("Correzioni di collaudo Agricoltura v1.20 applicate.")


if __name__ == "__main__":
    main()
