#!/usr/bin/env python3
"""Confina piramide, tabella e toolbar età×genere senza overflow pagina."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets" / "visual-grammar.css"
FIDELITY = ROOT / "assets" / "fidelity.css"
MARKER = "PR91 mobile containment"


def patch_visual_containment() -> None:
    text = CSS.read_text(encoding="utf-8")
    if MARKER in text:
        print("Containment mobile PR91 già applicato")
        return
    patch = r'''

/* PR91 mobile containment */
.history-panel.composite-history-panel,
.composite-fixed-detail,
.demographic-rate-pyramid,
.demographic-rate-detail,
.demographic-rate-table-wrap,
.demographic-rate-pyramid .age-pyramid-trend {
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.history-panel.composite-history-panel,
.composite-fixed-detail {
  overflow-x: hidden;
}

.demographic-rate-pyramid .age-pyramid-trend,
.demographic-rate-table-wrap {
  display: block;
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}

.demographic-rate-pyramid-chart {
  width: 720px;
  min-width: 720px;
  max-width: none;
}

.demographic-town-selectors,
.demographic-town-selectors label,
.demographic-town-selectors select {
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.demographic-town-selectors select {
  width: 100%;
}

@media (max-width: 700px) {
  .history-panel.composite-history-panel {
    width: 100%;
  }

  .demographic-rate-pyramid .age-pyramid-trend,
  .demographic-rate-table-wrap {
    scrollbar-gutter: stable;
  }
}
'''
    CSS.write_text(text.rstrip() + patch + "\n", encoding="utf-8")
    print("PR91: piramide, tabella e selettori confinati senza overflow pagina.")


def patch_laptop_toolbar() -> None:
    text = FIDELITY.read_text(encoding="utf-8")
    old = '''@media(max-width:1000px){
  .compare-chart-toolbar{align-items:flex-start;flex-direction:column;gap:13px}
  .compare-chart-toolbar .compare-view-controls{width:100%;justify-content:flex-start;flex-wrap:wrap}
  .compare-chart-toolbar .compare-choice-select{flex:1 1 220px;width:auto}
}'''
    new = '''@media(max-width:1100px){
  .compare-chart-toolbar{align-items:flex-start;flex-direction:column;gap:13px;min-width:0;max-width:100%;box-sizing:border-box}
  .compare-chart-toolbar .compare-view-controls{width:100%;max-width:100%;min-width:0;box-sizing:border-box;justify-content:flex-start;flex-wrap:wrap}
  .compare-chart-toolbar .compare-choice-select{flex:1 1 220px;width:auto;max-width:100%}
}'''
    if new in text:
        print("Containment laptop toolbar PR91 già applicato")
        return
    if old not in text:
        raise RuntimeError("Breakpoint toolbar confronto non trovato: aggiornare il patch PR91")
    FIDELITY.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("PR91: toolbar confronto compatta fino a 1100px; coperto il viewport laptop 1024px.")


def main() -> None:
    patch_visual_containment()
    patch_laptop_toolbar()


if __name__ == "__main__":
    main()
