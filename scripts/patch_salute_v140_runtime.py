#!/usr/bin/env python3
"""Runtime refinements for Salute v1.40 town pages.

The public build is transactional: this patch updates the materialized catalog and
UI sources only inside the ephemeral build workspace. Canonical tracked sources are
restored by ``public_build_workspace`` after prerendering.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
APP_PART = ROOT / "assets" / "app-parts" / "04.txt"
VISUAL_GRAMMAR = ROOT / "assets" / "visual-grammar.js"
VISUAL_GRAMMAR_CSS = ROOT / "assets" / "visual-grammar.css"


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Salute v1.40 runtime patch non univoca ({label}): {count}")
    return source.replace(old, new, 1)


def patch_health_comparison_contract() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    health = data.get("themes", {}).get("salute", {})
    metric_keys = health.get("metrics", [])
    metrics = data.get("metrics", {})

    for key in metric_keys:
        metric = metrics.get(key)
        if not isinstance(metric, dict):
            continue
        meta = metric.setdefault("meta", {})
        aggregate = metric.get("aggregate") or {}
        aggregate_label = str(aggregate.get("label") or "")

        # Strutture fisiche: il confronto percentuale corretto è la quota del
        # Comune sul totale dei sette Comuni, non lo scostamento dalla media.
        if key in {"hospitals", "accreditedRsaCount"}:
            meta["comparisonReference"] = "aggregate"
            meta["comparisonDifference"] = "shareOfAggregate"
            meta["comparisonLabel"] = "totale Versilia"
            meta["comparisonOverline"] = "Quota sul totale Versilia"
            meta["comparisonShareDirection"] = "del totale Versilia"
            meta["comparisonNote"] = (
                "Quota delle strutture presenti nel Comune sul totale censito nei sette Comuni; "
                "non misura accessibilità, capacità o qualità del servizio."
            )
            continue

        # Nel tema Salute l'aggregate già pubblicato è il riferimento editoriale:
        # ARS 202M, mediana dichiarata o densità territoriale. Non va sostituito
        # da una media semplice calcolata dal runtime.
        if aggregate.get("value") is None:
            continue
        meta["comparisonReference"] = "aggregate"

        if aggregate_label == "Valore ARS Versilia":
            meta["comparisonLabel"] = "valore ARS Versilia"
            meta["comparisonDirectionLabel"] = "il valore ARS Versilia"
            meta["comparisonOverline"] = "Rispetto al valore ARS Versilia"
            meta["comparisonNote"] = (
                "Il confronto usa l’aggregato ufficiale Zona Versilia pubblicato da ARS, "
                "non la media semplice dei Comuni; descrive uno scostamento numerico e "
                "non esprime un giudizio di qualità."
            )
        elif aggregate_label.startswith("Mediana"):
            meta["comparisonLabel"] = "mediana Versilia"
            meta["comparisonDirectionLabel"] = "la mediana Versilia"
            meta["comparisonOverline"] = "Rispetto alla mediana Versilia"
            meta["comparisonNote"] = (
                "Il confronto usa la mediana dichiarata per i sette Comuni e descrive "
                "soltanto lo scostamento numerico."
            )
        elif aggregate_label == "Densità Versilia":
            meta["comparisonLabel"] = "densità Versilia"
            meta["comparisonDirectionLabel"] = "la densità Versilia"
            meta["comparisonOverline"] = "Rispetto alla densità Versilia"
            meta["comparisonNote"] = (
                "Il confronto usa la densità calcolata sul totale della popolazione dei "
                "sette Comuni, non la media semplice delle densità comunali."
            )
        else:
            meta["comparisonLabel"] = "riferimento Versilia"
            meta["comparisonDirectionLabel"] = "il riferimento Versilia"
            meta["comparisonOverline"] = "Rispetto al riferimento Versilia"
            meta["comparisonNote"] = (
                "Il confronto usa il riferimento territoriale dichiarato dall’indicatore "
                "e non introduce valutazioni di qualità."
            )

    save_json(DATA, data)


def patch_visual_grammar() -> None:
    source = VISUAL_GRAMMAR.read_text(encoding="utf-8")
    source = replace_once(
        source,
        "if (['maritimeConcessions','maritimeConcessionFeesDue','extractiveSites','extractiveProduction','extractivePlanning'].includes(key) && metric?.meta?.comparisonDifference === 'shareOfAggregate') {",
        "if (metric?.meta?.comparisonDifference === 'shareOfAggregate') {",
        "shareOfAggregate generic contract",
    )
    source = replace_once(
        source,
        ": 'del totale dei quattro Comuni costieri';",
        ": (metric?.meta?.comparisonShareDirection || 'del totale Versilia');",
        "share direction fallback",
    )
    source = replace_once(
        source,
        "    if (aggregate === 0) {",
        "    const directionReference = metric?.meta?.comparisonDirectionLabel || `la ${comparisonLabel}`;\n    if (aggregate === 0) {",
        "comparison direction reference",
    )
    source = replace_once(
        source,
        "        direction: diff === 0 ? 'in linea' : diff > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia',\n        compact: 'confronto con Versilia',\n      };",
        "        direction: diff === 0 ? 'in linea' : diff > 0 ? `sopra ${directionReference}` : `sotto ${directionReference}`,\n        compact: `confronto con ${comparisonLabel}`,\n        overline,\n        note,\n      };",
        "zero-reference comparison copy",
    )
    source = replace_once(
        source,
        "    if (Math.abs(relative) < 0.05) return { headline: '0,0%', direction: 'in linea', compact: 'in linea con la media Versilia' };",
        "    if (Math.abs(relative) < 0.05) return { headline: '0,0%', direction: 'in linea', compact: `in linea con ${comparisonLabel}`, overline, note };",
        "relative in-line copy",
    )
    source = replace_once(
        source,
        "      direction: relative > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia',\n      compact: `${sign}${abs}% vs media Versilia`,\n    };",
        "      direction: relative > 0 ? `sopra ${directionReference}` : `sotto ${directionReference}`,\n      compact: `${sign}${abs}% vs ${comparisonLabel}`,\n      overline,\n      note,\n    };",
        "relative comparison copy",
    )
    VISUAL_GRAMMAR.write_text(source, encoding="utf-8")


def remove_redundant_health_deep_dive() -> None:
    source = APP_PART.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\n    if \(themeKey === 'salute'\) \{.*?\n    \}\n    if \(themeKey === 'economia'\)",
        flags=re.DOTALL,
    )
    replacement = "\n    if (themeKey === 'salute') return '';\n    if (themeKey === 'economia')"
    source, count = pattern.subn(replacement, source, count=1)
    if count != 1:
        raise RuntimeError(f"Blocco approfondimento Salute non trovato in modo univoco: {count}")
    APP_PART.write_text(source, encoding="utf-8")


def patch_health_position_layout() -> None:
    source = VISUAL_GRAMMAR_CSS.read_text(encoding="utf-8")
    sentinel = "/* Salute v1.40: confronto comunale senza sovrapposizioni */"
    if sentinel in source:
        return
    source += f"""

{sentinel}
.town-topic[data-theme="salute"] .versilia-position > div {{
  grid-template-columns: 1fr;
  align-items: start;
  gap: 5px;
}}

.town-topic[data-theme="salute"] .versilia-position > div span {{
  min-width: 0;
  overflow-wrap: anywhere;
}}

.town-topic[data-theme="salute"] .versilia-position > div b {{
  max-width: 100%;
  text-align: left;
  line-height: 1.12;
}}
"""
    VISUAL_GRAMMAR_CSS.write_text(source, encoding="utf-8")


def main() -> None:
    patch_health_comparison_contract()
    patch_visual_grammar()
    remove_redundant_health_deep_dive()
    patch_health_position_layout()
    print("Salute v1.40 runtime: riferimenti Versilia, quote strutture e scheda comunale allineati")


if __name__ == "__main__":
    main()
