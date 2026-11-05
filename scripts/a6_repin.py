#!/usr/bin/env python3
"""Ri-registra le impronte A6 dopo un aggiornamento dati verificato.

Esegue ogni indicatore del catalogo effettivo, in ogni dimensione, con il motore
A6 in modalità ri-registrazione: ogni confronto con un'impronta registrata
annota il valore osservato. Poi confronta con `ci/a6-source-pins.json`:

- senza `--write` mostra soltanto le differenze (prova a secco);
- con `--write --allow modulo1,modulo2` scrive le nuove impronte, ma fallisce
  se cambia un'impronta di un adattatore non dichiarato: un aggiornamento delle
  cave non può cambiare in silenzio le impronte del turismo.

Uso tipico dopo un aggiornatore:

    python scripts/a6_repin.py --catalog dist/data/site-data.json --allow extractive --write
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ["A6_REPIN"] = "1"
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import a6_pins  # noqa: E402
import semantic_query_engine as engine_module  # noqa: E402
from semantic_query_engine import QueryEngine  # noqa: E402


def exercise(catalog: Path) -> int:
    engine = QueryEngine(catalog, layer="effective")
    queries = 0
    for key in sorted(engine._catalog["metrics"]):
        try:
            dims = engine_module.dimensions(key)
        except Exception:
            dims = ["total"]
        for dim in dims or ["total"]:
            for operation in ("compare", "series"):
                request = {"operation": operation, "selectors": [{"metric": key, "dimension": dim}], "allowPartial": True}
                try:
                    engine.query(request)
                except Exception:
                    pass
                queries += 1
    return queries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--allow", default="", help="Adattatori autorizzati a cambiare impronta (es. extractive,road)")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    queries = exercise(args.catalog)
    document = json.loads(a6_pins.REGISTRY.read_text(encoding="utf-8"))
    registry = document["pins"]
    recorded = a6_pins.RECORDED
    changed = {k: (registry[k], v) for k, v in recorded.items() if registry.get(k) != v}
    unexercised = sorted(set(registry) - set(recorded))
    allowed = {m for m in args.allow.split(",") if m}
    forbidden = sorted(k for k in changed if k.split("#")[0] not in allowed)

    print(f"Richieste eseguite: {queries}; impronte esercitate {len(recorded)}/{len(registry)}; cambiate {len(changed)}")
    for key, (old, new) in sorted(changed.items()):
        print(f"  {key}: {old[:12]}… → {new[:12]}…{'  (NON autorizzata)' if key in forbidden else ''}")
    if unexercised:
        print(f"Impronte non esercitate (restano invariate): {', '.join(unexercised)}")
    if not args.write:
        return 0
    if forbidden:
        print("Scrittura rifiutata: cambiano impronte di adattatori non dichiarati con --allow.")
        return 1
    registry.update({k: new for k, (_, new) in changed.items()})
    a6_pins.REGISTRY.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"Registro aggiornato: {len(changed)} impronte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
