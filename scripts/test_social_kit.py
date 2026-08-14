#!/usr/bin/env python3
"""Verifica contratto editoriale, palette, layout, dati e provenienza del Social Kit."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"
DIST = KIT / "dist"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def role_elements(root: ET.Element, role: str):
    return [element for element in root.iter() if element.attrib.get("data-role") == role]


def number(element: ET.Element, key: str) -> float:
    return float(element.attrib[key])


def main() -> int:
    errors: list[str] = []

    def fail(message: str) -> None:
        errors.append(message)

    design = load(KIT / "config" / "design-system.json")
    themes = load(KIT / "config" / "themes.json")
    calendar = load(KIT / "config" / "editorial-calendar.json")
    ready = load(KIT / "config" / "social-ready.json")
    recurrences = load(KIT / "config" / "recurrences.json")
    site = load(ROOT / "data" / "site-data.json")
    climate = load(ROOT / "data" / "meteo-clima-minmax-poc.json")
    manifest = load(DIST / "manifest.json")

    if design["version"] != "social-v2.2":
        fail("Versione del design system inattesa")
    if design["format"] != {
        "name": "feed",
        "width": 1080,
        "height": 1350,
        "platforms": ["facebook", "instagram", "linkedin", "x"],
    }:
        fail("Il formato deve essere uno solo, 1080×1350, per i quattro social")
    if design["immutable"]["slides"] != ["current", "history", "change", "questions"]:
        fail("La sequenza delle quattro tavole è stata modificata")
    if design["immutable"]["forbidden_outputs"] != ["pdf", "story"]:
        fail("PDF e storie devono restare esplicitamente vietati")
    if manifest.get("method") != "two-carousels-per-week" or manifest.get("status") != "draft":
        fail("Manifest principale non conforme o non in bozza")
    if manifest.get("posts") != len(calendar["posts"]):
        fail("Il manifest non contiene tutte le voci del calendario")

    # La palette social deve derivare dalla palette canonica già pubblicata dal sito.
    css = (ROOT / "assets" / "original.css").read_text(encoding="utf-8").lower()
    site_themes = ["demografia", "economia", "lavoro", "istruzione", "salute", "mobilita", "abitare", "ambiente", "comunita"]
    for theme_name in site_themes:
        match = re.search(
            rf"\[data-theme={theme_name}\]\{{--theme-color:(#[0-9a-f]{{6}});--theme-soft:(#[0-9a-f]{{6}})\}}",
            css,
        )
        if not match:
            fail(f"Token del sito non trovato: {theme_name}")
            continue
        configured = themes["themes"][theme_name]
        if configured["accent"].lower() != match.group(1) or configured["soft"].lower() != match.group(2):
            fail(f"Palette social diversa dal sito: {theme_name}")

    weekly = Counter()
    for post in calendar["posts"]:
        parsed = datetime.fromisoformat(post["date"])
        weekly[parsed.isocalendar()[:2]] += 1
        if post.get("status") != "draft":
            fail(f"Voce non in bozza: {post['id']}")
        if len(post.get("questions", [])) != 2:
            fail(f"Servono esattamente due domande: {post['id']}")
        if post["theme"] not in themes["themes"]:
            fail(f"Tema senza palette: {post['id']}")
        if post["dataset"] == "site":
            if post["metric"] not in ready["approved_metrics"]:
                fail(f"Indicatore non approvato: {post['metric']}")
            metric = site["metrics"].get(post["metric"])
            if not metric or not metric.get("sourceUrl") or len(metric.get("rows", [])) != 7:
                fail(f"Indicatore privo di fonte o copertura 7/7: {post['metric']}")
        elif post["dataset"] == "climate-minmax":
            approved = ready["approved_datasets"].get("climate-minmax")
            if not approved or post["metric"] not in approved["metrics"]:
                fail(f"Dataset climatico non approvato: {post['id']}")
            if post.get("status") != "draft" or climate.get("status") != "draft":
                fail("Il dataset climatico POC può produrre soltanto bozze")
        else:
            fail(f"Dataset non supportato: {post['dataset']}")
    if any(count > calendar["cadence"]["maximum_posts_per_week"] for count in weekly.values()):
        fail("Il calendario supera due contenuti in una settimana")

    for event in recurrences["events"]:
        if not re.fullmatch(r"\d{2}-\d{2}", event["month_day"]):
            fail(f"Data ricorrenza non valida: {event['id']}")
        if not event["url"].startswith("https://") or event["authority"] not in {"Nazioni Unite", "Organizzazione mondiale della sanità"}:
            fail(f"Ricorrenza priva di fonte ufficiale: {event['id']}")
        for metric_key in event["candidate_metrics"]:
            if metric_key not in ready["approved_metrics"] or metric_key not in site["metrics"]:
                fail(f"Ricorrenza collegata a un indicatore non approvato: {event['id']} / {metric_key}")

    banned_tone = re.compile(r"\b(record|boom|crollo|allarme|virtuos[oaie]?|peggiore|maglia nera|flop|successo|fallimento|bocciatura)\b", re.IGNORECASE)
    expected_logo = design["immutable"]["logo"]
    all_post_manifests = {item["post_id"]: item for item in manifest["items"]}
    for post in calendar["posts"]:
        post_dir = DIST / post["id"]
        item = all_post_manifests.get(post["id"])
        if not item or item.get("method") != "four-slide-carousel" or len(item.get("cards", [])) != 4:
            fail(f"Carosello non composto da quattro tavole: {post['id']}")
            continue
        if item.get("platforms") != ["facebook", "instagram", "linkedin", "x"] or item.get("format") != "1080x1350":
            fail(f"Formato o piattaforme errati: {post['id']}")
        provenance_path = post_dir / "provenienza.json"
        if not provenance_path.exists():
            fail(f"Provenienza mancante: {post['id']}")
            continue
        provenance = load(provenance_path)
        if provenance.get("status") != "draft" or not provenance.get("source_url"):
            fail(f"Provenienza incompleta: {post['id']}")
        if provenance.get("palette", {}).get("accent") != themes["themes"][post["theme"]]["accent"]:
            fail(f"Colore del tema non registrato nella provenienza: {post['id']}")

        soft_seen = False
        for card in item["cards"]:
            svg_path = post_dir / "cards" / f"{card['filename']}.svg"
            png_path = post_dir / "cards" / f"{card['filename']}.png"
            alt_path = post_dir / "alt" / f"{card['filename']}.txt"
            if not svg_path.exists() or not png_path.exists():
                fail(f"Tavola mancante: {post['id']} / {card['filename']}")
                continue
            with Image.open(png_path) as image:
                if image.size != (1080, 1350) or image.format != "PNG":
                    fail(f"PNG non conforme: {png_path}")
            if not alt_path.exists() or len(alt_path.read_text(encoding="utf-8").strip()) < 70:
                fail(f"Testo alternativo insufficiente: {png_path}")
            svg_raw = svg_path.read_text(encoding="utf-8")
            root = ET.fromstring(svg_raw)
            if root.attrib.get("width") != "1080" or root.attrib.get("height") != "1350":
                fail(f"SVG non 1080×1350: {svg_path}")
            if themes["themes"][post["theme"]]["accent"].lower() not in svg_raw.lower():
                fail(f"Accento del tema assente: {svg_path}")
            soft_seen = soft_seen or themes["themes"][post["theme"]]["soft"].lower() in svg_raw.lower()
            logos = role_elements(root, "brand-logo")
            if len(logos) != 1:
                fail(f"Logo mancante o duplicato: {svg_path}")
            else:
                actual = tuple(number(logos[0], key) for key in ("x", "y", "width", "height"))
                wanted = tuple(float(expected_logo[key]) for key in ("x", "y", "width", "height"))
                if actual != wanted:
                    fail(f"Logo spostato o ridimensionato: {svg_path}")
            if len(role_elements(root, "fixed-background")) != 1 or len(role_elements(root, "content-panel")) != 1:
                fail(f"Griglia strutturale incompleta: {svg_path}")
            for text_element in root.iter():
                if not text_element.tag.endswith("text"):
                    continue
                if text_element.attrib.get("text-anchor") == "end" and text_element.attrib.get("data-role") not in {None, "numeric-value"}:
                    fail(f"Allineamento a destra non previsto: {svg_path}")
                if "data-box-width" not in text_element.attrib:
                    continue
                style = text_element.attrib.get("style", "")
                size_match = re.search(r"font-size:(\d+)px", style)
                if not size_match:
                    fail(f"Testo adattivo senza corpo: {svg_path}")
                    continue
                size = int(size_match.group(1))
                width = float(text_element.attrib["data-box-width"])
                height = float(text_element.attrib["data-box-height"])
                lines = ["".join(tspan.itertext()) for tspan in text_element if tspan.tag.endswith("tspan")]
                if not lines:
                    lines = ["".join(text_element.itertext())]
                if any(len(line) * size * 0.56 > width + 1 for line in lines):
                    fail(f"Testo oltre il margine orizzontale: {svg_path} / {text_element.attrib.get('data-role')}")
                if len(lines) * round(size * 1.24) > height + 1:
                    fail(f"Testo oltre il margine verticale: {svg_path} / {text_element.attrib.get('data-role')}")
            rendered = " ".join("".join(element.itertext()) for element in root.iter() if element.tag.endswith("text"))
            if banned_tone.search(rendered):
                fail(f"Lessico valutativo nella grafica: {svg_path}")
            if re.search(r"\b0[1-9]\s*[·-]\s*", rendered):
                fail(f"Numerazione interna del tema visibile: {svg_path}")
        if not soft_seen:
            fail(f"Tonalità soft del tema mai usata nel carosello: {post['id']}")

        platform_texts: dict[str, str] = {}
        for platform in ["master", "facebook", "instagram", "linkedin", "x"]:
            caption = post_dir / "testi" / f"{platform}.txt"
            if not caption.exists():
                fail(f"Testo {platform} mancante: {post['id']}")
                continue
            text = caption.read_text(encoding="utf-8").strip()
            platform_texts[platform] = text
            if banned_tone.search(text):
                fail(f"Lessico valutativo nel testo {platform}: {post['id']}")
            if platform == "x" and len(text) > 280:
                fail(f"Testo X oltre 280 caratteri: {post['id']}")
        if len({platform_texts.get("facebook"), platform_texts.get("instagram"), platform_texts.get("linkedin")}) != 3:
            fail(f"Facebook, Instagram e LinkedIn non hanno testi realmente adattati: {post['id']}")

        if post["dataset"] == "climate-minmax":
            if provenance["current_year"] != 2025 or "2026" in provenance["history"]:
                fail("Il carosello clima include un anno parziale")
            raw_rows = climate["municipalities"]
            for town, values in provenance["current_values"].items():
                if abs(values - raw_rows[town]["latestComplete"][post["metric"]]) > 1e-9:
                    fail(f"Valore climatico alterato: {town}")
            base = mean([
                mean([value for year, value in zip(raw_rows[town]["years"], raw_rows[town][post["metric"]]) if 1975 <= year <= 1984])
                for town in raw_rows
            ])
            current = mean([
                mean([value for year, value in zip(raw_rows[town]["years"], raw_rows[town][post["metric"]]) if 2016 <= year <= 2025])
                for town in raw_rows
            ])
            if abs(provenance["comparison"]["delta"] - (current - base)) > 1e-9:
                fail("Confronto climatico non riproducibile dai dati sorgente")

    forbidden_files = [path for path in DIST.rglob("*") if path.is_file() and (path.suffix.lower() == ".pdf" or "story" in path.name.lower())]
    if forbidden_files:
        fail("Sono stati generati PDF o storie, vietati dal metodo")
    if not (DIST / "index.html").exists():
        fail("Galleria di revisione mancante")

    if errors:
        print("Social Kit: controlli falliti")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Social Kit: {len(calendar['posts'])} caroselli, {len(calendar['posts']) * 4} PNG, palette sito e provenienza verificate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
