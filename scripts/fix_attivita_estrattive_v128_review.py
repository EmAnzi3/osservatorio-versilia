#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT / "scripts/materialize_attivita_estrattive_v128.py"
SITE = ROOT / "data/site-data.json"
APP03 = ROOT / "assets/app-parts/03.txt"
APP = ROOT / "assets/app.js"
UX = ROOT / "assets/ux-history.js"
UX_CORE = ROOT / "assets/ux-history-core.js"
VG = ROOT / "assets/visual-grammar.js"
CSS = ROOT / "assets/indicator-pages.css"
DATA_TEST = ROOT / "scripts/test_attivita_estrattive_v128.py"
BROWSER_TEST = ROOT / "scripts/test_attivita_estrattive_v128_browser.py"

YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
SERAVEZZA = [31151, 46093, 52048, 57199, 53518, 53194, 55801]
STAZZEMA = [19894, 13619, 17804, 31658, 25328, 38372, 23651]
AGG_VALUES = [a + b for a, b in zip(SERAVEZZA, STAZZEMA)]
assert AGG_VALUES == [51045, 59712, 69852, 88857, 78846, 91566, 79452]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        if new in text:
            return text
        raise RuntimeError(f"{label}: token non trovato")
    return text.replace(old, new, 1)


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


# 1) Materializzatore: aggregato produzione = somma dei valori comunali effettivamente pubblicati (2/7),
#    senza trasformare gli altri cinque n.d. in zero.
mat = MAT.read_text(encoding="utf-8")
mat = replace_once(
    mat,
    """def build_production_metric(site):
    slugs=slug_map(site); town_by_code={t['code']:t for t in site['towns']}; rows=[]
""",
    """def build_production_metric(site):
    slugs=slug_map(site); town_by_code={t['code']:t for t in site['towns']}; rows=[]
    aggregate_years=list(next(iter(PRODUCTION.values()))['years'])
    aggregate_values=[sum(PRODUCTION[code]['values'][i] for code in PRODUCTION) for i in range(len(aggregate_years))]
""",
    "materializzatore aggregate years",
)
mat = replace_once(
    mat,
    """            'sourceMeta':{'snapshot':'data/source-snapshots/attivita-estrattive-v128.json','note':'Serie 2019–2025 verificata per Seravezza e Stazzema. Nessun totale Versilia pubblicato.'}
""",
    """            'sourceMeta':{'snapshot':'data/source-snapshots/attivita-estrattive-v128.json','note':'Serie 2019–2025 verificata per Seravezza e Stazzema. L’aggregato è la somma aritmetica dei soli valori comunali pubblicati (copertura 2/7); gli altri cinque Comuni restano n.d.'},
            'comparisonReference':'aggregate','comparisonDifference':'shareOfAggregate','comparisonLabel':'somma pubblicata','comparisonOverline':'Peso sulla produzione rilevata','comparisonNote':'Quota del Comune sulla somma dei valori comunali effettivamente pubblicati. Copertura 2/7: i cinque Comuni senza dato restano n.d. e non vengono trattati come zero.'
""",
    "materializzatore production meta",
)
mat = replace_once(
    mat,
    """        'aggregate':{'value':None,'label':'Versilia · totale non pubblicato','note':'Il monitoraggio PRC non consente di dimostrare una produzione comunale omogenea per tutti i sette Comuni; la somma di Seravezza e Stazzema non viene presentata come totale Versilia.'},
""",
    """        'aggregate':{'value':aggregate_values[-1],'label':'Versilia · somma valori comunali disponibili (2/7)','series':{'years':aggregate_years,'values':aggregate_values},'coverage':'2/7','note':'Somma aritmetica dei valori pubblicati per Seravezza e Stazzema. I cinque Comuni senza dato restano n.d.: 79.452 m³ non implica produzione zero negli altri territori.'},
""",
    "materializzatore production aggregate",
)
mat = replace_once(
    mat,
    """            'formula':'Seravezza: comprensorio 8. Stazzema: somma dei comprensori 9 Bacino di Stazzema + 92 Cardoso delle Apuane, entrambi attribuiti dal PRC al Comune. I componenti elementari sono conservati nello snapshot.',
""",
    """            'formula':'Seravezza: comprensorio 8. Stazzema: somma dei comprensori 9 Bacino di Stazzema + 92 Cardoso delle Apuane, entrambi attribuiti dal PRC al Comune. Aggregato visualizzato: somma aritmetica dei soli Comuni con dato pubblicato (2/7). I componenti elementari sono conservati nello snapshot.',
""",
    "materializzatore production formula",
)
mat = mat.replace("'unit':'percent','value':info['g'][2]", "'unit':'%','value':info['g'][2]")
mat = mat.replace("'unit':'percent','value':info['gp'][2]", "'unit':'%','value':info['gp'][2]")
mat = mat.replace("'unit':'percent','value':info['acc'][2]", "'unit':'%','value':info['acc'][2]")
mat = replace_once(
    mat,
    """            'compositeType':'securityMeasures','selectorLabel':'Lettura','comparisonReference':'aggregate','comparisonDifference':'shareOfAggregate','comparisonLabel':'Versilia','comparisonOverline':'Peso sulla Versilia','comparisonNote':'Per la superficie il confronto usa l’intersezione geometrica col confine comunale; per il numero usa l’attribuzione comunale ufficiale PRC.'
""",
    """            'compositeType':'securityMeasures','selectorLabel':'Lettura','comparisonReference':'aggregate','comparisonDifference':'shareOfAggregate','comparisonLabel':'Versilia','comparisonOverline':'Peso sulla Versilia','comparisonNote':'Per superfici e numeri il peso è calcolato sul totale della stessa categoria PRC. Per la % di territorio si confrontano direttamente quota comunale e quota territoriale Versilia, senza dividere una percentuale per l’altra.'
""",
    "materializzatore planning note",
)
write(MAT, mat)

