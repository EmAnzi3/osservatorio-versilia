#!/usr/bin/env python3
"""Materializza l'Atlante Registro Imprese nella shell e nella navigazione pubblica."""
from __future__ import annotations

import json
from pathlib import Path

from site_chrome import ensure_sitemap_entries, synchronize_native_page

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TARGET = DIST / "confronta" / "economia" / "atlante-attivita-economiche" / "index.html"
CANONICAL = "https://osservatorioversilia.it/confronta/economia/atlante-attivita-economiche/"
EXPLORER = {
    "key": "economyActivityAtlas",
    "theme": "economia",
    "label": "Atlante delle attività economiche",
    "shortLabel": "Atlante attività economiche",
    "description": "Esplora 1.228 codici ATECO e confronta unità locali attive, specializzazione, peso toscano e storico nei sette Comuni della Versilia.",
    "year": "2014–2025",
    "source": "Regione Toscana — Banca dati Imprese / Registro Imprese InfoCamere",
    "route": "confronta/economia/atlante-attivita-economiche/",
    "searchTerms": [
        "ateco", "attività economiche", "imprese", "unità locali", "ul attive",
        "specializzazione", "registro imprese", "infocamere", "nautica", "marmo",
        "stabilimenti balneari", "gallerie d'arte"
    ],
}


def assert_canonical_dataset_unchanged() -> None:
    """La pagina speciale non deve mutare il catalogo canonico dei 181 indicatori."""
    source = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    built_path = DIST / "data" / "site-data.json"
    if not built_path.exists():
        raise RuntimeError(f"Catalogo runtime non trovato: {built_path}")
    built = json.loads(built_path.read_text(encoding="utf-8"))
    if source != built:
        raise RuntimeError("L'Atlante non può modificare dist/data/site-data.json: il catalogo canonico deve restare identico alla sorgente")


def patch_runtime_bundle() -> None:
    """Espone l'Atlante in conteggi e ricerca senza alterare site-data.json."""
    path = DIST / "assets" / "app-bundle.js"
    text = path.read_text(encoding="utf-8")

    explorer_json = json.dumps({EXPLORER["key"]: EXPLORER}, ensure_ascii=False, separators=(",", ":"))
    declaration = f"\n  const OV_SPECIAL_EXPLORERS = {explorer_json};\n"
    if "const OV_SPECIAL_EXPLORERS =" not in text:
        marker = "  'use strict';\n"
        if marker not in text:
            raise RuntimeError("Punto di inizializzazione del bundle non trovato")
        text = text.replace(marker, marker + declaration, 1)

    replacements = (
        (
            "${Object.keys(data.metrics).length} indicatori",
            "${Object.keys(data.metrics).length + Object.keys(OV_SPECIAL_EXPLORERS).length} indicatori",
        ),
        (
            "${theme.metrics.length} indicatori</span><i aria-hidden=\"true\">→</i>",
            "${theme.metrics.length + (theme.key === 'economia' ? Object.keys(OV_SPECIAL_EXPLORERS).length : 0)} indicatori</span><i aria-hidden=\"true\">→</i>",
        ),
        (
            "const categories = ['Indicatori comunali','Contesti sovrasovracomunali','Temi','Comuni'];",
            "const categories = ['Indicatori comunali','Esploratori','Contesti sovrasovracomunali','Temi','Comuni'];",
        ),
        (
            "const categories = ['Indicatori comunali','Contesti sovracomunali','Temi','Comuni'];",
            "const categories = ['Indicatori comunali','Esploratori','Contesti sovracomunali','Temi','Comuni'];",
        ),
        (
            "      { id:'context-crime', label:'Criminalità e delitti denunciati'",
            "      ...Object.values(OV_SPECIAL_EXPLORERS).map(item => ({ id:`explorer-${item.key}`, label:item.label, description:`${data.themes[item.theme]?.label || 'Economia'} · ${item.year} · ${item.description}`, category:'Esploratori', href:route(item.route), badge:'Atlante', keywords:normalize([item.label,item.shortLabel,item.description,item.source,...(item.searchTerms || [])].join(' ')) })),\n      { id:'context-crime', label:'Criminalità e delitti denunciati'",
        ),
        (
            "badge:`${t.metrics.length} indicatori`",
            "badge:`${t.metrics.length + (t.key === 'economia' ? Object.keys(OV_SPECIAL_EXPLORERS).length : 0)} indicatori`",
        ),
        (
            "const suggested = new Set(['metric-population','metric-income','metric-employmentRate','metric-businessValueAdded','metric-roadInjuries','context-crime','context-brain-drain']);",
            "const suggested = new Set(['metric-population','metric-income','metric-employmentRate','metric-businessValueAdded','explorer-economyActivityAtlas','metric-roadInjuries','context-crime','context-brain-drain']);",
        ),
    )
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)
        elif new in text:
            continue
        elif "sovrasovracomunali" in old:
            continue
        else:
            raise RuntimeError(f"Punto di integrazione Atlante non trovato nel bundle: {old[:80]}")
    path.write_text(text, encoding="utf-8")


def patch_prerendered_home() -> None:
    """Allinea l'HTML prerenderizzato prima dell'esecuzione JavaScript."""
    path = DIST / "index.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace("<span>181 indicatori</span>", "<span>182 indicatori</span>", 1)
    text = text.replace("5 sezioni · 31 indicatori", "5 sezioni · 32 indicatori", 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if not TARGET.exists():
        raise RuntimeError(f"Pagina Atlante non trovata nella build: {TARGET}")
    assert_canonical_dataset_unchanged()
    patch_runtime_bundle()
    patch_prerendered_home()
    synchronize_native_page(DIST, TARGET)
    ensure_sitemap_entries(DIST, (CANONICAL,))
    print("Atlante attività economiche materializzato: shell canonica, ricerca e conteggi pubblici allineati; catalogo 181 invariato.")


if __name__ == "__main__":
    main()
