#!/usr/bin/env python3
"""Genera due post coordinati per ogni settimana editoriale."""

from __future__ import annotations

import argparse
import base64
import html
import json
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"
DIST = KIT / "dist"
SITE_URL = "https://osservatorioversilia.it"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def fmt_it(value: float, decimals: int = 0) -> str:
    raw = f"{value:,.{decimals}f}"
    return raw.replace(",", "X").replace(".", ",").replace("X", ".")


def format_value(value: float, unit: str, compact: bool = False) -> str:
    if unit == "percent":
        return f"{fmt_it(value, 1)}%"
    if unit == "currency":
        return f"{fmt_it(value, 0)} €"
    if unit in {"per1000", "per10k"}:
        return fmt_it(value, 1) if compact else f"{fmt_it(value, 1)} ogni {'1.000' if unit == 'per1000' else '10.000'}"
    if unit == "minutes":
        return f"{fmt_it(value, 1)} min"
    if unit in {"number", "people"}:
        return fmt_it(value, 0 if float(value).is_integer() else 1)
    return fmt_it(value, 1)


def unit_label(unit: str) -> str:
    return {
        "percent": "percentuale",
        "currency": "euro",
        "per1000": "ogni 1.000 residenti",
        "per10k": "ogni 10.000 residenti",
        "number": "valore assoluto",
        "people": "persone",
        "minutes": "minuti",
    }.get(unit, unit)


def lines(text: str, width: int, max_lines: int | None = None) -> list[str]:
    wrapped = textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
        replace_whitespace=True,
    ) or [""]
    if max_lines and len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = wrapped[-1].rstrip(" .") + "…"
    return wrapped


def svg_text(
    text: str,
    x: int,
    y: int,
    css_class: str,
    width: int,
    line_height: int,
    max_lines: int,
    role: str | None = None,
) -> str:
    role_attr = f' data-role="{role}"' if role else ""
    tspans = []
    for index, line in enumerate(lines(text, width, max_lines)):
        tspans.append(f'<tspan x="{x}" dy="{0 if index == 0 else line_height}">{esc(line)}</tspan>')
    return f'<text{role_attr} x="{x}" y="{y}" class="{css_class}">' + "".join(tspans) + "</text>"


def logo_uri() -> str:
    raw = (ROOT / "assets" / "brand-mark.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")


def estimated_width(text: str, size: int) -> float:
    return len(text) * size * 0.58


def normalized_rows(metric: dict[str, Any], use_normalized: bool) -> tuple[list[dict[str, Any]], str, str]:
    rows = []
    unit = metric["meta"]["unit"]
    label = metric["meta"]["label"]
    for source_row in sorted(metric["rows"], key=lambda item: item["town"]):
        row = dict(source_row)
        if use_normalized:
            normalized = row.get("normalized")
            if not normalized:
                raise ValueError(f"{metric['meta']['key']} non dispone di misura normalizzata per tutti i Comuni")
            row["displayValue"] = normalized["value"]
            unit = normalized["unit"]
            label = normalized["label"]
        else:
            row["displayValue"] = row["value"]
        rows.append(row)
    return rows, unit, label


def aggregate_for(metric: dict[str, Any], use_normalized: bool) -> dict[str, Any] | None:
    if use_normalized:
        return metric.get("normalizedAggregate")
    return metric.get("aggregate")


def question_for(question_bank: dict[str, Any], theme: str, slot: str) -> str:
    return question_bank.get("themes", {}).get(theme, {}).get(slot) or question_bank["fallback"][slot]


def build_weeks(args: argparse.Namespace, calendar: dict[str, Any], questions: dict[str, Any]) -> list[dict[str, Any]]:
    if args.theme or args.metric:
        if not args.theme or not args.metric:
            raise ValueError("--theme e --metric devono essere usati insieme")
        return [{
            "id": args.week_id or "settimana-prova",
            "theme": args.theme,
            "metric": args.metric,
            "use_normalized": args.normalized,
            "data_question": args.data_question or question_for(questions, args.theme, "data"),
            "context_question": args.context_question or question_for(questions, args.theme, "context"),
        }]
    return calendar["weeks"]


