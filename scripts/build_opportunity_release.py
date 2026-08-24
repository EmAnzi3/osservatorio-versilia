#!/usr/bin/env python3
"""Materializza /opportunita/ per la pubblicazione nell'Osservatorio."""
from __future__ import annotations

import argparse
import copy
import json
import re
import tempfile
from pathlib import Path

import build_opportunity_preview_v04 as route_builder
import build_opportunity_preview_v043 as radar_v043
import materialize_opportunity_release_favicons as release_favicons
from site_chrome import ensure_sitemap_entries

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "opportunity-release.json"
DEFAULT_DIST = ROOT / "dist"
TARGET_ROUTE = "opportunita"
PUBLIC_URL = "https://osservatorioversilia.it/opportunita/"
PUBLIC_VERSION = "Radar v0.4.3"
PUBLIC_DESCRIPTION = (
    "Bandi, avvisi, incentivi e programmi utili ai Comuni della Versilia, "
    "con scadenze, requisiti e rimando alla fonte ufficiale."
)
FORBIDDEN_VISIBLE = (
    "Anteprima tecnica",
    "Anteprima v0.4.3",
    "Collaudo",
    "non pubblicata",
    "revisione interna",
    "prototipo",
    "Audit indipendente",
    "capture rate",
    "buchi baseline",
    "fonti di controllo",
    "Famiglie presidiate",
    "Rete di raccolta",
    "Quality gate",
    "coverageHold",
    "Le schede sono ordinate per scadenza",
    "Colore e segno grafico",
)


def _social_metadata() -> str:
    image = "https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg"
    return f'''  <meta property="og:title" content="Radar Opportunità · Osservatorio Versilia">
  <meta property="og:description" content="{PUBLIC_DESCRIPTION}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{PUBLIC_URL}">
  <meta property="og:site_name" content="Osservatorio Versilia">
  <meta property="og:locale" content="it_IT">
  <meta property="og:image" content="{image}">
  <meta property="og:image:alt" content="Versilia e Alpi Apuane">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Radar Opportunità · Osservatorio Versilia">
  <meta name="twitter:description" content="{PUBLIC_DESCRIPTION}">
  <meta name="twitter:site" content="@OssVersilia">
  <meta name="twitter:image" content="{image}">
  <meta name="twitter:image:alt" content="Versilia e Alpi Apuane">
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"CollectionPage","name":"Radar Opportunità","url":"{PUBLIC_URL}","description":"{PUBLIC_DESCRIPTION}","isPartOf":{{"@type":"WebSite","name":"Osservatorio Versilia","url":"https://osservatorioversilia.it/"}}}}</script>'''


def _build_v043_from_local_assets(payload_path: Path, dist: Path) -> tuple[Path, dict]:
    """Costruisce la UI v0.4.3 senza alcuna risoluzione favicon via rete."""
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    rendered_payload = copy.deepcopy(payload)
    provenance = release_favicons.materialize(rendered_payload, dist)
    release_favicons.apply_to_payload(rendered_payload, provenance)

    route_builder.TARGET_ROUTE = TARGET_ROUTE
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(rendered_payload, handle, ensure_ascii=False)
        temporary = Path(handle.name)
    try:
        target = route_builder.build(temporary, dist)
    finally:
        temporary.unlink(missing_ok=True)

    text = target.read_text(encoding="utf-8")
    text = text.replace("v0.4.2", "v0.4.3")
    source_select = '<select data-op-source>' + radar_v043._source_options(rendered_payload) + '</select>'
    text, replacements = re.subn(
        r'<select data-op-source>.*?</select>',
        source_select,
        text,
        count=1,
        flags=re.S,
    )
    if replacements != 1:
        raise RuntimeError("Filtro Fonte non trovato nella release v0.4.3")
    target.write_text(text, encoding="utf-8")

    check = target.read_text(encoding="utf-8")
    if "Anteprima v0.4.3" not in check:
        raise RuntimeError("Renderer v0.4.3 non materializzato")
    if "Tutte le fonti monitorate" not in check:
        raise RuntimeError("Filtro Fonti completo assente")
    if "../assets/source-favicons/" not in check:
        raise RuntimeError("Favicon locali non collegati alla release")
    return target, rendered_payload


