#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def save(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Pattern non trovato: {label}")
    return text.replace(old, new, 1)


def patch_snapshot() -> None:
    p = ROOT / "data/source-snapshots/istat-agricoltura-territorio-2020.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    q = d["sources"]["localizedCrops"]["query"]
    if "OLIVTTR" not in q:
        d["sources"]["localizedCrops"]["query"] = q.replace(
            "ARU.ALL+ARLAND+OLIVOOILTR+VINEY+PGRAPM.TOT",
            "ARU.ALL+ARLAND+OLIVOOILTR+OLIVTTR+VINEY+PGRAPM.TOT",
        )
    d["definitions"]["OLIVTTR"] = "Olivo per produzione di olive da tavola"
    d.setdefault("coveragePolicy", {}).setdefault("exceptions", {})["OLIVTTR"] = (
        "Olive da tavola: pubblicazione approvata con copertura 4/7; riga assente = n.d., non zero."
    )
    vals = {
        "046005": 0.30, "046013": None, "046018": 0.23, "046024": 0.10,
        "046028": 1.00, "046030": None, "046033": None,
    }
    for code, value in vals.items():
        d["towns"][code].setdefault("cropsHa", {})["OLIVTTR"] = value
    d.setdefault("derivations", {})["comparisonReference"] = (
        "Nei confronti grafici e nelle schede comunali il riferimento Versilia è la media semplice "
        "dei valori comunali disponibili. I totali territoriali restano distinti e sono usati solo quando esplicitamente indicati."
    )
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_materializer() -> None:
    rel = "scripts/materialize_agricoltura_territorio_v120.py"
    t = load(rel)
    t = must_replace(
        t,
        '    ("OLIVOOILTR", "Olivo da olio"),\n    ("VINEY", "Vite"),',
        '    ("OLIVOOILTR", "Olivo da olio"),\n    ("OLIVTTR", "Olive da tavola"),\n    ("VINEY", "Vite"),',
        "CROP_PARTS OLIVTTR",
    )
    t = must_replace(t, "        minimum = 6\n        if present < minimum:", "        minimum = 4 if crop == \"OLIVTTR\" else 6\n        if present < minimum:", "coverage OLIVTTR")
    t = must_replace(
        t,
        '    towns = site["towns"]\n\n    def item(town: dict) -> dict:',
        '    towns = site["towns"]\n    slug_by_code = {row["code"]: row["slug"] for row in site["metrics"]["population"]["rows"]}\n\n    def item(town: dict) -> dict:',
        "slug map",
    )
    if '"slug": slug_by_code[t["code"]]' not in t:
        t = t.replace('"town": t["name"], "code": t["code"],', '"town": t["name"], "code": t["code"], "slug": slug_by_code[t["code"]],')
    t = must_replace(
        t,
        '"normalized": {"value": share, "year": 2020},',
        '"normalized": {"label": "Quota della superficie comunale occupata da SAU", "value": share, "unit": "percent", "year": 2020},',
        "normalized SAU",
    )
    t = must_replace(
        t,
        '"normalized": {"value": item(t)["irrigatedAreaHa"] / item(t)["sauCenterHa"] * 100, "year": 2020}',
        '"normalized": {"label": "Quota di SAU irrigata", "value": item(t)["irrigatedAreaHa"] / item(t)["sauCenterHa"] * 100, "unit": "percent", "year": 2020}',
        "normalized irrigation",
    )
    t = must_replace(t, '"value": sum(present) if len(present) == 7 else None,', '"value": sum(present) if present else None,', "crop aggregate available")
    t = t.replace(
        '"note": "Per categorie con copertura incompleta il totale Versilia resta n.d.; la somma dei soli Comuni disponibili è conservata come dato tecnico nello snapshot/materializzazione.",',
        '"note": "Il totale di ciascuna coltura è la somma dei Comuni con dato disponibile; la copertura è dichiarata e i Comuni senza riga restano n.d.",',
    )
    t = t.replace('ARLAND, OLIVOOILTR, VINEY, PGRAPM.', 'ARLAND, OLIVOOILTR, OLIVTTR, VINEY, PGRAPM.')
    t = t.replace(
        '"caveat": "Una riga assente non è interpretata come zero. Vite: 6/7 (Forte dei Marmi n.d.). Non sono pubblicate sottodimensioni con copertura inferiore a 6/7.",',
        '"caveat": "Una riga assente non è interpretata come zero. Vite: 6/7 (Forte dei Marmi n.d.). Olive da tavola: eccezione approvata 4/7; Forte dei Marmi, Stazzema e Viareggio restano n.d.",',
    )
    t = t.replace(
        '"coverage": "7/7 seminativi, olivo da olio e prati/pascoli; 6/7 vite",',
        '"coverage": "7/7 seminativi, olivo da olio e prati/pascoli; 6/7 vite; 4/7 olive da tavola (eccezione approvata)",',
    )
    save(rel, t)


