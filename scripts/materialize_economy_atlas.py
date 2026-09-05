#!/usr/bin/env python3
"""Materializza l'Atlante Registro Imprese nella shell e nel catalogo pubblico."""
from __future__ import annotations

import json
from pathlib import Path

from site_chrome import ensure_sitemap_entries, synchronize_native_page

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TARGET = DIST / "confronta" / "economia" / "atlante-attivita-economiche" / "index.html"
CANONICAL = "https://osservatorioversilia.it/confronta/economia/atlante-attivita-economiche/"
PUBLIC_VERSION = "v1.30.0"
PUBLIC_UPDATED = "5 settembre 2026"
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


def inject_public_catalog() -> None:
    """Espone l'Atlante come singolo elemento pubblico oltre ai 181 indicatori tabellari."""
    path = DIST / "data" / "site-data.json"
    if not path.exists():
        raise RuntimeError(f"Catalogo runtime non trovato: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["specialExplorers"] = {EXPLORER["key"]: EXPLORER}
    data["version"] = PUBLIC_VERSION
    data["updated"] = PUBLIC_UPDATED
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_runtime_bundle() -> None:
    """Rende il nuovo explorer visibile nei conteggi e nella ricerca globale."""
    path = DIST / "assets" / "app-bundle.js"
    text = path.read_text(encoding="utf-8")

    replacements = (
        (
            "${Object.keys(data.metrics).length} indicatori",
            "${Object.keys(data.metrics).length + Object.keys(data.specialExplorers || {}).length} indicatori",
        ),
        (
            "${theme.metrics.length} indicatori</span><i aria-hidden=\"true\">→</i>",
            "${theme.metrics.length + (theme.key === 'economia' ? Object.keys(data.specialExplorers || {}).length : 0)} indicatori</span><i aria-hidden=\"true\">→</i>",
        ),
        (
            "const categories = ['Indicatori comunali','Contesti sovracomunali','Temi','Comuni'];",
            "const categories = ['Indicatori comunali','Esploratori','Contesti sovracomunali','Temi','Comuni'];",
        ),
        (
            "      { id:'context-crime', label:'Criminalità e delitti denunciati'",
            "      ...Object.values(data.specialExplorers || {}).map(item => ({ id:`explorer-${item.key}`, label:item.label, description:`${data.themes[item.theme]?.label || 'Economia'} · ${item.year} · ${item.description}`, category:'Esploratori', href:route(item.route), badge:'Atlante', keywords:normalize([item.label,item.shortLabel,item.description,item.source,...(item.searchTerms || [])].join(' ')) })),\n      { id:'context-crime', label:'Criminalità e delitti denunciati'",
        ),
        (
            "badge:`${t.metrics.length} indicatori`",
            "badge:`${t.metrics.length + (t.key === 'economia' ? Object.keys(data.specialExplorers || {}).length : 0)} indicatori`",
        ),
        (
            "const suggested = new Set(['metric-population','metric-income','metric-employmentRate','metric-businessValueAdded','metric-roadInjuries','context-crime','context-brain-drain']);",
            "const suggested = new Set(['metric-population','metric-income','metric-employmentRate','metric-businessValueAdded','explorer-economyActivityAtlas','metric-roadInjuries','context-crime','context-brain-drain']);",
        ),
    )
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise RuntimeError(f"Punto di integrazione Atlante non trovato nel bundle: {old[:80]}")
    path.write_text(text, encoding="utf-8")


def patch_prerendered_home() -> None:
    """Allinea anche l'HTML prerenderizzato prima dell'esecuzione JavaScript."""
    path = DIST / "index.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace("<span>181 indicatori</span>", "<span>182 indicatori</span>", 1)
    text = text.replace("5 sezioni · 31 indicatori", "5 sezioni · 32 indicatori", 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if not TARGET.exists():
        raise RuntimeError(f"Pagina Atlante non trovata nella build: {TARGET}")
    inject_public_catalog()
    patch_runtime_bundle()
    patch_prerendered_home()
    synchronize_native_page(DIST, TARGET)
    ensure_sitemap_entries(DIST, (CANONICAL,))
    print("Atlante attività economiche materializzato: shell canonica, catalogo pubblico e ricerca allineati.")


if __name__ == "__main__":
    main()