def expand_cards(weeks: list[dict[str, Any]], data: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for week in weeks:
        metric = data["metrics"].get(week["metric"])
        if not metric:
            raise ValueError(f"Indicatore inesistente: {week['metric']}")
        if metric["meta"]["theme"] != week["theme"]:
            raise ValueError(f"Il tema {week['theme']} non corrisponde all’indicatore {week['metric']}")
        short = metric["meta"].get("shortLabel") or metric["meta"]["label"]
        cards.extend([
            {
                "id": f"{week['id']}-a-dato",
                "week": week["id"],
                "slot": "data",
                "theme": week["theme"],
                "metric": week["metric"],
                "use_normalized": bool(week.get("use_normalized")),
                "title": f"{short}\nI sette Comuni a confronto",
                "question": week["data_question"],
            },
            {
                "id": f"{week['id']}-b-contesto",
                "week": week["id"],
                "slot": "context",
                "theme": week["theme"],
                "metric": week["metric"],
                "use_normalized": bool(week.get("use_normalized")),
                "title": f"{short}\nCome leggere il dato",
                "question": week["context_question"],
            },
        ])
    return cards


def svg_start(width: int, height: int, brand: dict[str, str]) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        "<style>",
        "@font-face{font-family:Geist;src:url('../../../assets/fonts/geist-latin.woff2') format('woff2');font-weight:100 900}",
        "@font-face{font-family:Geist Mono;src:url('../../../assets/fonts/geist-mono-latin.woff2') format('woff2');font-weight:100 900}",
        f"text{{font-family:Geist,Arial,sans-serif;fill:{brand['ink']}}}",
        ".brand{font-size:29px;font-weight:800}.brand-sub{font-size:16px;font-weight:600;fill:#526B7A}",
        ".theme{font-size:18px;font-weight:800;letter-spacing:3px}.title{font-size:56px;font-weight:720;letter-spacing:-1.8px}",
        ".description{font-size:25px;font-weight:450;fill:#526B7A}.section{font-size:16px;font-weight:800;letter-spacing:2.4px}",
        ".label{font-size:20px;font-weight:700}.body{font-size:22px;font-weight:470;fill:#365469}.small{font-size:16px;font-weight:540;fill:#526B7A}",
        ".number{font-size:31px;font-weight:760}.number-large{font-size:64px;font-weight:770;letter-spacing:-2px}",
        ".question-label{font-size:17px;font-weight:800;letter-spacing:2.8px;fill:#FFFFFF}.question{font-size:28px;font-weight:720;fill:#FFFFFF}",
        ".footer{font-size:16px;font-weight:570;fill:#526B7A}.mono{font-family:Geist Mono,monospace}",
        "</style>",
        f'<rect data-role="fixed-background" width="{width}" height="{height}" fill="{brand["paper"]}"/>',
        f'<circle data-role="fixed-motif" cx="1000" cy="95" r="245" fill="#E7ECE8" opacity=".82"/>',
        f'<circle data-role="fixed-motif" cx="45" cy="{height - 30}" r="220" fill="#EBE7DC" opacity=".78"/>',
    ]


def render_frame(
    parts: list[str],
    card: dict[str, Any],
    metric: dict[str, Any],
    theme: dict[str, str],
    design: dict[str, Any],
    size_name: str,
    description: str,
) -> dict[str, Any]:
    immutable = design["immutable"]
    frame = design["formats"][size_name]
    logo = immutable["logo"]
    brand_text = immutable["brand_text"]
    parts.extend([
        f'<image data-role="brand-logo" href="{logo_uri()}" x="{logo["x"]}" y="{logo["y"]}" width="{logo["width"]}" height="{logo["height"]}"/>',
        f'<text data-role="brand-name" x="{brand_text["x"]}" y="{brand_text["y"]}" class="brand">Osservatorio Versilia</text>',
        f'<text data-role="brand-subtitle" x="{brand_text["x"]}" y="{brand_text["y"] + 26}" class="brand-sub">Dati pubblici, lettura accessibile</text>',
        f'<line data-role="header-rule" x1="72" x2="1008" y1="{frame["rule_y"]}" y2="{frame["rule_y"]}" stroke="{immutable["line"]}" stroke-width="2"/>',
        f'<line data-role="header-accent" x1="72" x2="292" y1="{frame["rule_y"]}" y2="{frame["rule_y"]}" stroke="{theme["accent"]}" stroke-width="5" stroke-linecap="round"/>',
        f'<text data-role="theme-label" x="72" y="{frame["theme_y"]}" class="theme" fill="{theme["accent"]}">{esc(theme["label"].upper())}</text>',
    ])
    title_width = 31 if size_name == "feed" else 34
    explicit_lines = card["title"].split("\n")
    title_lines = explicit_lines if len(explicit_lines) == 2 else lines(card["title"], title_width, 2)
    for index, line in enumerate(title_lines):
        parts.append(f'<text data-role="post-title" x="72" y="{frame["title_y"] + index * 62}" class="title">{esc(line)}</text>')
    parts.append(svg_text(description, 72, frame["description_y"], "description", 65, 33, 2, "post-description"))
    return frame


