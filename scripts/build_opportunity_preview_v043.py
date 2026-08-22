#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import tempfile
import unicodedata
from pathlib import Path

import build_opportunity_preview_v04 as base
import source_favicon_assets

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "reports" / "runtime" / "opportunities-v04.json"
DEFAULT_DIST = ROOT / "dist"


def _slug(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def _source_options(payload: dict) -> str:
    rows = list((payload.get("sourceCoverage") or {}).get("rows") or [])
    options = []
    for row in sorted(rows, key=lambda x: str(x.get("label") or x.get("source_id") or "").lower()):
        source_id = str(row.get("source_id") or "")
        if not source_id:
            continue
        label = str(row.get("label") or source_id)
        public_count = int(row.get("publicCount") or row.get("verifiedOutputCount") or 0)
        status = str(row.get("monitoringStatus") or "active")
        if status == "planned":
            suffix = " · pianificata"
        elif public_count:
            suffix = f" · {public_count} corrent{'e' if public_count == 1 else 'i'}"
        else:
            suffix = " · monitorata"
        options.append(
            f'<option value="{html.escape(_slug(source_id), quote=True)}" data-current-count="{public_count}">'
            f'{html.escape(label + suffix)}</option>'
        )
    return '<option value="">Tutte le fonti monitorate</option>' + "".join(options)


def build(payload_path: Path, dist: Path) -> Path:
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    payload, provenance = source_favicon_assets.materialize(payload, dist)
    public_sources = {str(x.get("source_id") or "") for x in payload.get("opportunities") or [] if x.get("source_id")}
    missing_icons = sorted(public_sources - set(provenance))
    if missing_icons:
        raise SystemExit("Favicon ufficiale non risolto per: " + ", ".join(missing_icons))

    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False)
        temp_path = Path(handle.name)
    try:
        target = base.build(temp_path, dist)
    finally:
        temp_path.unlink(missing_ok=True)

    text = target.read_text(encoding="utf-8")
    text = text.replace("v0.4.2", "v0.4.3")
    source_select = '<select data-op-source>' + _source_options(payload) + '</select>'
    text, replacements = re.subn(
        r'<select data-op-source>.*?</select>',
        source_select,
        text,
        count=1,
        flags=re.S,
    )
    if replacements != 1:
        raise SystemExit("Filtro Fonte non trovato nella preview v0.4.3")
    text = text.replace(
        "Filtra per Comune, stato, modalità, fonte o ricerca libera.",
        "Filtra per Comune, stato, modalità, fonte o ricerca libera. Il menu Fonte mostra l'intera rete monitorata, anche quando una fonte non ha opportunità correnti.",
        1,
    )
    target.write_text(text, encoding="utf-8")

    check = target.read_text(encoding="utf-8")
    if "Anteprima v0.4.3" not in check:
        raise SystemExit("Preview v0.4.3 non materializzata correttamente")
    if "Tutte le fonti monitorate" not in check or "UE · URBACT · monitorata" not in check:
        raise SystemExit("La preview non espone l'intera rete nel filtro Fonte")
    if "../assets/source-favicons/" not in check:
        raise SystemExit("I favicon ufficiali locali non sono stati materializzati")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()
    print(f"Preview opportunità v0.4.3 materializzata: {build(args.data, args.dist)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
