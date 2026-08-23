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
        '<span class="overline">Età e sesso</span><h4>Piramide dei tassi</h4>',
        '<span class="overline">${row.town === \'Versilia\' ? \'Totale Versilia · Età e sesso\' : \'Età e sesso\'}</span><h4>${row.town === \'Versilia\' ? \'Piramide dei tassi · Versilia\' : \'Piramide dei tassi\'}</h4>',
        "identità piramide",
    )

    text = replace_once(
        text,
        '<p class="aggregate-note demographic-rate-pyramid-note">La piramide usa solo fasce non sovrapposte. Le letture aggregate 25–64 e complessiva restano disponibili nei selettori e nel dettaglio.</p>',
        '<p class="aggregate-note demographic-rate-pyramid-note">${row.town === \'Versilia\' ? \'Il totale Versilia è calcolato sommando numeratori e denominatori dei sette Comuni, non mediando le percentuali. \' : \'\'}La piramide usa solo fasce non sovrapposte. Le letture aggregate 25–64 e complessiva restano disponibili nei selettori e nel dettaglio.</p>',
        "nota aggregazione Versilia",
    )

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
        ? demographicRatePyramidMarkup(metric,{town:'Versilia',parts:metric.aggregate?.parts || []})
        : '';

      if (compositeType === 'demographicBreakdown') {
        const points = [...demographicPyramid.querySelectorAll('.age-pyramid-point')];
        const hideAll = except => points.forEach(point => {
          if (point === except) return;
          point.querySelector('.chart-tooltip')?.setAttribute('hidden','');
        });
        points.forEach(point => {
          const tooltip = point.querySelector('.chart-tooltip');
          if (!tooltip) return;
          const show = () => {
            hideAll(point);
            tooltip.removeAttribute('hidden');
          };
          const hide = () => tooltip.setAttribute('hidden','');
          point.addEventListener('pointerenter', show);
          point.addEventListener('pointerleave', hide);
          point.addEventListener('focus', show);
          point.addEventListener('blur', hide);
          point.addEventListener('click', event => {
            event.preventDefault();
            show();
          });
          point.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              show();
            } else if (event.key === 'Escape') {
              hide();
              point.blur();
            }
          });
        });
      }
    }

'''
    text = replace_once(text, benchmark_anchor, pyramid_runtime + benchmark_anchor, "render aggregato Versilia")
    APP.write_text(text, encoding="utf-8")
    print("APP: piramide età/genere del totale Versilia aggiunta ai confronti Lavoro/Istruzione con tooltip interattivi")


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