def patch_links_and_controls() -> None:
    rel = "assets/app-parts/01.txt"
    t = load(rel)
    t = must_replace(
        t,
        '      const href = route(`comuni/${row.slug}/?${query}`);',
        "      const rowSlug = row.slug || normalize(row.town).replaceAll(' ', '-');\n      const href = route(`comuni/${rowSlug}/?${query}`);",
        "regular href slug",
    )
    t = t.replace("row.slug === selectedTown", "rowSlug === selectedTown")
    save(rel, t)

    rel = "assets/app-parts/03.txt"
    t = load(rel)
    old = """    if (['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)) {
      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);
      const part = metric.aggregate?.parts?.[index] || {};
      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}`, note:metric.aggregate?.note };
    }"""
    new = """    if (metric.meta.compositeType === 'agricultureProfile') {
      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);
      const part = metric.aggregate?.parts?.[index] || {};
      const values = metric.rows.map(row => row.parts?.[index]?.value).filter(value => value !== null && value !== undefined && Number.isFinite(Number(value))).map(Number);
      return { value:values.length ? values.reduce((sum,value)=>sum+value,0)/values.length : null, unit:part.unit || metric.meta.unit, label:`Media comuni Versilia · ${part.label || metric.meta.label}`, note:`Media semplice dei ${values.length} comuni con dato disponibile.` };
    }
    if (metric.meta.compositeType === 'securityMeasures') {
      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);
      const part = metric.aggregate?.parts?.[index] || {};
      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}`, note:metric.aggregate?.note };
    }"""
    t = must_replace(t, old, new, "agriculture aggregate mean")
    t = must_replace(
        t,
        "    const definitionControls = metric.meta.detailGroup === 'tpl' ? '' : controls;\n    const chartScaleControls = metric.meta.detailGroup === 'tpl' ? controls : '';",
        "    const definitionControls = '';\n    const chartScaleControls = controls;",
        "controls beside chart",
    )
    t = t.replace(
        '`<div class="topic-bars">${chartScaleControls ? `<div class="tpl-chart-toolbar">${chartScaleControls}</div>` : \'\'}<div class="comparison-bars">${barRows(data,metricKey,{normalized})}</div></div>`',
        '`<div class="topic-bars">${chartScaleControls ? `<div class="compare-chart-toolbar scale-toolbar">${chartScaleControls}</div>` : \'\'}<div class="comparison-bars">${barRows(data,metricKey,{normalized})}</div></div>`',
    )
    t = must_replace(
        t,
        '      const href=route(`comuni/${row.slug}/?${query}`);',
        "      const rowSlug=row.slug || normalize(row.town).replaceAll(' ','-');\n      const href=route(`comuni/${rowSlug}/?${query}`);",
        "composite href slug",
    )
    save(rel, t)


