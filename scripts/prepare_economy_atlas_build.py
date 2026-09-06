#!/usr/bin/env python3
"""Prepara il builder statico per la preview dell'Atlante Economia.

Rimuove esclusivamente il vecchio runtime ATECO globale e registra il nuovo
custom element. La modifica avviene nel checkout effimero della CI; il sorgente
canonico resta invariato.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_STATIC = ROOT / "scripts" / "build_static.py"


def main() -> None:
    lines = BUILD_STATIC.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Normalizzazioni legacy: sono istruzioni su una sola riga.
        if "text = re.sub" in line and "ateco-detail" in line:
            i += 1
            continue

        # Iniezione CSS legacy: if + singola replace.
        if stripped == 'if "assets/ateco-detail.css" not in text:':
            i += 2
            continue

        # Iniezione JS legacy: salta l'intero blocco text.replace(...).
        if stripped == 'if "assets/ateco-detail.js" not in text:':
            i += 1
            while i < len(lines):
                candidate = lines[i]
                i += 1
                if candidate.startswith("            )"):
                    break
            continue

        out.append(line)
        i += 1

    text = "".join(out)
    if "ateco-detail.js" in text or "ateco-detail.css" in text:
        raise RuntimeError("Riferimenti legacy ATECO residui nel builder")

    if "assets/economy-atlas.js" not in text:
        anchor = '        path.write_text(text, encoding="utf-8")\n'
        block = '''        if "assets/economy-atlas.js" not in text:\n            text = text.replace(\n                "</body>",\n                f'  <script src="{assets}assets/economy-atlas.js" defer></script>\\n</body>',\n            )\n\n'''
        if text.count(anchor) != 1:
            raise RuntimeError("Punto di iniezione runtime Atlante non univoco")
        text = text.replace(anchor, block + anchor, 1)

    BUILD_STATIC.write_text(text, encoding="utf-8")
    print("Builder preview Atlante preparato: runtime legacy rimosso, economy-atlas.js registrato.")


if __name__ == "__main__":
    main()