def render_data_panel(
    parts: list[str],
    card: dict[str, Any],
    metric: dict[str, Any],
    theme: dict[str, str],
    frame: dict[str, Any],
) -> dict[str, Any]:
    box = frame["content"]
    rows, unit, label = normalized_rows(metric, card["use_normalized"])
    aggregate = aggregate_for(metric, card["use_normalized"])
    x, y, w, h = box["x"], box["y"], box["width"], box["height"]
    parts.extend([
        f'<rect data-role="content-panel" x="{x}" y="{y}" width="{w}" height="{h}" rx="30" fill="#FFFAF1" stroke="#C9D5D5" stroke-width="2"/>',
        f'<text data-role="panel-heading" x="{x + 36}" y="{y + 43}" class="section" fill="{theme["accent"]}">SETTE COMUNI · ORDINE ALFABETICO</text>',
    ])
    row_start = y + (82 if h < 600 else 105)
    step = 44 if h < 600 else 76
    label_x = x + 36
    bar_x = x + 300
    value_x = x + w - 36
    bar_w = 430
    maximum = max(row["displayValue"] for row in rows) or 1
    values: dict[str, float] = {}
    for index, row in enumerate(rows):
        cy = row_start + index * step
        value = float(row["displayValue"])
        value_text = format_value(value, unit, compact=True)
        font_size = min(31, max(23, int(165 / max(1, len(value_text)) / 0.58)))
        value_left = value_x - estimated_width(value_text, font_size)
        parts.extend([
            f'<text data-role="town-label" x="{label_x}" y="{cy + 20}" class="label">{esc(row["town"])}</text>',
            f'<rect data-role="bar-track" x="{bar_x}" y="{cy}" width="{bar_w}" height="26" rx="13" fill="#FFFFFF" stroke="{theme["line"]}"/>',
            f'<rect data-role="bar-fill" x="{bar_x}" y="{cy}" width="{max(2, bar_w * value / maximum):.1f}" height="26" rx="13" fill="{theme["accent"]}"/>',
            f'<text data-role="numeric-value" data-left="{value_left:.1f}" x="{value_x}" y="{cy + 22}" font-size="{font_size}" font-weight="760" text-anchor="end">{esc(value_text)}</text>',
        ])
        values[row["town"]] = value
    if aggregate:
        divider_y = y + h - 66
        parts.extend([
            f'<line x1="{x + 36}" x2="{x + w - 36}" y1="{divider_y}" y2="{divider_y}" stroke="{theme["line"]}"/>',
            f'<text x="{x + 36}" y="{divider_y + 38}" class="small">{esc(aggregate["label"])}</text>',
            f'<text data-role="numeric-value" x="{value_x}" y="{divider_y + 40}" class="number" text-anchor="end">{esc(format_value(aggregate["value"], unit, compact=True))}</text>',
        ])
    return {"values": values, "unit": unit, "label": label, "aggregate": aggregate}


def benchmark_is_compatible(metric: dict[str, Any]) -> bool:
    benchmark = metric["meta"].get("benchmark")
    return bool(benchmark and str(benchmark.get("year")) == str(metric["meta"].get("year")))


