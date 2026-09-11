#!/usr/bin/env python3
"""Estende solo il formatter canonico con le unità fisiche usate dalla v1.35.0."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "assets" / "app-parts" / "00.txt"
MARKER = "/* OV BIOMETRIA UNITS v1.35.0 */"


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")
    if MARKER in source:
        return
    needle = "      case 'km': return `${number2.format(v)} km`;"
    replacement = """      /* OV BIOMETRIA UNITS v1.35.0 */
      case 'squareKm': return `${number2.format(v)} km²`;
      case 'peoplePerSquareKm': return `${number1.format(v)} ab./km²`;
      case 'metres': return `${number0.format(v)} m`;
      case 'km': return `${number2.format(v)} km`;"""
    if source.count(needle) != 1:
        raise RuntimeError(f"Formatter canonico non patchabile in modo univoco: {source.count(needle)} occorrenze")
    TARGET.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
    print("Unità Biometria aggiunte al formatter canonico.")


if __name__ == "__main__":
    main()