def _clean_public_markup(text: str, reference: str) -> str:
    text = text.replace(
        "<title>Anteprima Radar Opportunità · Osservatorio Versilia</title>",
        "<title>Radar Opportunità · Osservatorio Versilia</title>",
        1,
    )
    text = re.sub(
        r'<meta\s+name="description"\s+content="[^"]*Radar Opportunità[^"]*"\s*/?>',
        f'<meta name="description" content="{PUBLIC_DESCRIPTION}">',
        text,
        count=1,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\s*<meta\s+name="robots"\s+content="noindex,nofollow,noarchive"\s*/?>',
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )
    if 'rel="canonical"' not in text:
        text = text.replace("</head>", f'  <link rel="canonical" href="{PUBLIC_URL}">\n{_social_metadata()}\n</head>', 1)
    else:
        text = re.sub(
            r'<link\b[^>]*rel="canonical"[^>]*>',
            f'<link rel="canonical" href="{PUBLIC_URL}">',
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        if 'property="og:title"' not in text:
            text = text.replace("</head>", _social_metadata() + "\n</head>", 1)

    text = text.replace("Radar opportunità · Anteprima v0.4.3", "Radar opportunità", 1)
    public_intro = (
        '<p>Bandi, avvisi, incentivi e programmi con un <strong>ruolo operativo documentato</strong> '
        'per almeno un Comune della Versilia. Ogni scheda rimanda alla fonte ufficiale per requisiti e dettagli.</p>'
    )
    text, hero_replacements = re.subn(
        r'(<section class="editorial-hero page-width op-preview-hero">.*?<h1>.*?</h1>)\s*<p>.*?</p>',
        rf'\1\n      {public_intro}',
        text,
        count=1,
        flags=re.DOTALL,
    )
    if hero_replacements != 1:
        raise RuntimeError("Testo introduttivo Radar pubblico non individuato")
    text = re.sub(r'\s*<div class="op-preview-banner">.*?</div>', "", text, count=1, flags=re.DOTALL)
    text = text.replace("Radar / UI v0.4.3", PUBLIC_VERSION, 1)
    text = text.replace(
        "Aperte, misure a sportello e procedure annunciate. La copertura è verificata anche con fonti di controllo che non alimentano il radar.",
        "Una sintesi delle opportunità disponibili e delle fonti pubbliche monitorate.",
    )
    text = re.sub(
        r'<small>Rete di raccolta</small><strong>([^<]+)</strong><span>.*?</span>',
        r'<small>Fonti monitorate</small><strong>\1</strong><span>Fonti pubbliche e istituzionali</span>',
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        r'<small>Famiglie presidiate</small><strong>[^<]+</strong><span>.*?</span>',
        '<small>Comuni coperti</small><strong>7</strong><span>Tutti i Comuni della Versilia</span>',
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(r'\s*<div class="op-audit-summary">.*?</div>', "", text, count=1, flags=re.DOTALL)
    text = text.replace(
        "Il menu Fonte mostra l’intera rete monitorata, anche quando una fonte non produce opportunità correnti.",
        "Filtra per Comune, stato, modalità, fonte o ricerca libera.",
    )
    text = text.replace(
        "Il menu Fonte mostra l'intera rete monitorata, anche quando una fonte non produce opportunità correnti.",
        "Filtra per Comune, stato, modalità, fonte o ricerca libera.",
    )
    text = re.sub(
        r'(<section class="method-detail page-width" aria-label="Elenco opportunità">\s*<div class="section-heading"><div><span class="section-number">03</span><h2>Opportunità aperte</h2></div>)<p>.*?</p>(</div>)',
        r'\1\2',
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = text.replace(
        "Il conteggio riguarda le fonti attualmente integrate nel prototipo.",
        "Una sintesi delle opportunità disponibili e delle fonti pubbliche monitorate.",
    )
    if reference not in text:
        raise RuntimeError(f"Data di riferimento {reference} non esposta nella pagina")
    return text


def build(payload_path: Path, dist: Path) -> Path:
    target, payload = _build_v043_from_local_assets(payload_path, dist)
    reference_iso = str(payload.get("referenceDate") or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", reference_iso):
        raise RuntimeError("referenceDate Radar assente o non valida")
    year, month, day = reference_iso.split("-")
    reference = f"{day}/{month}/{year}"

    text = _clean_public_markup(target.read_text(encoding="utf-8"), reference)
    target.write_text(text, encoding="utf-8")
    ensure_sitemap_entries(dist, (PUBLIC_URL,))

    final = target.read_text(encoding="utf-8")
    visible = re.sub(r"<script\b.*?</script>", " ", final, flags=re.I | re.S)
    visible = re.sub(r"<style\b.*?</style>", " ", visible, flags=re.I | re.S)
    visible = re.sub(r"<[^>]+>", " ", visible)
    visible = " ".join(visible.split())
    bad = [token for token in FORBIDDEN_VISIBLE if token.lower() in visible.lower()]
    if bad:
        raise RuntimeError(f"Testi tecnici ancora esposti nel Radar pubblico: {bad}")
    if 'name="robots" content="noindex' in final.lower():
        raise RuntimeError("Il Radar pubblico non può restare noindex")
    if final.count(f'rel="canonical" href="{PUBLIC_URL}"') != 1:
        raise RuntimeError("Canonical Radar assente o duplicata")
    if "Tutte le fonti monitorate" not in final:
        raise RuntimeError("Filtro Fonti completo assente")
    total = len(payload.get("opportunities") or [])
    if final.count("data-opportunity-card") != total:
        raise RuntimeError(f"Card Radar incoerenti: HTML={final.count('data-opportunity-card')} payload={total}")
    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
    if sitemap.count(PUBLIC_URL) != 1:
        raise RuntimeError("/opportunita/ deve comparire una sola volta nella sitemap")
    print(f"Radar pubblico materializzato: {total} opportunità · dati {reference} · {PUBLIC_VERSION}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()
    build(args.data, args.dist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