# 2) Dataset già materializzato sul branch.
site = json.loads(SITE.read_text(encoding="utf-8"))
prod = site["metrics"]["extractiveProduction"]
prod["meta"]["sourceMeta"]["note"] = (
    "Serie 2019–2025 verificata per Seravezza e Stazzema. "
    "L’aggregato è la somma aritmetica dei soli valori comunali pubblicati (copertura 2/7); "
    "gli altri cinque Comuni restano n.d."
)
prod["meta"].update({
    "comparisonReference": "aggregate",
    "comparisonDifference": "shareOfAggregate",
    "comparisonLabel": "somma pubblicata",
    "comparisonOverline": "Peso sulla produzione rilevata",
    "comparisonNote": (
        "Quota del Comune sulla somma dei valori comunali effettivamente pubblicati. "
        "Copertura 2/7: i cinque Comuni senza dato restano n.d. e non vengono trattati come zero."
    ),
})
prod["aggregate"] = {
    "value": AGG_VALUES[-1],
    "label": "Versilia · somma valori comunali disponibili (2/7)",
    "series": {"years": YEARS, "values": AGG_VALUES},
    "coverage": "2/7",
    "note": (
        "Somma aritmetica dei valori pubblicati per Seravezza e Stazzema. "
        "I cinque Comuni senza dato restano n.d.: 79.452 m³ non implica produzione zero negli altri territori."
    ),
}
prod["method"]["formula"] = (
    "Seravezza: comprensorio 8. Stazzema: somma dei comprensori 9 Bacino di Stazzema + "
    "92 Cardoso delle Apuane, entrambi attribuiti dal PRC al Comune. Aggregato visualizzato: "
    "somma aritmetica dei soli Comuni con dato pubblicato (2/7). I componenti elementari sono conservati nello snapshot."
)

planning = site["metrics"]["extractivePlanning"]
for row in planning["rows"]:
    for part in row.get("parts", []):
        if part.get("key", "").endswith("_pct"):
            part["unit"] = "%"
for part in planning["aggregate"].get("parts", []):
    if part.get("key", "").endswith("_pct"):
        part["unit"] = "%"
