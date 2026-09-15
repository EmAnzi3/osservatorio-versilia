#!/usr/bin/env python3
"""Generate/check the README public-status block from the materialized release."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from public_build_snapshot import effective_public_catalog, public_registry_path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
START = "<!-- OV_PUBLIC_STATUS_START -->"
END = "<!-- OV_PUBLIC_STATUS_END -->"


def _registry() -> dict[str, Any]:
    value = json.loads(public_registry_path().read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Registry pubblico non valido")
    return value


def release_summary() -> dict[str, Any]:
    data = effective_public_catalog()
    registry = _registry()
    metrics = data.get("metrics")
    towns = data.get("towns")
    themes = data.get("themes")
    if not isinstance(metrics, dict) or not isinstance(towns, list) or not isinstance(themes, dict):
        raise RuntimeError("Catalogo pubblico non valido per il riepilogo release")
    external = sum(
        isinstance(metric, dict)
        and (metric.get("dataStorage") or {}).get("type") == "external-climate"
        for metric in metrics.values()
    )
    special = sum(
        isinstance(metric, dict)
        and (metric.get("dataStorage") or {}).get("type") == "special-route"
        for metric in metrics.values()
    )
    total = len(metrics)
    inline = total - external
    standalone = inline - special
    expected = (
        int(registry.get("expectedMetricCount", -1)),
        int(registry.get("expectedInlineMetricCount", -1)),
        int(registry.get("expectedExternalMetricCount", -1)),
    )
    actual = (total, inline, external)
    if expected != actual:
        raise RuntimeError(f"Registry pubblico non allineato al riepilogo README: {expected} != {actual}")
    version = str(data.get("version") or "").strip()
    updated = str(data.get("updated") or "").strip()
    if not version or not updated:
        raise RuntimeError("Versione/data aggiornamento mancanti nel catalogo pubblico")
    return {
        "version": version,
        "updated": updated,
        "towns": len(towns),
        "themes": len(themes),
        "total": total,
        "inline": inline,
        "standalone": standalone,
        "special": special,
        "external": external,
    }


def render_status_block(summary: dict[str, Any]) -> str:
    return f"""{START}
Release corrente: **{summary['version']}** — aggiornata **{summary['updated']}**.

## Stato del progetto

- **{summary['towns']} Comuni**: Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema e Viareggio;
- **{summary['themes']} aree tematiche**;
- **{summary['total']} indicatori pubblicati**;
- **{summary['inline']} indicatori incorporati**: {summary['standalone']} con scheda autonoma e {summary['special']} con route dedicata;
- **{summary['external']} indicatori climatici esterni**, integrati nell'esperienza del sito con storici separati;
- confronti territoriali, profili comunali, serie storiche e benchmark Versilia;
- benchmark Toscana/Italia quando la comparabilità metodologica è adeguata;
- esportazione CSV e stampa/PDF nelle viste che la supportano;
- approfondimenti dedicati, tra cui PNRR, Atlante economico/ATECO, Opportunità e Percorsi;
- Stato dati, metodologia, fonti e segnalazioni accessibili dal sito pubblico.
{END}"""


def _inject_initial(text: str, block: str) -> str:
    method = "## Metodo e qualità dei dati"
    start = text.find("Release corrente:")
    end = text.find(method)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("README privo del blocco release legacy atteso")
    text = text[:start] + block + "\n\n" + text[end:]
    text = re.sub(
        r"- `indicatori/` — \d+ schede indicatore autonome generate dalla build;",
        "- `indicatori/` — schede indicatore autonome generate dalla build, salvo route dedicate e indicatori esterni;",
        text,
    )
    return text


def expected_readme(text: str | None = None) -> str:
    text = README.read_text(encoding="utf-8") if text is None else text
    block = render_status_block(release_summary())
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1:
            raise RuntimeError("Marker README pubblico duplicati o incompleti")
        begin = text.index(START)
        finish = text.index(END, begin) + len(END)
        return text[:begin] + block + text[finish:]
    return _inject_initial(text, block)


def write_readme() -> dict[str, Any]:
    current = README.read_text(encoding="utf-8")
    expected = expected_readme(current)
    README.write_text(expected, encoding="utf-8")
    return release_summary()


def validate_readme() -> dict[str, Any]:
    current = README.read_text(encoding="utf-8")
    expected = expected_readme(current)
    if current != expected:
        raise RuntimeError(
            "README pubblico non derivato dalla release corrente. Eseguire: "
            "python scripts/public_readme_status.py --write"
        )
    outside = current.replace(current[current.index(START): current.index(END) + len(END)], "")
    if re.search(r"Novità della v\d+\.\d+\.\d+", outside):
        raise RuntimeError("README contiene ancora una sezione release-specifica mantenuta a mano")
    return release_summary()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    summary = write_readme() if args.write else validate_readme()
    verb = "aggiornato" if args.write else "allineato"
    print(
        f"README pubblico {verb}: {summary['version']} · {summary['total']} indicatori · "
        f"{summary['updated']}."
    )


if __name__ == "__main__":
    main()
