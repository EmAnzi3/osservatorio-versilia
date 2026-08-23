#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "assets" / "app-parts" / "03.txt"
CSS = ROOT / "assets" / "visual-grammar.css"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Patch piramide Versilia non applicabile: {label}")
    return text.replace(old, new, 1)


def patch_app() -> None:
    text = APP.read_text(encoding="utf-8")
    marker = 'id="compare-demographic-pyramid"'
    if marker in text:
        print("Piramide aggregata Versilia già applicata")
        return
    if "demographicRatePyramidMarkup" not in text:
        raise RuntimeError("Applicare prima refine_lavoro_istruzione_eta_genere_ui.py")

    text = replace_once(
        text,
        '      <section id="compare-benchmark" class="page-width"></section>',
        '      <section id="compare-demographic-pyramid" class="compare-demographic-pyramid page-width"></section>\n      <section id="compare-benchmark" class="page-width"></section>',
        "host confronto",
    )

    text = replace_once(
        text,
        "    const tools = document.getElementById('compare-tools');\n",
        "    const tools = document.getElementById('compare-tools');\n    const demographicPyramid = document.getElementById('compare-demographic-pyramid');\n",
        "riferimento host",
    )

    benchmark_anchor = "    benchmark.innerHTML = (metricKey.startsWith('slowMobility') || metric.meta.compositeType) ? '' : benchmarkMarkup(metric,aggregate,unit,null);"
    pyramid_runtime = r'''    if (demographicPyramid) {
      demographicPyramid.innerHTML = compositeType === 'demographicBreakdown'
        ? `<div class="section-heading compact compare-demographic-pyramid-heading"><div><span class="overline">Totale Versilia · ${html(metric.meta.year)}</span><h2>Piramide per età e genere</h2><p>${html(metric.meta.label)} nelle quattro fasce non sovrapposte. Il totale Versilia è calcolato sommando numeratori e denominatori dei sette Comuni, non mediando le percentuali.</p></div></div>${demographicRatePyramidMarkup(metric,{town:'Versilia',parts:metric.aggregate?.parts || []})}`
        : '';
    }

'''
    text = replace_once(text, benchmark_anchor, pyramid_runtime + benchmark_anchor, "render aggregato Versilia")
    APP.write_text(text, encoding="utf-8")
    print("APP: piramide età/genere del totale Versilia aggiunta ai confronti Lavoro/Istruzione")


def patch_css() -> None:
    text = CSS.read_text(encoding="utf-8")
    marker = "PR91 Versilia aggregate pyramid"
    if marker in text:
        print("CSS piramide aggregata Versilia già presente")
        return
    css = r'''

/* PR91 Versilia aggregate pyramid */
.compare-demographic-pyramid:empty {
  display: none;
}

.compare-demographic-pyramid {
  margin-top: 30px;
}

.compare-demographic-pyramid-heading {
  margin-bottom: 12px;
}

.compare-demographic-pyramid-heading p {
  max-width: 78ch;
}

@media (max-width: 700px) {
  .compare-demographic-pyramid {
    margin-top: 20px;
  }
}
'''
    CSS.write_text(text.rstrip() + css + "\n", encoding="utf-8")
    print("CSS: host piramide aggregata Versilia applicato")


def main() -> None:
    patch_app()
    patch_css()


if __name__ == "__main__":
    main()
