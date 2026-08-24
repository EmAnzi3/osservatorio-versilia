#!/usr/bin/env python3
"""Quality gate del pacchetto Social Kit generato dal piano settimanale."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"
DIST = KIT / "dist"
BANNED = re.compile(r"\b(record|boom|crollo|allarme|virtuos[oaie]?|peggiore|maglia nera|flop|successo|fallimento|bocciatura)\b", re.IGNORECASE)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def role_elements(root: ET.Element, role: str):
    return [element for element in root.iter() if element.attrib.get("data-role") == role]


def visible_text(root: ET.Element) -> str:
    return " ".join("".join(element.itertext()) for element in root.iter() if element.tag.endswith("text"))


def check_fitted_text(svg_path: Path, root: ET.Element, errors: list[str]) -> None:
    for element in root.iter():
        if not element.tag.endswith("text") or "data-box-width" not in element.attrib:
            continue
        style = element.attrib.get("style", "")
        match = re.search(r"font-size:(\d+)px", style)
        if not match:
            errors.append(f"Testo adattivo senza font-size: {svg_path}")
            continue
        size = int(match.group(1))
        width = float(element.attrib["data-box-width"])
        height = float(element.attrib["data-box-height"])
        lines = ["".join(child.itertext()) for child in element if child.tag.endswith("tspan")]
        if not lines:
            lines = ["".join(element.itertext())]
        if any(len(line) * size * 0.56 > width + 1 for line in lines):
            errors.append(f"Testo oltre il box orizzontale: {svg_path} / {element.attrib.get('data-role')}")
        if len(lines) * round(size * 1.24) > height + 1:
            errors.append(f"Testo oltre il box verticale: {svg_path} / {element.attrib.get('data-role')}")


def main() -> int:
    errors: list[str] = []
    plan = load(DIST / "week.json")
    manifest = load(DIST / "manifest.json")
    design = load(KIT / "config" / "design-system.json")
    themes = load(KIT / "config" / "themes.json")

    if plan.get("version") != "social-week-v3":
        errors.append("week.json non usa social-week-v3")
    if manifest.get("method") != "weekly-four-slide-carousels":
        errors.append("Metodo del manifest settimanale inatteso")
    if manifest.get("design_system") != design.get("version"):
        errors.append("Design system del manifest non coerente")
    if manifest.get("scheduled_count") != len(plan.get("scheduled", [])):
        errors.append("Conteggio uscite pianificate non coerente")
    if manifest.get("scheduled_count", 0) > plan.get("weekly_budget", 2):
        errors.append("Budget settimanale superato")
    if manifest.get("posts", 0) + len(manifest.get("manual_required", [])) != manifest.get("scheduled_count"):
        errors.append("Uscite generate + manuali non coincidono con il piano")
    if manifest.get("slides") != manifest.get("posts", 0) * 4:
        errors.append("Ogni carosello deve avere quattro tavole")
    if design.get("format") != {
        "name": "feed",
        "width": 1080,
        "height": 1350,
        "platforms": ["facebook", "instagram", "linkedin", "x"],
    }:
        errors.append("Il Social Kit deve usare un unico formato 1080×1350 per i quattro social")
    if design.get("immutable", {}).get("forbidden_outputs") != ["pdf", "story"]:
        errors.append("PDF e story devono restare vietati")

    expected_logo = design["immutable"]["logo"]
    for item in manifest.get("items", []):
        post_dir = DIST / item["post_id"]
        if item.get("method") != "four-slide-carousel" or len(item.get("cards", [])) != 4:
            errors.append(f"Carosello incompleto: {item.get('post_id')}")
            continue
        if item.get("format") != "1080x1350" or item.get("platforms") != ["facebook", "instagram", "linkedin", "x"]:
            errors.append(f"Formato/piattaforme errati: {item['post_id']}")
        provenance_path = post_dir / "provenienza.json"
        if not provenance_path.exists():
            errors.append(f"Provenienza mancante: {item['post_id']}")
            continue
        provenance = load(provenance_path)
        if not provenance.get("source_url") or len(provenance.get("current_values", {})) != 7:
            errors.append(f"Fonte o copertura 7/7 mancante: {item['post_id']}")
        theme = provenance.get("theme")
        if theme not in themes["themes"]:
            errors.append(f"Tema non canonico: {item['post_id']}")
            continue
        accent = themes["themes"][theme]["accent"].lower()
        if provenance.get("palette", {}).get("accent", "").lower() != accent:
            errors.append(f"Palette non coerente: {item['post_id']}")

        for card in item["cards"]:
            stem = card["filename"]
            png_path = post_dir / "cards" / f"{stem}.png"
            svg_path = post_dir / "cards" / f"{stem}.svg"
            alt_path = post_dir / "alt" / f"{stem}.txt"
            if not png_path.exists() or not svg_path.exists():
                errors.append(f"Tavola mancante: {item['post_id']} / {stem}")
                continue
            with Image.open(png_path) as image:
                if image.size != (1080, 1350) or image.format != "PNG":
                    errors.append(f"PNG non conforme: {png_path}")
            if not alt_path.exists() or len(alt_path.read_text(encoding="utf-8").strip()) < 70:
                errors.append(f"ALT insufficiente: {item['post_id']} / {stem}")
            raw = svg_path.read_text(encoding="utf-8")
            root = ET.fromstring(raw)
            if root.attrib.get("width") != "1080" or root.attrib.get("height") != "1350":
                errors.append(f"SVG non 1080×1350: {svg_path}")
            if accent not in raw.lower():
                errors.append(f"Colore tema assente: {svg_path}")
            logos = role_elements(root, "brand-logo")
            if len(logos) != 1:
                errors.append(f"Logo mancante/duplicato: {svg_path}")
            else:
                actual = tuple(float(logos[0].attrib[key]) for key in ("x", "y", "width", "height"))
                wanted = tuple(float(expected_logo[key]) for key in ("x", "y", "width", "height"))
                if actual != wanted:
                    errors.append(f"Logo spostato o ridimensionato: {svg_path}")
            if len(role_elements(root, "fixed-background")) != 1 or len(role_elements(root, "content-panel")) != 1:
                errors.append(f"Griglia fissa incompleta: {svg_path}")
            check_fitted_text(svg_path, root, errors)
            rendered = visible_text(root)
            if BANNED.search(rendered):
                errors.append(f"Lessico valutativo nella grafica: {svg_path}")
            if re.search(r"\b0[1-9]\s*[·-]\s*", rendered):
                errors.append(f"Chiave/numerazione tecnica visibile: {svg_path}")

        platform_texts: dict[str, str] = {}
        for platform in ["master", "facebook", "instagram", "linkedin", "x"]:
            path = post_dir / "testi" / f"{platform}.txt"
            if not path.exists():
                errors.append(f"Copy {platform} mancante: {item['post_id']}")
                continue
            text = path.read_text(encoding="utf-8").strip()
            platform_texts[platform] = text
            if BANNED.search(text):
                errors.append(f"Lessico valutativo nel copy {platform}: {item['post_id']}")
            if platform == "x" and len(text) > 280:
                errors.append(f"Copy X oltre 280 caratteri: {item['post_id']}")
        if len({platform_texts.get("facebook"), platform_texts.get("instagram"), platform_texts.get("linkedin")}) != 3:
            errors.append(f"Copy Facebook/Instagram/LinkedIn non differenziati: {item['post_id']}")

    forbidden = [path for path in DIST.rglob("*") if path.is_file() and (path.suffix.lower() == ".pdf" or "story" in path.name.lower())]
    if forbidden:
        errors.append("Il pacchetto contiene PDF o story")
    for required in [DIST / "README.md", DIST / "index.html", DIST / "week.json"]:
        if not required.exists():
            errors.append(f"File pacchetto mancante: {required.name}")

    if errors:
        print("Social Kit settimanale: controlli falliti")
        for error in errors:
            print(f"- {error}")
        return 1

    manual = len(manifest.get("manual_required", []))
    print(
        f"Social Kit settimanale: {manifest['posts']} caroselli, {manifest['slides']} PNG, "
        f"budget rispettato, {manual} interventi manuali segnalati"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
