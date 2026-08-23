#!/usr/bin/env python3
"""Confina piramide e tabella età×genere nei propri scroller senza overflow pagina."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets" / "visual-grammar.css"
MARKER = "PR91 mobile containment"


def main() -> None:
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
    print("PR91: piramide, tabella e selettori confinati; nessun min-content deve allargare la pagina mobile.")


if __name__ == "__main__":
    main()