def render_context_panel(
    parts: list[str],
    card: dict[str, Any],
    metric: dict[str, Any],
    theme: dict[str, str],
    frame: dict[str, Any],
) -> dict[str, Any]:
    box = frame["content"]
    x, y, w, h = box["x"], box["y"], box["width"], box["height"]
    meta = metric["meta"]
    method = metric["method"]
    unit = meta["unit"]
    parts.append(f'<rect data-role="content-panel" x="{x}" y="{y}" width="{w}" height="{h}" rx="30" fill="#FFFAF1" stroke="#C9D5D5" stroke-width="2"/>')
    result: dict[str, Any] = {"unit": unit}
    if benchmark_is_compatible(metric):
        benchmark = meta["benchmark"]
        items = [("Versilia", metric["aggregate"]["value"]), ("Toscana", benchmark["tuscany"])]
        if benchmark.get("italy") is not None:
            items.append(("Italia", benchmark["italy"]))
        parts.append(f'<text x="{x + 36}" y="{y + 45}" class="section" fill="{theme["accent"]}">CONFRONTO OMOGENEO · {esc(benchmark["year"])}</text>')
        row_start = y + (90 if h < 600 else 120)
        step = 72 if h < 600 else 105
        maximum = max(value for _, value in items) or 1
        bar_x, bar_w, value_x = x + 290, 440, x + w - 36
        for index, (label, value) in enumerate(items):
            cy = row_start + index * step
            parts.extend([
                f'<text x="{x + 36}" y="{cy + 23}" class="label">{label}</text>',
                f'<rect data-role="bar-track" x="{bar_x}" y="{cy}" width="{bar_w}" height="28" rx="14" fill="#FFFFFF" stroke="{theme["line"]}"/>',
                f'<rect data-role="bar-fill" x="{bar_x}" y="{cy}" width="{bar_w * value / maximum:.1f}" height="28" rx="14" fill="{theme["accent"]}"/>',
                f'<text data-role="numeric-value" x="{value_x}" y="{cy + 25}" class="number" text-anchor="end">{esc(format_value(value, unit, compact=True))}</text>',
            ])
        note_y = y + (h - 112 if h < 600 else h - 170)
        parts.append(f'<text x="{x + 36}" y="{note_y}" class="section" fill="{theme["accent"]}">COME LEGGERLO</text>')
        parts.append(svg_text(benchmark["note"], x + 36, note_y + 44, "body", 72, 31, 2 if h < 600 else 4, "method-note"))
        result.update({"values": dict(items), "source": benchmark["source"], "source_url": benchmark["url"]})
    else:
        aggregate = aggregate_for(metric, card["use_normalized"])
        cursor = y + 45
        parts.append(f'<text x="{x + 36}" y="{cursor}" class="section" fill="{theme["accent"]}">CHE COSA MISURA</text>')
        parts.append(svg_text(meta["description"], x + 36, cursor + 43, "body", 72, 31, 2 if h < 600 else 4, "definition"))
        cursor += 120 if h < 600 else 170
        if aggregate:
            parts.append(f'<text x="{x + 36}" y="{cursor}" class="small">{esc(aggregate["label"])}</text>')
            parts.append(f'<text data-role="numeric-value" x="{x + 36}" y="{cursor + 67}" class="number-large">{esc(format_value(aggregate["value"], unit, compact=True))}</text>')
            cursor += 112 if h < 600 else 145
        parts.append(f'<line x1="{x + 36}" x2="{x + w - 36}" y1="{cursor}" y2="{cursor}" stroke="{theme["line"]}"/>')
        parts.append(f'<text x="{x + 36}" y="{cursor + 43}" class="section" fill="{theme["accent"]}">COME SI CALCOLA</text>')
        parts.append(svg_text(method["formula"], x + 36, cursor + 84, "body", 72, 30, 2 if h < 600 else 4, "formula"))
        cursor += 145 if h < 600 else 195
        parts.append(f'<text x="{x + 36}" y="{cursor}" class="section" fill="{theme["accent"]}">LIMITE DI LETTURA</text>')
        parts.append(svg_text(method["caveat"], x + 36, cursor + 42, "body", 72, 30, 2 if h < 600 else 4, "caveat"))
        result.update({"values": {"aggregate": aggregate["value"] if aggregate else None}, "source": meta["source"], "source_url": metric["sourceUrl"]})
    return result


def render_question(parts: list[str], question: str, theme: dict[str, str], frame: dict[str, Any]) -> None:
    box = frame["question"]
    x, y, w, h = box["x"], box["y"], box["width"], box["height"]
    parts.extend([
        f'<rect data-role="question-panel" x="{x}" y="{y}" width="{w}" height="{h}" rx="30" fill="{theme["accent"]}"/>',
        f'<text data-role="question-label" x="{x + 36}" y="{y + 45}" class="question-label">LA DOMANDA</text>',
        svg_text(question, x + 36, y + 94, "question", 49 if h < 200 else 54, 34, 2, "question-text"),
    ])