planning["meta"]["comparisonNote"] = (
    "Per superfici e numeri il peso è calcolato sul totale della stessa categoria PRC. "
    "Per la % di territorio si confrontano direttamente quota comunale e quota territoriale Versilia, "
    "senza dividere una percentuale per l’altra."
)
SITE.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 3) UI principale: inizializzazione coerente e niente rapporto fra percentuali PRC.
app3 = APP03.read_text(encoding="utf-8")
pattern = re.compile(
    r"  function updateExtractiveTownPosition\(metric,row,choice,position\) \{.*?\n  \}\n\n  function updateFiscalRecoveryTownPosition",
    re.S,
)
replacement = r"""  function updateExtractiveTownPosition(metric,row,choice,position) {
    if (!position || !['extractiveSites','extractivePlanning'].includes(metric?.meta?.key)) return;
    const options=compositeSelectionOptions(metric,row);
    const selected=options.find(option=>option.key===choice) || options[0];
    const agg=compositeSelectionAggregate(metric,choice);
    const selectedPart=selected?.index === undefined ? null : row.parts?.[selected.index];
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');

    if (metric.meta.key === 'extractivePlanning' && selectedPart?.key?.endsWith('_pct')) {
      if(overline) overline.textContent='Quota territoriale Versilia';
      if(deltaEl) deltaEl.innerHTML=`${html(agg.formatted)}<small>sul territorio complessivo dei sette Comuni</small>`;
      if(noteEl) noteEl.textContent='Confronto diretto tra due quote territoriali: la percentuale comunale non viene divisa per la percentuale Versilia.';
      if(aggLabel) aggLabel.textContent=`${row.town} · quota comunale`;
      if(aggValue) aggValue.textContent=selected.formatted;
      return;
    }

    const localRaw=selected?.value;
    const totalRaw=agg?.value;
    const local=localRaw === null || localRaw === undefined ? NaN : Number(localRaw);
    const total=totalRaw === null || totalRaw === undefined ? NaN : Number(totalRaw);
    const share=Number.isFinite(local) && Number.isFinite(total) && total > 0 ? local/total*100 : null;
    if(overline) overline.textContent=metric.meta.comparisonOverline || 'Peso sulla Versilia';
    if(deltaEl) deltaEl.innerHTML=share === null
      ? `n.d.<small>${total === 0 ? 'totale Versilia pari a zero' : 'quota non disponibile'}</small>`
      : `${html(number2.format(share))}%<small>del totale della lettura selezionata</small>`;
    if(noteEl) noteEl.textContent=metric.meta.comparisonNote || 'Quota del valore comunale sul totale dei sette Comuni per la lettura selezionata.';
    if(aggLabel) aggLabel.textContent=agg.label;
    if(aggValue) aggValue.textContent=agg.formatted;
  }

  function updateFiscalRecoveryTownPosition"""
app3, n = pattern.subn(replacement, app3, count=1)
if n != 1:
    raise RuntimeError(f"updateExtractiveTownPosition: sostituzioni={n}")
app3 = app3.replace(
    '<div class="indicator-table-scroll"><table class="indicator-values-table"><thead><tr><th>Codice RT</th>',
    '<div class="indicator-table-scroll extractive-records-scroll"><table class="indicator-values-table"><thead><tr><th>Codice RT</th>',
    1,
)
write(APP03, app3)

