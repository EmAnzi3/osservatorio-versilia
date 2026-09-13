#!/usr/bin/env python3
"""Allinea gli scostamenti UI al benchmark pro capite Versilia dichiarato nei dati.

La patch opera nel workspace effimero della build, dopo le patch runtime delle
release precedenti. Modifica soltanto il ramo relativo di ``deltaFor``: per gli
indicatori marcati dal contratto dati come ``valore pro capite Versilia`` usa
quel benchmark anche nel testo e propaga overline/nota metodologica.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VISUAL_GRAMMAR = ROOT / "assets" / "visual-grammar.js"
SENTINEL = "territorialPerCapitaReference"

OLD = """    if (aggregate === 0) {
      const diff = local - aggregate;
      return {
        headline: formatAxis(diff, metric.meta.unit),
        direction: diff === 0 ? 'in linea' : diff > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia',
        compact: 'confronto con Versilia',
      };
    }

    const relative = ((local / aggregate) - 1) * 100;
    if (Math.abs(relative) < 0.05) return { headline: '0,0%', direction: 'in linea', compact: 'in linea con la media Versilia' };
    const sign = relative > 0 ? '+' : '−';
    const abs = number1.format(Math.abs(relative));
    return {
      headline: `${sign}${abs}%`,
      direction: relative > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia',
      compact: `${sign}${abs}% vs media Versilia`,
    };
"""

NEW = """    const territorialPerCapitaReference = comparisonLabel === 'valore pro capite Versilia';
    if (aggregate === 0) {
      const diff = local - aggregate;
      return {
        headline: formatAxis(diff, metric.meta.unit),
        direction: diff === 0
          ? 'in linea'
          : territorialPerCapitaReference
            ? (diff > 0 ? 'sopra il valore pro capite Versilia' : 'sotto il valore pro capite Versilia')
            : (diff > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia'),
        compact: territorialPerCapitaReference ? 'confronto con il valore pro capite Versilia' : 'confronto con Versilia',
        overline,
        note,
      };
    }

    const relative = ((local / aggregate) - 1) * 100;
    if (Math.abs(relative) < 0.05) return {
      headline: '0,0%',
      direction: 'in linea',
      compact: territorialPerCapitaReference ? 'in linea con il valore pro capite Versilia' : 'in linea con la media Versilia',
      overline,
      note,
    };
    const sign = relative > 0 ? '+' : '−';
    const abs = number1.format(Math.abs(relative));
    return {
      headline: `${sign}${abs}%`,
      direction: territorialPerCapitaReference
        ? (relative > 0 ? 'sopra il valore pro capite Versilia' : 'sotto il valore pro capite Versilia')
        : (relative > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia'),
      compact: territorialPerCapitaReference
        ? `${sign}${abs}% vs valore pro capite Versilia`
        : `${sign}${abs}% vs media Versilia`,
      overline,
      note,
    };
"""


def main() -> None:
    source = VISUAL_GRAMMAR.read_text(encoding="utf-8")
    if SENTINEL in source:
        if "sopra il valore pro capite Versilia" not in source:
            raise RuntimeError("Patch benchmark pro capite applicata solo parzialmente")
        print("Runtime benchmark pro capite Versilia gia' applicato.")
        return

    count = source.count(OLD)
    if count != 1:
        raise RuntimeError(
            "Runtime benchmark pro capite: blocco deltaFor inatteso: "
            f"attesa 1 occorrenza, trovate {count}"
        )
    source = source.replace(OLD, NEW, 1)
    VISUAL_GRAMMAR.write_text(source, encoding="utf-8")
    print("Runtime benchmark pro capite Versilia applicato.")


if __name__ == "__main__":
    main()