def render_footer(parts: list[str], source: str, year: str, version: str, theme: dict[str, str], frame: dict[str, Any]) -> None:
    y = frame["footer_y"]
    parts.extend([
        f'<line data-role="footer-rule" x1="72" x2="1008" y1="{y}" y2="{y}" stroke="{theme["line"]}" stroke-width="2"/>',
        f'<text data-role="source" x="72" y="{y + 38}" class="footer">Fonte: {esc(source)}</text>',
        f'<text data-role="data-version" x="72" y="{y + 72}" class="footer mono">{esc(year)} · dati {esc(version)}</text>',
        f'<text data-role="site-domain" x="72" y="{y + 102}" class="footer">osservatorioversilia.it</text>',
    ])


def render_card(
    card: dict[str, Any],
    size_name: str,
    data: dict[str, Any],
    themes: dict[str, Any],
    design: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    metric = data["metrics"][card["metric"]]
    theme = themes["themes"][card["theme"]]
    brand = themes["brand"]
    frame = design["formats"][size_name]
    parts = svg_start(frame["width"], frame["height"], brand)
    _, display_unit, display_label = normalized_rows(metric, card["use_normalized"])
    if card["slot"] == "data":
        description = f"{display_label} · {unit_label(display_unit)} · {metric['meta']['year']}"
    else:
        description = f"Definizione, metodo e limiti · {metric['meta']['year']}"
    render_frame(parts, card, metric, theme, design, size_name, description)
    if card["slot"] == "data":
        result = render_data_panel(parts, card, metric, theme, frame)
        source = metric["meta"]["source"]
        source_url = metric["sourceUrl"]
    else:
        result = render_context_panel(parts, card, metric, theme, frame)
        source = result["source"]
        source_url = result["source_url"]
    render_question(parts, card["question"], theme, frame)
    render_footer(parts, source, str(metric["meta"]["year"]), data["version"], theme, frame)
    parts.append("</svg>")
    result.update({
        "id": card["id"],
        "week": card["week"],
        "slot": card["slot"],
        "theme": card["theme"],
        "metric": card["metric"],
        "title": card["title"],
        "question": card["question"],
        "size": size_name,
        "source": source,
        "source_url": source_url,
        "year": str(metric["meta"]["year"]),
        "display_label": display_label,
    })
    return "\n".join(parts), result


def indicator_url(metric: str, theme: str) -> str:
    return f"{SITE_URL}/confronta/{theme}/?indicatore={metric}"


def make_copy(card: dict[str, Any], result: dict[str, Any], data: dict[str, Any]) -> dict[str, str]:
    metric = data["metrics"][card["metric"]]
    link = indicator_url(card["metric"], card["theme"])
    if card["slot"] == "data":
        values = list(result["values"].values())
        unit = result["unit"]
        factual = f"Nei sette Comuni il valore va da {format_value(min(values), unit)} a {format_value(max(values), unit)}."
        interpretation = "Il grafico mostra uno scostamento numerico e non attribuisce automaticamente un giudizio di qualità."
    else:
        factual = metric["meta"]["description"]
        interpretation = f"Metodo: {metric['method']['formula']}"
    master = "\n\n".join([
        f"{metric['meta']['label']} · {metric['meta']['year']}",
        factual,
        interpretation,
        f"Fonte: {result['source']}",
        f"Dati e metodo: {link}",
        card["question"],
    ])
    tags = "#OsservatorioVersilia #DatiPubblici #Versilia"
    x_text = f"{metric['meta']['shortLabel']}: {factual} {card['question']} {link}"
    if len(x_text) > 275:
        x_text = x_text[:272].rstrip() + "…"
    return {
        "master": master,
        "facebook": master,
        "instagram": master + "\n\n" + tags,
        "linkedin": master + "\n\nLa provenienza completa è disponibile nella scheda collegata.",
        "x": x_text,
    }


def alt_text(card: dict[str, Any], result: dict[str, Any], data: dict[str, Any]) -> str:
    metric = data["metrics"][card["metric"]]
    if card["slot"] == "data":
        unit = result["unit"]
        values = "; ".join(f"{town} {format_value(value, unit)}" for town, value in result["values"].items())
        return f"Infografica di Osservatorio Versilia. {metric['meta']['label']}, {metric['meta']['year']}. Sette Comuni in ordine alfabetico: {values}. Domanda: {card['question']}"
    return f"Infografica di Osservatorio Versilia. Come leggere {metric['meta']['label'].lower()}. {metric['meta']['description']} Metodo: {metric['method']['formula']} Domanda: {card['question']}"


def render_png(svg_path: Path, png_path: Path, width: int, height: int) -> bool:
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=width, output_height=height)
        return True
    except ImportError:
        pass
    except Exception as exc:
        print(f"Avviso CairoSVG per {svg_path.name}: {exc}")
    converter = shutil.which("magick") or shutil.which("convert")
    if not converter:
        return False
    command = [converter]
    if Path(converter).name == "magick":
        command.append("convert")
    command.extend([str(svg_path), str(png_path)])
    completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return completed.returncode == 0