# 4) Visual grammar: non sovrascrivere il pannello dinamico RTCave/PRC;
#    per le card e per la produzione usare una quota sul totale, non una "media" generica.
vg = VG.read_text(encoding="utf-8")
vg = replace_once(
    vg,
    """    if (['maritimeConcessions','maritimeConcessionFeesDue'].includes(key) && metric?.meta?.comparisonDifference === 'shareOfAggregate') {
      const total = finite(metric?.aggregate?.value);
""",
    """    if (['maritimeConcessions','maritimeConcessionFeesDue','extractiveSites','extractiveProduction','extractivePlanning'].includes(key) && metric?.meta?.comparisonDifference === 'shareOfAggregate') {
      const total = finite(metric?.aggregate?.value);
""",
    "visual grammar share branch",
)
vg = replace_once(
    vg,
    """      const share = local / total * 100;
      const formattedShare = number1.format(share);
      return {
        headline: `${formattedShare}%`,
        direction: 'del totale dei quattro Comuni costieri',
        compact: `${formattedShare}% del totale costiero`,
        overline: metric?.meta?.comparisonOverline || 'Peso sulla Versilia costiera',
        note: metric?.meta?.comparisonNote || 'Quota del valore comunale sul totale dei quattro Comuni costieri.',
      };
""",
    """      const share = local / total * 100;
      const formattedShare = number1.format(share);
      const extractive = key.startsWith('extractive');
      const direction = key === 'extractiveProduction'
        ? 'della somma dei Comuni con dato'
        : key === 'extractiveSites'
          ? 'del totale dei record RTCave'
          : key === 'extractivePlanning'
            ? 'del totale della categoria PRC'
            : 'del totale dei quattro Comuni costieri';
      return {
        headline: `${formattedShare}%`,
        direction,
        compact: `${formattedShare}% ${direction}`,
        overline: metric?.meta?.comparisonOverline || (extractive ? 'Peso sulla Versilia' : 'Peso sulla Versilia costiera'),
        note: metric?.meta?.comparisonNote || (extractive ? 'Quota del valore comunale sul totale della lettura selezionata.' : 'Quota del valore comunale sul totale dei quattro Comuni costieri.'),
      };
""",
    "visual grammar share semantics",
)
vg = replace_once(
    vg,
    """    if (['maritimeConcessions','maritimeConcessionFeesDue'].includes(metricKey)) return;
""",
    """    if (['maritimeConcessions','maritimeConcessionFeesDue','extractiveSites','extractivePlanning'].includes(metricKey)) return;
""",
    "visual grammar town override exclusions",
)
vg = replace_once(
    vg,
    """    if (token === 'hectares' || token === 'ha') return 'hectares';
""",
    """    if (token === 'hectares' || token === 'ha') return 'hectares';
    if (token === 'cubicmetres' || token === 'm3' || token === 'm³') return 'cubic-metres';
""",
    "visual grammar cubic unit kind",
)
vg = replace_once(
    vg,
    """    if (kind === 'hectares') return `${formatted} ha`;
""",
    """    if (kind === 'hectares') return `${formatted} ha`;
    if (kind === 'cubic-metres') return `${formatted} m³`;
""",
    "visual grammar cubic format",
)
write(VG, vg)

# 5) Lo storico produzione non richiede 7/7: in scheda comunale preserva il grafico nativo;
#    nel confronto usa soltanto le due serie comunali ufficialmente disponibili.
ux = UX.read_text(encoding="utf-8")
ux = replace_once(
    ux,
    """    if (!selected) return;
    if (['drinkingWaterQuality','remediationProceedings'].includes(selected.metric?.meta?.compositeType)) return;
    const existingShell = target.querySelector(':scope > .ux-view-shell');
""",
    """    if (!selected) return;
    if (['drinkingWaterQuality','remediationProceedings'].includes(selected.metric?.meta?.compositeType)) return;
    const existingShell = target.querySelector(':scope > .ux-view-shell');
    if (selected.key === 'extractiveProduction') {
      if (existingShell) {
        wireShell(existingShell, 'ov-compare-view', selectedTown, true);
        return;
      }
      const rowsWithHistory=(selected.metric.rows || []).filter(row=>row.series?.years?.length >= 2);
      const historyView={...selected.metric, rows:rowsWithHistory};
      const series=toolkit.comparableSeries(historyView);
      const currentMarkup=target.innerHTML;
      const historyMarkup=renderHistoryMarkup(historyView,series,selectedTown);
      const note='Serie 2019–2025 per i due Comuni con raccordo PRC→Comune certo. Gli altri cinque Comuni restano n.d. e non vengono trasformati in zero.';
      target.innerHTML=toolkit.viewShellMarkup(currentMarkup,historyMarkup,Boolean(series),note);
      wireShell(target.querySelector('.ux-view-shell'),'ov-compare-view',selectedTown,true);
      return;
    }
""",
    "ux compare extractive production",
)
ux = replace_once(
    ux,
    """    const selected = selectedMetric(data);
    if (!selected) return;
    if (['drinkingWaterQuality','remediationProceedings'].includes(selected.metric?.meta?.compositeType)) return;
""",
    """    const selected = selectedMetric(data);
    if (!selected) return;
    if (selected.key === 'extractiveProduction') return;
    if (['drinkingWaterQuality','remediationProceedings'].includes(selected.metric?.meta?.compositeType)) return;
""",
    "ux town preserve production chart",
)
write(UX, ux)