def patch_visual_grammar() -> None:
    rel = "assets/visual-grammar.js"
    t = load(rel)
    t = must_replace(
        t,
        "    if (token === 'eurperresident' || token === '€/ab' || token === '€/ab.') return 'eurperresident';\n    return token;",
        "    if (token === 'eurperresident' || token === '€/ab' || token === '€/ab.') return 'eurperresident';\n    if (token === 'hectares' || token === 'ha') return 'hectares';\n    if (token === 'hectaresperfarm' || token === 'ha/azienda') return 'hectares-per-farm';\n    return token;",
        "hectare unit token",
    )
    t = must_replace(
        t,
        "  function aggregateFor(metric, normalized) {\n    return normalized && metric.normalizedAggregate ? metric.normalizedAggregate : metric.aggregate;\n  }",
        "  function aggregateFor(metric, normalized) {\n    const values = (metric?.rows || []).map(row => valueFor(row, metric, normalized)).map(finite).filter(value => value !== null);\n    if (!values.length) return normalized && metric.normalizedAggregate ? metric.normalizedAggregate : metric.aggregate;\n    const value = values.reduce((sum,item) => sum + item, 0) / values.length;\n    return { value, label:`Media semplice dei ${values.length} comuni`, note:'Ogni comune con dato disponibile pesa allo stesso modo.' };\n  }",
        "mean aggregate reference",
    )
    t = must_replace(
        t,
        "    if (kind === 'eurm2') return `${formatted} €/m²`;\n    if (kind === 'rentm2') return `${formatted} €/m²/mese`;",
        "    if (kind === 'eurm2') return `${formatted} €/m²`;\n    if (kind === 'rentm2') return `${formatted} €/m²/mese`;\n    if (kind === 'hectares') return `${formatted} ha`;\n    if (kind === 'hectares-per-farm') return `${formatted} ha/azienda`;",
        "hectare formatting",
    )
    # Elimina la vecchia eccezione popolazione basata sulla quota del totale Versilia.
    t = re.sub(
        r"\n\s*if \(key === 'population'\) \{.*?\n\s*\}\n(?=\s*if \(isPercentageLike)",
        "\n",
        t,
        count=1,
        flags=re.S,
    )
    old_delta = "    const aggregate = finite(distribution && metric?.aggregate?.summaryValue !== undefined ? metric.aggregate.summaryValue : metric?.aggregate?.value);"
    new_delta = "    const meanReference = aggregateFor(metric, false);\n    const summaryValues = distribution ? (metric?.rows || []).map(item => finite(item?.summaryValue)).filter(value => value !== null) : [];\n    const aggregate = finite(distribution ? (summaryValues.length ? summaryValues.reduce((sum,value)=>sum+value,0)/summaryValues.length : null) : meanReference?.value);"
    t = must_replace(t, old_delta, new_delta, "town delta mean")
    t = t.replace("sopra la Versilia", "sopra la media Versilia").replace("sotto la Versilia", "sotto la media Versilia")
    t = t.replace("vs Versilia", "vs media Versilia").replace("in linea con Versilia", "in linea con la media Versilia")
    t = t.replace("const overlineText = delta.overline || 'Rispetto alla Versilia';", "const overlineText = delta.overline || 'Rispetto alla media Versilia';")
    t = t.replace(
        "'Il confronto con la Versilia descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.'",
        "'Il confronto con la media dei Comuni della Versilia descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.'",
    )
    t = t.replace(
        "if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown'].includes(type)) return null;",
        "if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile'].includes(type)) return null;",
    )
    # Selezione del valore della coltura, non della SAU totale della riga.
    old_sec_sel = """    if (type === 'securityMeasures') {
      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);
      const part = row?.parts?.[index] || {};
      return { value: part.value, unit: part.unit || metric?.meta?.unit || '' };
    }"""
    new_sec_sel = """    if (type === 'securityMeasures' || type === 'agricultureProfile') {
      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);
      const part = row?.parts?.[index] || {};
      return { value: part.value, unit: part.unit || metric?.meta?.unit || '' };
    }"""
    t = must_replace(t, old_sec_sel, new_sec_sel, "crop selected value")
    old_sec_agg = """    if (type === 'securityMeasures') {
      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);
      const part = metric.aggregate?.parts?.[index] || {};
      return { value: part.value, label:`Versilia · ${part.label || metric.meta.label}`, unit:part.unit || metric?.meta?.unit || '' };
    }"""
    new_sec_agg = """    if (type === 'agricultureProfile') {
      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);
      const part = metric.aggregate?.parts?.[index] || {};
      const values = (metric.rows || []).map(row => finite(row?.parts?.[index]?.value)).filter(value => value !== null);
      return { value: values.length ? values.reduce((sum,value)=>sum+value,0)/values.length : null, label:`Media semplice dei ${values.length} comuni · ${part.label || metric.meta.label}`, unit:part.unit || metric?.meta?.unit || '' };
    }
    if (type === 'securityMeasures') {
      const index = Math.max(0, Number(String(choice).replace('part-','')) || 0);
      const part = metric.aggregate?.parts?.[index] || {};
      return { value: part.value, label:`Versilia · ${part.label || metric.meta.label}`, unit:part.unit || metric?.meta?.unit || '' };
    }"""
    t = must_replace(t, old_sec_agg, new_sec_agg, "crop selected mean")
    save(rel, t)