def build_pdf(pngs: list[Path], output: Path) -> bool:
    if not pngs:
        return False
    try:
        from PIL import Image
    except ImportError:
        return False
    images = [Image.open(path).convert("RGB") for path in pngs]
    images[0].save(output, save_all=True, append_images=images[1:], resolution=144.0)
    for image in images:
        image.close()
    return True


def gallery(cards: list[dict[str, Any]], feed_results: dict[str, dict[str, Any]], has_png: bool, has_pdf: bool, design_version: str) -> str:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        grouped.setdefault(card["week"], []).append(card)
    sections = []
    ext = "png" if has_png else "svg"
    for week, week_cards in grouped.items():
        figures = []
        for card in week_cards:
            result = feed_results[card["id"]]
            figures.append(f"""
            <article>
              <img src="feed/{esc(card['id'])}.{ext}" alt="{esc(alt_text(card, result, GLOBAL_DATA))}">
              <h3>{'Martedì · Il dato' if card['slot'] == 'data' else 'Venerdì · Come leggerlo'}</h3>
              <p>{esc(card['question'])}</p>
              <nav><a href="feed/{esc(card['id'])}.png">PNG feed</a><a href="story/{esc(card['id'])}.png">PNG storia</a><a href="captions/{esc(card['id'])}-instagram.txt">Testo</a><a href="provenance/{esc(card['id'])}.json">Provenienza</a></nav>
            </article>""")
        sections.append(f'<section><header><span>{esc(week)}</span><h2>{esc(feed_results[week_cards[0]["id"]]["display_label"])}</h2></header><div class="pair">{"".join(figures)}</div></section>')
    pdf = '<a class="download" href="linkedin-carousel.pdf">PDF LinkedIn</a>' if has_pdf else ""
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Social Kit · Osservatorio Versilia</title><style>
    @font-face{{font-family:Geist;src:url('../../assets/fonts/geist-latin.woff2')}}*{{box-sizing:border-box}}body{{margin:0;background:#f4eee2;color:#102f45;font-family:Geist,Arial,sans-serif}}body>header{{padding:54px max(24px,6vw);background:#fffaf1;border-bottom:1px solid #c9d5d5}}h1{{font-size:clamp(44px,7vw,88px);line-height:.94;margin:15px 0}}body>header p{{font-size:20px;line-height:1.5;max-width:780px;color:#526b7a}}.download{{display:inline-block;padding:12px 18px;border:1px solid #145b78;border-radius:12px;color:#145b78;text-decoration:none;font-weight:700}}main{{padding:50px max(24px,6vw) 100px}}section{{margin-bottom:80px}}section>header span{{font-family:monospace;color:#526b7a}}h2{{font-size:42px;margin:10px 0 28px}}.pair{{display:grid;grid-template-columns:repeat(2,minmax(0,430px));gap:36px}}article img{{width:100%;border-radius:16px;box-shadow:0 20px 44px rgba(16,47,69,.15)}}h3{{font-size:24px;margin:20px 0 8px}}article p{{font-size:18px;line-height:1.45;color:#365469}}nav{{display:flex;flex-wrap:wrap;gap:8px}}nav a{{padding:9px 11px;border:1px solid #c9d5d5;border-radius:9px;color:#145b78;text-decoration:none;background:#fffaf1}}@media(max-width:760px){{.pair{{grid-template-columns:1fr}}}}
    </style></head><body><header><span>BOZZA LOCALE · {esc(design_version)}</span><h1>Due post.<br>Un solo sistema.</h1><p>Ogni settimana usa lo stesso indicatore in due momenti coordinati. Griglia, logo, fondo, gerarchie e fonti rimangono bloccati.</p>{pdf}</header><main>{''.join(sections)}</main></body></html>"""


GLOBAL_DATA: dict[str, Any] = {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera il Social Kit settimanale")
    parser.add_argument("--theme")
    parser.add_argument("--metric")
    parser.add_argument("--week-id")
    parser.add_argument("--normalized", action="store_true")
    parser.add_argument("--data-question")
    parser.add_argument("--context-question")
    parser.add_argument("--list-metrics", action="store_true")
    parser.add_argument("--no-png", action="store_true")
    args = parser.parse_args()

    data = load_json(ROOT / "data" / "site-data.json")
    global GLOBAL_DATA
    GLOBAL_DATA = data
    themes = load_json(KIT / "config" / "themes.json")
    design = load_json(KIT / "config" / "design-system.json")
    calendar = load_json(KIT / "config" / "editorial-calendar.json")
    question_bank = load_json(KIT / "config" / "question-bank.json")
    ready = load_json(KIT / "config" / "social-ready.json")

    if args.list_metrics:
        for key, metric in sorted(data["metrics"].items(), key=lambda item: (item[1]["meta"]["theme"], item[1]["meta"]["label"])):
            if key in ready["approved_metrics"]:
                print(f"{metric['meta']['theme']:<12} {key:<42} {metric['meta']['label']}")
        return 0

    weeks = build_weeks(args, calendar, question_bank)
    for week in weeks:
        if week["metric"] not in ready["approved_metrics"]:
            raise ValueError(f"Indicatore non approvato per il Social Kit: {week['metric']}")
    cards = expand_cards(weeks, data)

    if DIST.exists():
        shutil.rmtree(DIST)
    for folder in ["feed", "story", "captions", "alt", "provenance"]:
        (DIST / folder).mkdir(parents=True, exist_ok=True)

    generated: list[dict[str, Any]] = []
    feed_results: dict[str, dict[str, Any]] = {}
    feed_pngs: list[Path] = []
    png_ok = not args.no_png
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    for card in cards:
        primary: dict[str, Any] | None = None
        for size_name, size in design["formats"].items():
            svg, result = render_card(card, size_name, data, themes, design)
            svg_path = DIST / size_name / f"{card['id']}.svg"
            png_path = DIST / size_name / f"{card['id']}.png"
            svg_path.write_text(svg, encoding="utf-8")
            if not args.no_png:
                ok = render_png(svg_path, png_path, size["width"], size["height"])
                png_ok = png_ok and ok
                if ok and size_name == "feed":
                    feed_pngs.append(png_path)
            generated.append(result)
            if size_name == "feed":
                primary = result
                feed_results[card["id"]] = result
        assert primary is not None
        for platform, copy in make_copy(card, primary, data).items():
            (DIST / "captions" / f"{card['id']}-{platform}.txt").write_text(copy + "\n", encoding="utf-8")
        (DIST / "alt" / f"{card['id']}.txt").write_text(alt_text(card, primary, data) + "\n", encoding="utf-8")
        provenance = {
            "design_system": design["version"],
            "week": card["week"],
            "slot": card["slot"],
            "dataset": {"path": "data/site-data.json", "version": data["version"], "updated": data["updated"]},
            "metric": card["metric"],
            "theme": card["theme"],
            "year": primary["year"],
            "source": primary["source"],
            "source_url": primary["source_url"],
            "values": primary["values"],
            "question": card["question"],
            "generated_at": timestamp,
        }
        (DIST / "provenance" / f"{card['id']}.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    has_png = png_ok and len(feed_pngs) == len(cards)
    has_pdf = build_pdf(feed_pngs, DIST / "linkedin-carousel.pdf") if has_png else False
    manifest = {
        "method": "two-post-week",
        "design_system": design["version"],
        "dataset_version": data["version"],
        "generated_at": timestamp,
        "weeks": weeks,
        "cards": generated,
        "png": has_png,
        "linkedin_pdf": has_pdf,
    }
    (DIST / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DIST / "index.html").write_text(gallery(cards, feed_results, has_png, has_pdf, design["version"]), encoding="utf-8")
    print(f"Generate {len(weeks)} settimane · {len(cards)} post · master {design['version']}")
    print(f"PNG: {'sì' if has_png else 'no'} · PDF LinkedIn: {'sì' if has_pdf else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
