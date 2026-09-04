#!/usr/bin/env python3
"""Patch isolata del runtime della preview Agricoltura II.

La preview usa ``ratioProfile`` per impedire che gli indicatori Agricoltura II
ricadano nelle vecchie semantiche di ``agricultureProfile``. Le due librerie
post-render devono quindi conoscere questo profilo:

- visual-grammar: punti e riferimento devono usare la componente selezionata e
  il rapporto Versilia dichiarato in ``aggregate.parts``;
- ux-history: il grafico corrente delle schede comunali deve aggiornarsi quando
  cambia il selettore.

La patch opera solo su ``dist`` e non modifica gli asset canonici del branch.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def replace_exact(path: Path, old: str, new: str, expected: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(
            f"Patch non applicabile a {path.name}: attese {expected} occorrenze, trovate {count}"
        )
    path.write_text(text.replace(old, new), encoding="utf-8")


def patch_visual_grammar() -> None:
    path = DIST / "assets" / "visual-grammar.js"
    base_types = (
        "['stock','omi','mobility','securityMeasures','demographicBreakdown',"
        "'agricultureProfile','financialProfile','sexBreakdown']"
    )
    ratio_types = (
        "['stock','omi','mobility','securityMeasures','demographicBreakdown',"
        "'agricultureProfile','ratioProfile','financialProfile','sexBreakdown']"
    )
    replace_exact(path, base_types, ratio_types, expected=2)
    replace_exact(
        path,
        "if (type === 'securityMeasures' || type === 'agricultureProfile' || type === 'financialProfile') {",
        "if (type === 'securityMeasures' || type === 'agricultureProfile' || type === 'ratioProfile' || type === 'financialProfile') {",
    )
    replace_exact(
        path,
        "if (type === 'securityMeasures' || type === 'financialProfile') {",
        "if (type === 'securityMeasures' || type === 'ratioProfile' || type === 'financialProfile') {",
    )
    # Il pannello comunale ratioProfile viene già aggiornato correttamente dal
    # renderer con l'aggregate.parts selezionato. Visual grammar non deve
    # sovrascriverlo con la logica generica della media comunale.
    replace_exact(
        path,
        "if (['distribution','agricultureProfile','financialProfile'].includes(metric.meta?.compositeType)) return;",
        "if (['distribution','agricultureProfile','ratioProfile','financialProfile'].includes(metric.meta?.compositeType)) return;",
    )


def patch_history() -> None:
    path = DIST / "assets" / "ux-history.js"
    base_types = "['distribution','omi','stock','securityMeasures','sexBreakdown']"
    ratio_types = "['distribution','omi','stock','securityMeasures','ratioProfile','sexBreakdown']"
    # Una occorrenza abilita compositeChoiceMetric, la seconda il refresh della
    # vista corrente nelle schede comunali.
    replace_exact(path, base_types, ratio_types, expected=2)


def validate() -> None:
    visual = (DIST / "assets" / "visual-grammar.js").read_text(encoding="utf-8")
    history = (DIST / "assets" / "ux-history.js").read_text(encoding="utf-8")
    if visual.count("ratioProfile") < 4:
        raise RuntimeError("ratioProfile non integrato completamente in visual-grammar.js")
    if history.count("ratioProfile") < 2:
        raise RuntimeError("ratioProfile non integrato completamente in ux-history.js")
    subprocess.run(["node", "--check", str(DIST / "assets" / "visual-grammar.js")], check=True)
    subprocess.run(["node", "--check", str(DIST / "assets" / "ux-history.js")], check=True)


def main() -> None:
    if not DIST.exists():
        raise SystemExit("dist/ non esiste: eseguire prima build_agricoltura_ii_preview.py")
    patch_visual_grammar()
    patch_history()
    validate()
    print(
        "Agricoltura II preview runtime: aggregate Versilia e refresh dei grafici comunali abilitati."
    )


if __name__ == "__main__":
    main()