def patch_css() -> None:
    rel = "assets/chart-surfaces.css"
    t = load(rel)
    marker = "/* v1.20 review: switch di scala accanto al grafico */"
    if marker not in t:
        t += f'''\n\n{marker}\n#compare-bars .compare-chart-toolbar.scale-toolbar {{\n  display:flex;\n  justify-content:flex-end;\n  align-items:center;\n  min-width:0;\n  margin:0 0 18px;\n}}\n#compare-bars .compare-chart-toolbar.scale-toolbar .scale-switch {{\n  width:min(100%,430px);\n  margin:0;\n}}\n@media (max-width:1000px) {{\n  #compare-bars .compare-chart-toolbar.scale-toolbar {{ justify-content:stretch; }}\n  #compare-bars .compare-chart-toolbar.scale-toolbar .scale-switch {{ width:100%; }}\n}}\n'''
    save(rel, t)


def patch_tests() -> None:
    rel = "scripts/test_agricoltura_territorio_v120.py"
    t = load(rel)
    t = t.replace(
        'assert {p["key"] for p in crop_rows["046005"]["parts"]} == {"ARLAND", "OLIVOOILTR", "VINEY", "PGRAPM"}',
        'assert {p["key"] for p in crop_rows["046005"]["parts"]} == {"ARLAND", "OLIVOOILTR", "OLIVTTR", "VINEY", "PGRAPM"}',
    )
    t = t.replace(
        'assert set(agg_parts) == {"ARLAND", "OLIVOOILTR", "VINEY", "PGRAPM"}\nassert agg_parts["VINEY"]["value"] is None and agg_parts["VINEY"]["coverage"] == "6/7"',
        'assert set(agg_parts) == {"ARLAND", "OLIVOOILTR", "OLIVTTR", "VINEY", "PGRAPM"}\nassert math.isclose(agg_parts["VINEY"]["value"], sum(part(code, "VINEY")["value"] for code in crop_rows if part(code, "VINEY")["value"] is not None), rel_tol=1e-12)\nassert agg_parts["VINEY"]["coverage"] == "6/7"\nassert math.isclose(agg_parts["OLIVTTR"]["value"], 1.63, rel_tol=1e-12) and agg_parts["OLIVTTR"]["coverage"] == "4/7"\nassert part("046013", "OLIVTTR")["value"] is None\nassert part("046030", "OLIVTTR")["value"] is None\nassert part("046033", "OLIVTTR")["value"] is None',
    )
    t = t.replace(
        'assert all(int(p["coverage"].split("/")[0]) >= 6 for p in agg_parts.values())',
        'assert all(int(p["coverage"].split("/")[0]) >= 6 for key,p in agg_parts.items() if key != "OLIVTTR")',
    )
    anchor = 'assert "centro aziendale" in irr["method"]["caveat"]\n'
    extra = '''\nfor key in KEYS:\n    assert all(row.get("slug") for row in site["metrics"][key]["rows"]), key\nfor metric_key in ("agriculturalUsedArea", "irrigatedAgriculturalArea"):\n    for row in site["metrics"][metric_key]["rows"]:\n        assert row["normalized"]["unit"] == "percent"\n        assert row["normalized"]["label"]\n\n'''
    if extra not in t:
        if anchor not in t:
            raise RuntimeError("Anchor test normalized non trovato")
        t = t.replace(anchor, anchor + extra, 1)
    if 'assert "compare-chart-toolbar scale-toolbar" in app03' not in t:
        anchor2 = 'assert "a.displayValue===null||a.displayValue===undefined" in app03\n'
        extra2 = '''assert "compare-chart-toolbar scale-toolbar" in app03\nassert "Media comuni Versilia" in app03\nvisual = (ROOT / "assets/visual-grammar.js").read_text(encoding="utf-8")\nassert "agricultureProfile" in visual\nassert "Media semplice dei ${values.length} comuni" in visual\nassert "hectares-per-farm" in visual\n'''
        if anchor2 not in t:
            raise RuntimeError("Anchor test UX non trovato")
        t = t.replace(anchor2, anchor2 + extra2, 1)
    t = t.replace(
        'print("Agricoltura e territorio v1.20.0 verificata: 5 indicatori; tutte le sottodimensioni pubblicate hanno copertura almeno 6/7.")',
        'print("Agricoltura e territorio v1.20.0 verificata: media Versilia nei confronti; Vite 6/7 e olive da tavola 4/7 come eccezione approvata.")',
    )
    save(rel, t)


def main() -> None:
    patch_snapshot()
    patch_materializer()
    patch_links_and_controls()
    patch_visual_grammar()
    patch_css()
    patch_tests()
    print("Correzioni feedback collaudo Agricoltura v1.20 applicate.")


if __name__ == "__main__":
    main()