core = UX_CORE.read_text(encoding="utf-8")
core = replace_once(
    core,
    """      case 'hectares': return `${formatNumber(number, 2)} ha`;
""",
    """      case 'hectares': return `${formatNumber(number, 2)} ha`;
      case 'cubicMetres': return `${formatNumber(number, 0)} m³`;
""",
    "ux core cubic metres",
)
write(UX_CORE, core)

# 6) Margini + scrolling verticale interno per l'anagrafica RTCave lunga.
css = CSS.read_text(encoding="utf-8")
marker = "/* Attività estrattive v1.28 · revisione draft */"
if marker not in css:
    css += r"""

/* Attività estrattive v1.28 · revisione draft */
.extractive-detail {
  overflow: hidden;
}
.extractive-detail > summary {
  padding-left: 24px;
  padding-right: 24px;
}
.extractive-detail > .composite-town-detail {
  margin: 0 24px 22px;
}
.extractive-detail > .indicator-table-scroll {
  width: calc(100% - 48px);
  margin: 0 24px 22px;
}
.extractive-detail > .aggregate-note {
  margin: 0 24px 24px;
  line-height: 1.55;
}
.extractive-records-scroll {
  max-height: 520px;
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
.extractive-records-scroll .indicator-values-table thead th {
  position: sticky;
  top: 0;
  z-index: 3;
}
@media (max-width: 700px) {
  .extractive-detail > summary {
    padding-left: 18px;
    padding-right: 18px;
  }
  .extractive-detail > .composite-town-detail,
  .extractive-detail > .indicator-table-scroll {
    width: calc(100% - 32px);
    margin-left: 16px;
    margin-right: 16px;
  }
  .extractive-detail > .aggregate-note {
    margin-left: 16px;
    margin-right: 16px;
  }
  .extractive-records-scroll {
    max-height: 420px;
  }
}
"""
write(CSS, css)

# 7) Regressioni dati aggiornate.
dt = DATA_TEST.read_text(encoding="utf-8")
dt = replace_once(
    dt,
    """    assert production["aggregate"]["value"] is None
    assert production["aggregate"]["label"] == "Versilia · totale non pubblicato"
    assert "non viene presentata come totale Versilia" in production["aggregate"]["note"]
""",
    """    assert production["aggregate"]["value"] == 79452
    assert production["aggregate"]["label"] == "Versilia · somma valori comunali disponibili (2/7)"
    assert production["aggregate"]["series"] == {"years": [2019, 2020, 2021, 2022, 2023, 2024, 2025], "values": [51045, 59712, 69852, 88857, 78846, 91566, 79452]}
    assert production["aggregate"]["coverage"] == "2/7"
    assert "non implica produzione zero" in production["aggregate"]["note"]
""",
    "data test production aggregate",
)
dt = replace_once(
    dt,
    """    assert plan_agg["acc_n"] == 19 and plan_agg["acc_ha"] == 556.495 and plan_agg["acc_pct"] == 1.559
""",
    """    assert plan_agg["acc_n"] == 19 and plan_agg["acc_ha"] == 556.495 and plan_agg["acc_pct"] == 1.559
    assert next(p for p in planning["aggregate"]["parts"] if p["key"] == "g_pct")["unit"] == "%"
""",
    "data test planning percent unit",
)
write(DATA_TEST, dt)

