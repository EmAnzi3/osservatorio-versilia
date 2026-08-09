#!/usr/bin/env python3
"""Verifica metodo editoriale, coerenza grafica e provenienza del Social Kit."""

from __future__ import annotations

import json
import re
import sys
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"
DIST = KIT / "dist"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def attr_number(element: ET.Element, name: str) -> float:
    return float(element.attrib[name])


def role_elements(root: ET.Element, role: str) -> list[ET.Element]:
    return [element for element in root.iter() if element.attrib.get("data-role") == role]


def visible_text(root: ET.Element) -> str:
    return " ".join("".join(element.itertext()) for element in root.iter() if element.tag.endswith("text"))


def main() -> int:
    errors: list[str] = []
    data = load(ROOT / "data" / "site-data.json")
    design = load(KIT / "config" / "design-system.json")
    themes = load(KIT / "config" / "themes.json")
    calendar = load(KIT / "config" / "editorial-calendar.json")
    questions = load(KIT / "config" / "question-bank.json")
    ready = load(KIT / "config" / "social-ready.json")
    manifest = load(DIST / "manifest.json")

    def fail(message: str) -> None:
        errors.append(message)

    if design["immutable"]["templates"] != ["data", "context"]:
        fail("Il metodo deve avere esattamente i due master data e context")
    if manifest.get("method") != "two-post-week":
        fail("Manifest privo del metodo two-post-week")
    if manifest.get("design_system") != design["version"]:
        fail("Versione del design system non coerente")
    if manifest.get("dataset_version") != data["version"]:
        fail("Versione del dataset non coerente")
    if len(manifest["cards"]) != len(calendar["weeks"]) * 4:
        fail("Ogni settimana deve produrre due post in due formati")

    forbidden = [item.casefold() for item in questions["forbidden"]]
    banned_tone = re.compile(r"\b(record|boom|crollo|allarme|virtuos[oaie]?|peggiore|maglia nera|flop|successo|fallimento|bocciatura)\b", re.IGNORECASE)
    expected_cards: list[dict] = []
    for week in calendar["weeks"]:
        metric_key = week["metric"]
        metric = data["metrics"].get(metric_key)
        if not metric:
            fail(f"Indicatore inesistente: {metric_key}")
            continue
        if metric_key not in ready["approved_metrics"]:
            fail(f"Indicatore non approvato: {metric_key}")
        if metric["meta"]["theme"] != week["theme"]:
            fail(f"Tema errato per {metric_key}")
        if len(metric["rows"]) != 7 or metric["method"].get("coverage") != "7/7":
            fail(f"Copertura non completa per {metric_key}")
        for slot, suffix, key in [("data", "a-dato", "data_question"), ("context", "b-contesto", "context_question")]:
            question = week[key]
            if question.casefold() in forbidden or banned_tone.search(question):
                fail(f"Domanda vietata o valutativa: {week['id']} {slot}")
            wrapped = textwrap.wrap(question, width=49, break_long_words=False, break_on_hyphens=False)
            if len(wrapped) > 2:
                fail(f"Domanda oltre due righe: {week['id']} {slot}")
            expected_cards.append({"id": f"{week['id']}-{suffix}", "slot": slot, "week": week["id"], "metric": metric_key, "theme": week["theme"], "question": question})

    fixed_snapshots: dict[str, dict[str, tuple]] = {}
    logo_cfg = design["immutable"]["logo"]
    for card in expected_cards:
        for size_name, frame in design["formats"].items():
            svg_path = DIST / size_name / f"{card['id']}.svg"
            png_path = DIST / size_name / f"{card['id']}.png"
            if not svg_path.exists():
                fail(f"SVG mancante: {svg_path}")
                continue
            root = ET.parse(svg_path).getroot()
            if root.attrib.get("width") != str(frame["width"]) or root.attrib.get("height") != str(frame["height"]):
                fail(f"Dimensioni errate: {svg_path}")

            logo = role_elements(root, "brand-logo")
            if len(logo) != 1:
                fail(f"Logo mancante o duplicato: {svg_path}")
            else:
                geometry = tuple(attr_number(logo[0], key) for key in ("x", "y", "width", "height"))
                expected_geometry = tuple(float(logo_cfg[key]) for key in ("x", "y", "width", "height"))
                if geometry != expected_geometry:
                    fail(f"Dimensione o posizione logo modificata: {svg_path}")

            background = role_elements(root, "fixed-background")
            motifs = role_elements(root, "fixed-motif")
            header_rule = role_elements(root, "header-rule")
            snapshot = {
                "background": tuple(sorted(background[0].attrib.items())) if background else (),
                "motifs": tuple(tuple(sorted(item.attrib.items())) for item in motifs),
                "header_rule": tuple(sorted(header_rule[0].attrib.items())) if header_rule else (),
            }
            if size_name not in fixed_snapshots:
                fixed_snapshots[size_name] = snapshot
            elif snapshot != fixed_snapshots[size_name]:
                fail(f"Sfondo o testata non costanti: {svg_path}")

            for role, expected_x in [("theme-label", 72), ("post-title", 72), ("post-description", 72), ("source", 72), ("site-domain", 72)]:
                elements = role_elements(root, role)
                if not elements or any(attr_number(element, "x") != expected_x for element in elements):
                    fail(f"Allineamento {role} incoerente: {svg_path}")
            question_panel = role_elements(root, "question-panel")
            if len(question_panel) != 1:
                fail(f"Blocco domanda mancante: {svg_path}")
            else:
                expected = frame["question"]
                actual = tuple(attr_number(question_panel[0], key) for key in ("x", "y", "width", "height"))
                wanted = tuple(float(expected[key]) for key in ("x", "y", "width", "height"))
                if actual != wanted:
                    fail(f"Blocco domanda spostato o ridimensionato: {svg_path}")
            content_panel = role_elements(root, "content-panel")
            if len(content_panel) != 1:
                fail(f"Pannello contenuto mancante: {svg_path}")
            else:
                expected = frame["content"]
                actual = tuple(attr_number(content_panel[0], key) for key in ("x", "y", "width", "height"))
                wanted = tuple(float(expected[key]) for key in ("x", "y", "width", "height"))
                if actual != wanted:
                    fail(f"Pannello contenuto spostato o ridimensionato: {svg_path}")

            for element in root.iter():
                anchor = element.attrib.get("text-anchor")
                if anchor == "middle":
                    fail(f"Testo centrato non ammesso: {svg_path}")
                if anchor == "end" and element.attrib.get("data-role") != "numeric-value":
                    fail(f"Allineamento a destra riservato ai numeri: {svg_path}")

            rendered_text = visible_text(root)
            if f">{card['metric']}<" in svg_path.read_text(encoding="utf-8") or card["metric"] in rendered_text:
                fail(f"Chiave tecnica visibile: {svg_path}")
            if re.search(r"\b0[1-9]\s*[·-]\s*", rendered_text):
                fail(f"Numerazione interna del tema visibile: {svg_path}")
            if banned_tone.search(rendered_text):
                fail(f"Lessico valutativo nella grafica: {svg_path}")

            if card["slot"] == "data":
                tracks = role_elements(root, "bar-track")
                numeric = [item for item in role_elements(root, "numeric-value") if item.attrib.get("data-left")]
                if len(tracks) < 7 or len(numeric) != 7:
                    fail(f"Geometria confronto incompleta: {svg_path}")
                else:
                    for index, (track, value) in enumerate(zip(tracks[:7], numeric), start=1):
                        if attr_number(track, "x") + attr_number(track, "width") + 24 > attr_number(value, "data-left"):
                            fail(f"Barra e numero interferiscono: {svg_path}, riga {index}")

            if manifest.get("png") and not png_path.exists():
                fail(f"PNG mancante: {png_path}")

        provenance = DIST / "provenance" / f"{card['id']}.json"
        alt = DIST / "alt" / f"{card['id']}.txt"
        if not provenance.exists():
            fail(f"Provenienza mancante: {card['id']}")
        else:
            item = load(provenance)
            if item.get("design_system") != design["version"] or not item.get("source_url"):
                fail(f"Provenienza incompleta: {card['id']}")
        if not alt.exists() or len(alt.read_text(encoding="utf-8").strip()) < 80:
            fail(f"ALT mancante o insufficiente: {card['id']}")
        for platform in ["master", "facebook", "instagram", "linkedin", "x"]:
            caption = DIST / "captions" / f"{card['id']}-{platform}.txt"
            if not caption.exists():
                fail(f"Testo {platform} mancante: {card['id']}")
                continue
            text = caption.read_text(encoding="utf-8").strip()
            if banned_tone.search(text):
                fail(f"Lessico valutativo nel testo {platform}: {card['id']}")
            if platform == "x" and len(text) > 280:
                fail(f"Testo X oltre 280 caratteri: {card['id']}")

    if not (DIST / "index.html").exists():
        fail("Galleria mancante")
    if manifest.get("linkedin_pdf") and not (DIST / "linkedin-carousel.pdf").exists():
        fail("PDF LinkedIn mancante")

    if errors:
        print("Social Kit: controlli falliti")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Social Kit: {len(calendar['weeks'])} settimane, 2 post/settimana, 2 formati — metodo {design['version']} verificato")
    return 0


if __name__ == "__main__":
    sys.exit(main())

