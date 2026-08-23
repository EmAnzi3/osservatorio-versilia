#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import html
import json
import re
import tempfile
import unicodedata
from pathlib import Path

import build_opportunity_preview_v04 as base
import source_brandmark_fallback
import source_favicon_assets
import source_mic_favicon_alias
import source_pcm_favicon_alias
import source_pinned_favicon_assets

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


def _transfer_dynamic_favicons(target_payload: dict, dynamic_payload: dict, pinned_sources: set[str]) -> None:
    by_source: dict[str, str] = {}
    for item in dynamic_payload.get("opportunities") or []:
        sid = str(item.get("source_id") or "")
        favicon = str((item.get("presentation") or {}).get("source_favicon") or "")
        if sid and favicon:
            by_source[sid] = favicon
    for item in dynamic_payload.get("archive") or []:
        sid = str(item.get("source_id") or "")
        favicon = str(item.get("source_favicon") or "")
        if sid and favicon:
            by_source[sid] = favicon

    for item in target_payload.get("opportunities") or []:
        sid = str(item.get("source_id") or "")
        if sid not in pinned_sources and sid in by_source:
            item.setdefault("presentation", {})["source_favicon"] = by_source[sid]
    for item in target_payload.get("archive") or []:
        sid = str(item.get("source_id") or "")
        if sid not in pinned_sources and sid in by_source:
            item["source_favicon"] = by_source[sid]


def build(payload_path: Path, dist: Path) -> Path:
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    # Le sorgenti già acquisite byte-per-byte da un run verde vengono
    # materializzate per prime. Il resolver dinamico non prova neppure a
    # raggiungerle: questo rende mic-dgcc indipendente da rete/HTML/Playwright.
    payload, pinned_provenance = source_pinned_favicon_assets.materialize(payload, dist)
    pinned_sources = set(pinned_provenance)

    dynamic_payload = copy.deepcopy(payload)
    if pinned_sources:
        dynamic_payload["opportunities"] = [
            item for item in dynamic_payload.get("opportunities") or []
            if str(item.get("source_id") or "") not in pinned_sources
        ]
        dynamic_payload["archive"] = [
            item for item in dynamic_payload.get("archive") or []
            if str(item.get("source_id") or "") not in pinned_sources
        ]

    dynamic_payload, dynamic_provenance = source_favicon_assets.materialize(dynamic_payload, dist)
    _transfer_dynamic_favicons(payload, dynamic_payload, pinned_sources)
    provenance = {**dynamic_provenance, **pinned_provenance}

    # Fallback istituzionali per gli altri sottositi fragili. Il DGCC non passa
    # più da qui perché è già coperto dal pin verificato sopra.
    payload, provenance = source_mic_favicon_alias.materialize(payload, dist, provenance)
    payload, provenance = source_pcm_favicon_alias.materialize(payload, dist, provenance)
    payload, provenance = source_brandmark_fallback.materialize_missing(payload, dist, provenance)
    public_sources = {str(x.get("source_id") or "") for x in payload.get("opportunities") or [] if x.get("source_id")}
    missing_icons = sorted(public_sources - set(provenance))
    if missing_icons:
        raise SystemExit("Icona ufficiale non risolta per: " + ", ".join(missing_icons))

    asset_dir = dist / "assets" / "source-favicons"
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )

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
        raise SystemExit("Le icone ufficiali locali non sono state materializzate")
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