# 8) Smoke browser: stato iniziale corretto, storico visibile, % PRC ragionevole e tabella RTCave scrollabile.
bt = BROWSER_TEST.read_text(encoding="utf-8")
bt = replace_once(
    bt,
    """    text = detail.inner_text()
    assert "TOMBACCIO" in text
""",
    """    text = detail.inner_text()
    position = page.locator("#town-topic .composite-versilia-position")
    position.wait_for()
    position_text = position.inner_text()
    assert "Peso sulla Versilia" in position_text
    assert "48,89%" in position_text or "48.89%" in position_text
    scroll = detail.locator(".extractive-records-scroll")
    assert scroll.count() == 1
    scroll_state = scroll.evaluate("(el) => ({scrollHeight: el.scrollHeight, clientHeight: el.clientHeight, overflowY: getComputedStyle(el).overflowY, left: el.getBoundingClientRect().left, parentLeft: el.closest('.extractive-detail').getBoundingClientRect().left})")
    assert scroll_state["scrollHeight"] > scroll_state["clientHeight"]
    assert scroll_state["overflowY"] in ("auto", "scroll")
    assert scroll_state["left"] - scroll_state["parentLeft"] >= 15
    assert "TOMBACCIO" in text
""",
    "browser RTCave position/scroll",
)
bt = replace_once(
    bt,
    """    page.get_by_text("Produzione estrattiva", exact=True).first.wait_for()
    detail = page.locator("#compare-bars .extractive-detail:visible")
""",
    """    page.get_by_text("Produzione estrattiva", exact=True).first.wait_for()
    assert "79.452" in page.locator("#compare-definition").inner_text()
    detail = page.locator("#compare-bars .extractive-detail:visible")
""",
    "browser production aggregate",
)
bt = replace_once(
    bt,
    """    assert "55.801" in detail.inner_text()
    table = detail.locator("table.indicator-values-table:visible")
""",
    """    assert "55.801" in detail.inner_text()
    chart = page.locator("#town-topic .history-panel .trend-chart:visible")
    chart.wait_for()
    chart_text = chart.inner_text()
    assert "2019" in chart_text and "2025" in chart_text
    position = page.locator("#town-topic .versilia-position")
    position.wait_for()
    pos_text = position.inner_text()
    assert "79.452" in pos_text
    assert "n.d." not in pos_text.lower()
    table = detail.locator("table.indicator-values-table:visible")
""",
    "browser production history/position",
)
bt = replace_once(
    bt,
    """    no_page_overflow(page, "PRC confronto")

    page.goto(urljoin(base, "comuni/pietrasanta/?tema=ambiente&indicatore=extractivePlanning"), wait_until="networkidle")
""",
    """    no_page_overflow(page, "PRC confronto")

    page.goto(urljoin(base, "comuni/seravezza/?tema=ambiente&indicatore=extractivePlanning"), wait_until="networkidle")
    wait_town_metric(page, "extractivePlanning")
    select = page.locator("#town-topic select[data-composite-choice]")
    select.wait_for()
    select.select_option("part-1")
    page.wait_for_timeout(250)
    position = page.locator("#town-topic .composite-versilia-position")
    position_text = position.inner_text()
    assert "Quota territoriale Versilia" in position_text
    assert ("0,16%" in position_text or "0.16%" in position_text)
    assert ("0,97%" in position_text or "0.97%" in position_text)
    assert "603" not in position_text
    no_page_overflow(page, "PRC quota territorio Seravezza")

    page.goto(urljoin(base, "comuni/pietrasanta/?tema=ambiente&indicatore=extractivePlanning"), wait_until="networkidle")
""",
    "browser PRC percent semantics",
)
write(BROWSER_TEST, bt)

# 9) Sincronizza il sorgente monolitico col bundle modulare.
parts = sorted((ROOT / "assets/app-parts").glob("[0-9][0-9].txt"))
if len(parts) != 7:
    raise RuntimeError(f"Attesi 7 app-parts, trovati {len(parts)}")
APP.write_text("".join(p.read_text(encoding="utf-8") for p in parts), encoding="utf-8")

print("Fix revisione draft v1.28 applicati.")
