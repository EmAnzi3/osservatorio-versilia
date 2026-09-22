#!/usr/bin/env python3
"""Genera caroselli social standardizzati in quattro tavole 1080×1350."""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import shutil
import subprocess
import textwrap
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "social-kit"
DIST = KIT / "dist"
SITE_URL = "https://osservatorioversilia.it"
MUNICIPALITY_HASHTAGS = (
    "#Camaiore #ForteDeiMarmi #Massarosa #Pietrasanta "
    "#Seravezza #Stazzema #Viareggio"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def fmt_it(value: float, decimals: int = 0) -> str:
    raw = f"{value:,.{decimals}f}"
    return raw.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_value(value: float, unit: str, signed: bool = False) -> str:
    prefix = "+" if signed and value > 0 else ""
    if unit == "percent":
        return f"{prefix}{fmt_it(value, 1)}%"
    if unit == "currency":
        return f"{prefix}{fmt_it(value, 0)} €"
    if unit == "celsius":
        return f"{prefix}{fmt_it(value, 1)} °C"
    if unit == "percentage_points":
        return f"{prefix}{fmt_it(value, 1)} punti"
    if unit == "per1000":
        return f"{prefix}{fmt_it(value, 1)} ogni 1.000"
    if unit == "per10k":
        return f"{prefix}{fmt_it(value, 1)} ogni 10.000"
    if unit == "minutes":
        return f"{prefix}{fmt_it(value, 1)} min"
    decimals = 0 if float(value).is_integer() or unit in {"number", "people"} else 1
    return prefix + fmt_it(value, decimals)


def compact_value(value: float, unit: str) -> str:
    if unit == "percent":
        return f"{fmt_it(value, 1)}%"
    if unit == "currency":
        return f"{fmt_it(value, 0)} €"
    if unit == "celsius":
        return f"{fmt_it(value, 1)} °C"
    if unit in {"per1000", "per10k", "minutes"}:
        return fmt_it(value, 1)
    return fmt_it(value, 0 if float(value).is_integer() else 1)


def logo_uri() -> str:
    raw = (ROOT / "assets" / "brand-mark.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")


def fit_lines(text: str, max_width: float, max_height: float, start_size: int, min_size: int, max_lines: int) -> tuple[list[str], int, int]:
    """Adatta il testo al rettangolo; se non entra, fallisce invece di debordare."""
    for size in range(start_size, min_size - 1, -1):
        line_height = int(round(size * 1.24))
        capacity = max(8, int(max_width / (size * 0.56)))
        wrapped = textwrap.wrap(
            text,
            width=capacity,
            break_long_words=False,
            break_on_hyphens=False,
            replace_whitespace=True,
        ) or [""]
        if len(wrapped) <= max_lines and len(wrapped) * line_height <= max_height:
            return wrapped, size, line_height
    raise ValueError(f"Testo non contenibile nel box: {text}")


def fitted_text(
    text: str,
    x: float,
    y: float,
    max_width: float,
    max_height: float,
    css_class: str,
    start_size: int,
    min_size: int,
    max_lines: int,
    role: str,
    fill: str | None = None,
) -> str:
    wrapped, size, line_height = fit_lines(text, max_width, max_height, start_size, min_size, max_lines)
    fill_attr = f' fill="{fill}"' if fill else ""
    tspans = "".join(
        f'<tspan x="{x}" dy="{0 if index == 0 else line_height}">{esc(line)}</tspan>'
        for index, line in enumerate(wrapped)
    )
    return (
        f'<text data-role="{role}" data-box-x="{x}" data-box-y="{y - size}" '
        f'data-box-width="{max_width}" data-box-height="{max_height}" x="{x}" y="{y}" '
        f'class="{css_class}" style="font-size:{size}px"{fill_attr}>{tspans}</text>'
    )


def render_png(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    try:
        import cairosvg
    except ImportError:  # pragma: no cover - fallback utile negli ambienti di revisione
        node = shutil.which("node")
        if node:
            probe = subprocess.run(
                [node, "-e", "require.resolve('sharp')"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if probe.returncode == 0:
                script = (
                    "const sharp=require('sharp');const [src,dst,w,h]=process.argv.slice(1);"
                    "sharp(src,{density:144}).resize(Number(w),Number(h)).png().toFile(dst)"
                    ".catch(e=>{console.error(e);process.exit(1)})"
                )
                subprocess.run(
                    [node, "-e", script, str(svg_path), str(png_path), str(width), str(height)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
        chromium = os.environ.get("CHROMIUM_BIN") or shutil.which("chromium") or shutil.which("google-chrome")
        if not chromium:
            raise RuntimeError("Installa social-kit/requirements.txt oppure imposta CHROMIUM_BIN")
        subprocess.run(
            [
                chromium,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                f"--window-size={width},{height}",
                f"--screenshot={png_path}",
                svg_path.resolve().as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        cairosvg.svg2png(
            bytestring=svg_path.read_bytes(),
            write_to=str(png_path),
            output_width=width,
            output_height=height,
        )


def aggregate_mode(unit: str) -> str:
    return "sum" if unit in {"number", "people"} else "mean"


def aggregate(values: list[float], mode: str) -> float:
    return sum(values) if mode == "sum" else mean(values)


def site_model(post: dict[str, Any]) -> dict[str, Any]:
    data = load(ROOT / "data" / "site-data.json")
    metric = data["metrics"].get(post["metric"])
    if not metric:
        raise ValueError(f"Indicatore inesistente: {post['metric']}")
    rows = sorted(metric["rows"], key=lambda row: row["town"].casefold())
    unit = metric["meta"]["unit"]
    series_available = all(row.get("series") for row in rows)
    years: list[int] = []
    if series_available:
        years = [int(year) for year in rows[0]["series"]["years"]]
        for row in rows:
            row_years = [int(year) for year in row["series"]["years"]]
            if row_years != years or len(row["series"]["values"]) != len(years):
                raise ValueError(f"Serie non omogenea: {row['town']}")
    normalized_rows = [
        {
            "town": row["town"],
            "value": float(row["value"]),
            "series": [float(value) for value in row["series"]["values"]] if series_available else None,
        }
        for row in rows
    ]
    return {
        "dataset": "site",
        "dataset_path": "data/site-data.json",
        "dataset_version": data["version"],
        "dataset_updated": data.get("updated"),
        "dataset_status": "published",
        "metric": post["metric"],
        "theme": metric["meta"]["theme"],
        "label": metric["meta"]["label"],
        "short_label": metric["meta"].get("shortLabel") or metric["meta"]["label"],
        "description": metric["meta"]["description"],
        "unit": unit,
        "year": int(metric["meta"]["year"]),
        "year_label": str(metric["meta"]["year"]),
        "source": metric["meta"]["source"],
        "source_url": metric.get("sourceUrl") or metric.get("meta", {}).get("sourceUrl"),
        "method": metric.get("method", {}),
        "benchmark": metric["meta"].get("benchmark"),
        "rows": normalized_rows,
        "years": years,
        "aggregate_mode": aggregate_mode(unit),
        "link": f"{SITE_URL}/confronta/{metric['meta']['theme']}/?indicatore={post['metric']}",
    }


def climate_model(post: dict[str, Any]) -> dict[str, Any]:
    data = load(ROOT / "data" / "meteo-clima-minmax-poc.json")
    key = post["metric"]
    if key not in {"tmin", "tmax"}:
        raise ValueError(f"Variabile climatica non supportata: {key}")
    rows = []
    years: list[int] | None = None
    for town, item in sorted(data["municipalities"].items(), key=lambda pair: pair[0].casefold()):
        row_years = [int(year) for year in item["years"]]
        values = [float(value) for value in item[key]]
        if years is None:
            years = row_years
        elif years != row_years:
            raise ValueError("Le serie climatiche comunali non hanno lo stesso periodo")
        latest = item["latestComplete"]
        if int(latest["year"]) != row_years[-1] or float(latest[key]) != values[-1]:
            raise ValueError(f"Ultimo valore climatico non coerente: {town}")
        rows.append({"town": town, "value": float(latest[key]), "series": values})
    label = "Temperatura massima media annua" if key == "tmax" else "Temperatura minima media annua"
    return {
        "dataset": "climate-minmax",
        "dataset_path": "data/meteo-clima-minmax-poc.json",
        "dataset_version": data["version"],
        "dataset_updated": None,
        "dataset_status": data["status"],
        "metric": key,
        "theme": "ambiente",
        "label": label,
        "short_label": label.replace(" annua", ""),
        "description": data["definition"][key],
        "unit": "celsius",
        "year": int(years[-1]),
        "year_label": f"{years[0]}–{years[-1]}",
        "source": "Copernicus ERA5-Land · riferimento LaMMA/SIR",
        "source_url": "https://cds.climate.copernicus.eu/",
        "method": data["method"],
        "benchmark": None,
        "rows": rows,
        "years": years,
        "aggregate_mode": "mean",
        "link": f"{SITE_URL}/confronta/meteo-clima/",
    }


def build_model(post: dict[str, Any]) -> dict[str, Any]:
    model = climate_model(post) if post["dataset"] == "climate-minmax" else site_model(post)
    if model["theme"] != post["theme"]:
        raise ValueError(f"Tema {post['theme']} non coerente con {post['metric']}")
    if len(model["rows"]) != 7:
        raise ValueError(f"{post['id']} non ha copertura 7/7")
    if not model["source_url"]:
        raise ValueError(f"Fonte senza URL: {post['id']}")
    return model


def history_slice(model: dict[str, Any], post: dict[str, Any]) -> tuple[list[int], list[float]]:
    if not model["years"]:
        return [], []
    start = int(post.get("history_from", model["years"][0]))
    if start not in model["years"]:
        raise ValueError(f"Anno iniziale {start} assente: {post['id']}")
    index = model["years"].index(start)
    years = model["years"][index:]
    values = [
        aggregate([row["series"][position] for row in model["rows"]], model["aggregate_mode"])
        for position in range(index, len(model["years"]))
    ]
    return years, values


def comparison(model: dict[str, Any], post: dict[str, Any]) -> dict[str, Any] | None:
    if not model["years"]:
        return None
    spec = post["comparison"]
    rows = []
    if spec["type"] == "base_year":
        base_year = int(spec["year"])
        if base_year not in model["years"]:
            raise ValueError(f"Anno base assente: {base_year}")
        index = model["years"].index(base_year)
        for row in model["rows"]:
            base = float(row["series"][index])
            current = float(row["value"])
            delta = current - base
            display = delta if model["unit"] == "percent" else (delta / base * 100 if base else 0.0)
            rows.append({"town": row["town"], "base": base, "current": current, "delta": delta, "display": display})
        base_values = [row["base"] for row in rows]
        current_values = [row["current"] for row in rows]
        base_total = aggregate(base_values, model["aggregate_mode"])
        current_total = aggregate(current_values, model["aggregate_mode"])
        delta = current_total - base_total
        display_unit = "percentage_points" if model["unit"] == "percent" else "percent"
        display = delta if display_unit == "percentage_points" else (delta / base_total * 100 if base_total else 0.0)
        return {
            "type": "base_year",
            "label": f"dal {base_year} al {model['year']}",
            "section": f"VARIAZIONE DAL {base_year}",
            "rows": rows,
            "base": base_total,
            "current": current_total,
            "delta": delta,
            "display": display,
            "display_unit": display_unit,
        }
    if spec["type"] == "period_mean":
        base_from, base_to = [int(value) for value in spec["base"]]
        current_from, current_to = [int(value) for value in spec["current"]]
        for row in model["rows"]:
            base_values = [value for year, value in zip(model["years"], row["series"]) if base_from <= year <= base_to]
            current_values = [value for year, value in zip(model["years"], row["series"]) if current_from <= year <= current_to]
            if len(base_values) != base_to - base_from + 1 or len(current_values) != current_to - current_from + 1:
                raise ValueError(f"Periodi incompleti: {row['town']}")
            base = mean(base_values)
            current = mean(current_values)
            rows.append({"town": row["town"], "base": base, "current": current, "delta": current - base, "display": current - base})
        base_total = mean([row["base"] for row in rows])
        current_total = mean([row["current"] for row in rows])
        return {
            "type": "period_mean",
            "label": f"media {base_from}–{base_to} e media {current_from}–{current_to}",
            "section": f"DIFFERENZA TRA {base_from}–{base_to} E {current_from}–{current_to}",
            "rows": rows,
            "base": base_total,
            "current": current_total,
            "delta": current_total - base_total,
            "display": current_total - base_total,
            "display_unit": model["unit"],
        }
    raise ValueError(f"Confronto non supportato: {spec['type']}")


def svg_start(design: dict[str, Any]) -> list[str]:
    width = design["format"]["width"]
    height = design["format"]["height"]
    immutable = design["immutable"]
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        "<style>",
        "@font-face{font-family:Geist;src:url('../../../assets/fonts/geist-latin.woff2') format('woff2');font-weight:100 900}",
        f"text{{font-family:Geist,Arial,sans-serif;fill:{immutable['ink']}}}",
        ".brand{font-size:29px;font-weight:800}.brand-sub{font-size:16px;font-weight:600;fill:#526B7A}",
        ".theme{font-size:18px;font-weight:800;letter-spacing:3px}.counter{font-size:15px;font-weight:760}",
        ".title{font-weight:740;letter-spacing:-1.8px}.subtitle{font-weight:460;fill:#526B7A}",
        ".section{font-size:16px;font-weight:800;letter-spacing:2.4px}.label{font-size:20px;font-weight:700}",
        ".small{font-size:16px;font-weight:540;fill:#526B7A}.axis{font-size:14px;font-weight:560;fill:#526B7A}",
        ".number{font-size:30px;font-weight:760}.hero-label{font-size:17px;font-weight:760;letter-spacing:1.5px}",
        ".body{font-size:22px;font-weight:470;fill:#365469}.question{font-weight:720}",
        ".footer{font-size:16px;font-weight:570;fill:#526B7A}.white{fill:#FFFFFF}",
        "</style>",
        f'<rect data-role="fixed-background" width="{width}" height="{height}" fill="{immutable["background"]}"/>',
        '<circle data-role="fixed-motif" cx="1000" cy="95" r="245" fill="#E7ECE8" opacity=".82"/>',
        f'<circle data-role="fixed-motif" cx="45" cy="{height - 30}" r="220" fill="#EBE7DC" opacity=".78"/>',
    ]


def frame(parts: list[str], index: int, title: str, subtitle: str, model: dict[str, Any], design: dict[str, Any], theme: dict[str, str]) -> None:
    immutable = design["immutable"]
    layout = design["layout"]
    logo = immutable["logo"]
    brand_text = immutable["brand_text"]
    parts.extend([
        f'<image data-role="brand-logo" href="{logo_uri()}" x="{logo["x"]}" y="{logo["y"]}" width="{logo["width"]}" height="{logo["height"]}"/>',
        f'<text x="{brand_text["x"]}" y="{brand_text["y"]}" class="brand">Osservatorio Versilia</text>',
        f'<text x="{brand_text["x"]}" y="{brand_text["y"] + 26}" class="brand-sub">Dati pubblici, lettura accessibile</text>',
        f'<line data-role="header-rule" x1="72" x2="1008" y1="{layout["header_rule_y"]}" y2="{layout["header_rule_y"]}" stroke="{immutable["line"]}" stroke-width="2"/>',
        f'<line x1="72" x2="292" y1="{layout["header_rule_y"]}" y2="{layout["header_rule_y"]}" stroke="{theme["accent"]}" stroke-width="5" stroke-linecap="round"/>',
        f'<rect x="928" y="176" width="80" height="38" rx="19" fill="{theme["accent"]}" opacity=".12"/>',
        f'<text x="968" y="201" class="counter" fill="{theme["accent"]}" text-anchor="middle">{index} DI 4</text>',
        f'<text x="72" y="{layout["theme_y"]}" class="theme" fill="{theme["accent"]}">{esc(theme["label"].upper())}</text>',
        fitted_text(title, 72, layout["title_y"], 820, 108, "title", 56, 42, 2, "post-title"),
        fitted_text(subtitle, 72, layout["subtitle_y"], 900, 62, "subtitle", 24, 20, 2, "post-subtitle"),
        f'<line x1="72" x2="1008" y1="{layout["footer_y"]}" y2="{layout["footer_y"]}" stroke="{theme["line"]}" stroke-width="2"/>',
        fitted_text(f"Fonte: {model['source']}", 72, layout["footer_y"] + 38, 820, 25, "footer", 16, 14, 1, "source"),
        f'<text x="72" y="{layout["footer_y"] + 72}" class="footer">{esc(model["year_label"])} · dati {esc(model["dataset_version"])}</text>',
        f'<text x="72" y="{layout["footer_y"] + 102}" class="footer">osservatorioversilia.it</text>',
    ])


def panel(parts: list[str], design: dict[str, Any], theme: dict[str, str], fill: str | None = None) -> dict[str, float]:
    box = design["layout"]["panel"]
    parts.append(
        f'<rect data-role="content-panel" x="{box["x"]}" y="{box["y"]}" width="{box["width"]}" height="{box["height"]}" '
        f'rx="30" fill="{fill or design["immutable"]["surface"]}" stroke="{theme["line"]}" stroke-width="2"/>'
    )
    return {key: float(value) for key, value in box.items()}


def current_slide(parts: list[str], box: dict[str, float], model: dict[str, Any], theme: dict[str, str]) -> None:
    x, y, w = box["x"], box["y"], box["width"]
    rows = model["rows"]
    current = aggregate([row["value"] for row in rows], model["aggregate_mode"])
    aggregate_label = "TOTALE VERSILIA" if model["aggregate_mode"] == "sum" else "MEDIA DEI SETTE COMUNI"
    hero_y = y + 28
    parts.extend([
        f'<rect x="{x + 32}" y="{hero_y}" width="{w - 64}" height="128" rx="24" fill="{theme["accent"]}"/>',
        f'<text x="{x + 68}" y="{hero_y + 37}" class="hero-label white">{aggregate_label}</text>',
        fitted_text(fmt_value(current, model["unit"]), x + 66, hero_y + 101, 370, 58, "white", 56, 38, 1, "aggregate-current", "#FFFFFF"),
        fitted_text(model["short_label"].lower(), x + 450, hero_y + 91, 390, 44, "white", 19, 16, 2, "aggregate-description", "#FFFFFF"),
        f'<text x="{x + w - 64}" y="{hero_y + 39}" class="white" style="font-size:18px;font-weight:650" text-anchor="end">{model["year"]}</text>',
        f'<text x="{x + 36}" y="{y + 195}" class="section" fill="{theme["accent"]}">COMUNE PER COMUNE · ORDINE ALFABETICO</text>',
    ])
    maximum = max(row["value"] for row in rows) or 1.0
    label_x, bar_x, value_x, bar_w = x + 36, x + 300, x + w - 36, 430
    row_start, step = y + 222, 58
    for index, row in enumerate(rows):
        cy = row_start + index * step
        width = max(3, bar_w * row["value"] / maximum)
        parts.extend([
            f'<text x="{label_x}" y="{cy + 22}" class="label">{esc(row["town"])}</text>',
            f'<rect data-role="bar-track" x="{bar_x}" y="{cy}" width="{bar_w}" height="24" rx="12" fill="#FFFFFF" stroke="{theme["line"]}"/>',
            f'<rect x="{bar_x}" y="{cy}" width="{width:.1f}" height="24" rx="12" fill="{theme["accent"]}"/>',
            f'<text data-role="numeric-value" x="{value_x}" y="{cy + 21}" class="number" text-anchor="end">{esc(compact_value(row["value"], model["unit"]))}</text>',
        ])


def history_slide(parts: list[str], box: dict[str, float], model: dict[str, Any], years: list[int], values: list[float], comp: dict[str, Any], theme: dict[str, str]) -> None:
    """Mostra sette serie comunali come piccoli multipli, mai un aggregato."""
    x, y, w, h = box["x"], box["y"], box["width"], box["height"]
    del values, comp
    start_index = model["years"].index(years[0])
    hero_y = y + 28
    parts.extend([
        f'<rect x="{x + 32}" y="{hero_y}" width="{w - 64}" height="84" rx="22" fill="{theme["soft"]}" stroke="{theme["line"]}" stroke-width="2"/>',
        f'<text x="{x + 64}" y="{hero_y + 34}" class="hero-label" fill="{theme["accent"]}">EVOLUZIONE DEI SINGOLI COMUNI</text>',
        f'<text x="{x + w - 64}" y="{hero_y + 57}" style="font-size:30px;font-weight:790" text-anchor="end">{years[0]}–{years[-1]}</text>',
        f'<text x="{x + 36}" y="{y + 151}" class="section" fill="{theme["accent"]}">EVOLUZIONE COMUNE PER COMUNE · SERIE ANNUALE</text>',
    ])

    label_x = x + 36
    spark_x, spark_w = x + 268, 300
    first_value_x, last_value_x = x + 704, x + w - 36
    header_y = y + 184
    parts.extend([
        f'<text x="{label_x}" y="{header_y}" class="axis">COMUNE</text>',
        f'<text x="{spark_x}" y="{header_y}" class="axis">ANDAMENTO</text>',
        f'<text x="{first_value_x}" y="{header_y}" class="axis" text-anchor="end">{years[0]}</text>',
        f'<text x="{last_value_x}" y="{header_y}" class="axis" text-anchor="end">{years[-1]}</text>',
    ])

    row_start, step, spark_h = y + 218, 59, 32
    for row_index, row in enumerate(model["rows"]):
        cy = row_start + row_index * step
        series = row["series"][start_index:]
        raw_min, raw_max = min(series), max(series)
        spread = max(0.01, raw_max - raw_min)
        minimum, maximum = raw_min - spread * 0.12, raw_max + spread * 0.12

        def px(index: int) -> float:
            return spark_x + spark_w * index / max(1, len(years) - 1)

        def py(value: float) -> float:
            return cy + spark_h * (maximum - value) / (maximum - minimum) - spark_h / 2

        points = " ".join(f"{px(index):.1f},{py(value):.1f}" for index, value in enumerate(series))
        parts.extend([
            f'<text x="{label_x}" y="{cy + 7}" class="label">{esc(row["town"])}</text>',
            f'<line x1="{spark_x}" x2="{spark_x + spark_w}" y1="{cy}" y2="{cy}" stroke="#D8DFDC" stroke-width="2"/>',
            f'<polyline data-role="history-spark" data-row="{row_index}" x="{spark_x}" width="{spark_w}" points="{points}" fill="none" stroke="{theme["accent"]}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
            f'<circle cx="{px(0):.1f}" cy="{py(series[0]):.1f}" r="5" fill="{theme["accent"]}" stroke="#FFF9F2" stroke-width="2"/>',
            f'<circle cx="{px(len(series) - 1):.1f}" cy="{py(series[-1]):.1f}" r="5" fill="{theme["accent"]}" stroke="#FFF9F2" stroke-width="2"/>',
            f'<text data-role="history-start-value" data-row="{row_index}" x="{first_value_x}" y="{cy + 7}" class="axis" text-anchor="end">{esc(compact_value(series[0], model["unit"]))}</text>',
            f'<text x="{x + 748}" y="{cy + 7}" class="axis">→</text>',
            f'<text data-role="history-end-value" data-row="{row_index}" data-left="{last_value_x - 112}" x="{last_value_x}" y="{cy + 8}" class="label" text-anchor="end">{esc(compact_value(series[-1], model["unit"]))}</text>',
        ])
    parts.append(f'<text x="{x + 36}" y="{y + h - 24}" class="small">Scala adattata a ciascun Comune: confronta la forma, non l’altezza tra le righe.</text>')


def change_slide(parts: list[str], box: dict[str, float], model: dict[str, Any], comp: dict[str, Any], theme: dict[str, str]) -> None:
    x, y, w, h = box["x"], box["y"], box["width"], box["height"]
    hero_y = y + 28
    parts.extend([
        f'<rect x="{x + 32}" y="{hero_y}" width="{w - 64}" height="104" rx="22" fill="{theme["soft"]}" stroke="{theme["line"]}" stroke-width="2"/>',
        f'<text x="{x + 64}" y="{hero_y + 32}" class="hero-label" fill="{theme["accent"]}">VERSILIA NEL COMPLESSO</text>',
        fitted_text(comp["label"], x + 62, hero_y + 76, 560, 35, "label", 22, 18, 1, "aggregate-change-label"),
        f'<text x="{x + w - 62}" y="{hero_y + 78}" style="font-size:33px;font-weight:790" text-anchor="end">{esc(fmt_value(comp["display"], comp["display_unit"], True))}</text>',
        f'<text x="{x + 36}" y="{y + 174}" class="section" fill="{theme["accent"]}">{esc(comp["section"])}</text>',
    ])
    rows = comp["rows"]
    maximum = max(abs(row["display"]) for row in rows) or 1.0
    # Corsie indipendenti: etichetta, grafico, valore. Nessuna barra entra nei numeri.
    label_x, zero_x, value_x, half_w = x + 36, x + 570, x + w - 36, 170
    row_start, step = y + 205, 58
    axis_top = row_start - 18
    axis_bottom = row_start + (len(rows) - 1) * step + 34
    parts.extend([
        f'<line x1="{zero_x}" x2="{zero_x}" y1="{axis_top}" y2="{axis_bottom}" stroke="#82949D" stroke-width="2"/>',
        f'<text x="{zero_x}" y="{axis_top - 12}" class="axis" text-anchor="middle">0</text>',
    ])
    for index, row in enumerate(rows):
        cy = row_start + index * step
        width = max(3, half_w * abs(row["display"]) / maximum)
        bar_x = zero_x if row["display"] >= 0 else zero_x - width
        value_text = fmt_value(row["display"], comp["display_unit"], True)
        value_left = value_x - max(112, len(value_text) * 18)
        parts.extend([
            f'<text x="{label_x}" y="{cy + 20}" class="label">{esc(row["town"])}</text>',
            f'<line x1="{zero_x - half_w}" x2="{zero_x + half_w}" y1="{cy + 13}" y2="{cy + 13}" stroke="#D8DFDC" stroke-width="2"/>',
            f'<rect data-role="change-bar" data-row="{index}" x="{bar_x:.1f}" y="{cy}" width="{width:.1f}" height="26" rx="13" fill="{theme["accent"]}"/>',
            f'<text data-role="change-value" data-row="{index}" data-left="{value_left:.1f}" x="{value_x}" y="{cy + 22}" class="number" text-anchor="end">{esc(value_text)}</text>',
        ])
    parts.append(f'<text x="{x + 36}" y="{y + h - 28}" class="small">La posizione rispetto allo zero indica la direzione, non un giudizio.</text>')


def validate_slide_geometry(svg: str, post_id: str, slide_index: int) -> None:
    """Blocca la generazione se grafico e testo condividono lo stesso spazio."""
    root = ET.fromstring(svg)
    by_role: dict[str, dict[str, ET.Element]] = {}
    for element in root.iter():
        role = element.attrib.get("data-role")
        row = element.attrib.get("data-row")
        if role and row is not None:
            by_role.setdefault(role, {})[row] = element

    def right_edge(element: ET.Element) -> float:
        return float(element.attrib["x"]) + float(element.attrib["width"])

    pairs = {2: ("history-spark", "history-end-value"), 3: ("change-bar", "change-value")}
    if slide_index not in pairs:
        return
    graphic_role, value_role = pairs[slide_index]
    for row, graphic in by_role.get(graphic_role, {}).items():
        value = by_role.get(value_role, {}).get(row)
        if value is None or right_edge(graphic) + 24 > float(value.attrib["data-left"]):
            raise ValueError(f"Sovrapposizione grafico/testo: {post_id}, tavola {slide_index}, riga {int(row) + 1}")


def context_slides(parts: list[str], box: dict[str, float], model: dict[str, Any], theme: dict[str, str], kind: str) -> None:
    x, y, w = box["x"], box["y"], box["width"]
    heading = "CHE COSA MISURA" if kind == "history" else "COME LEGGERLO"
    body = model["description"]
    if kind == "change":
        benchmark = model.get("benchmark")
        body = (
            "Il confronto tra Comuni descrive una differenza numerica; da solo non stabilisce cause, qualità dei servizi o responsabilità."
        )
        if benchmark:
            body += f" Il benchmark documentato dalla fonte è riferito al {benchmark.get('year', model['year'])}."
    parts.extend([
        f'<rect x="{x + 32}" y="{y + 32}" width="{w - 64}" height="112" rx="24" fill="{theme["accent"]}"/>',
        f'<text x="{x + 68}" y="{y + 72}" class="hero-label white">{heading}</text>',
        fitted_text(model["short_label"], x + 66, y + 120, 790, 36, "white", 31, 24, 1, "context-heading", "#FFFFFF"),
        f'<rect x="{x + 36}" y="{y + 190}" width="{w - 72}" height="310" rx="26" fill="{theme["soft"]}" stroke="{theme["line"]}" stroke-width="2"/>',
        fitted_text(body, x + 72, y + 248, w - 144, 205, "body", 25, 18, 6, "context-body"),
        fitted_text("Il contenuto resta una descrizione del dato pubblicato: nessuna differenza viene trasformata in una classifica.", x + 72, y + 550, w - 144, 70, "body", 21, 17, 3, "context-caveat"),
    ])


def questions_slide(parts: list[str], design: dict[str, Any], post: dict[str, Any], theme: dict[str, str]) -> None:
    layout = design["layout"]
    panel_box = layout["panel"]
    x, y, w = panel_box["x"], panel_box["y"], panel_box["width"]
    parts.append(fitted_text(
        "I dati descrivono il territorio. La tua esperienza può aggiungere ciò che i grafici non mostrano.",
        x + 42, y + 56, w - 84, 64, "body", 22, 18, 2, "question-intro"
    ))
    labels = ["NEL TUO COMUNE", "GUARDANDO AI SERVIZI"]
    for index, (question, box) in enumerate(zip(post["questions"], layout["question_boxes"]), start=1):
        parts.extend([
            f'<rect data-role="question-box" x="{box["x"]}" y="{box["y"]}" width="{box["width"]}" height="{box["height"]}" rx="25" fill="#FFFFFF" stroke="{theme["line"]}" stroke-width="2"/>',
            f'<circle cx="{box["x"] + 36}" cy="{box["y"] + 39}" r="14" fill="{theme["accent"]}" opacity=".13"/>',
            f'<text x="{box["x"] + 36}" y="{box["y"] + 45}" style="font-size:20px;font-weight:800" fill="{theme["accent"]}" text-anchor="middle">{index}</text>',
            f'<text x="{box["x"] + 72}" y="{box["y"] + 42}" class="section" fill="{theme["accent"]}">{labels[index - 1]}</text>',
            fitted_text(
                question,
                box["x"] + 32,
                box["y"] + 93,
                box["width"] - 64,
                box["height"] - 82,
                "question",
                design["type"]["question_start"],
                design["type"]["question_min"],
                design["type"]["question_max_lines"],
                f"question-{index}",
            ),
        ])
    cta = layout["cta"]
    parts.extend([
        f'<rect data-role="cta" x="{cta["x"]}" y="{cta["y"]}" width="{cta["width"]}" height="{cta["height"]}" rx="26" fill="{theme["accent"]}"/>',
        f'<text x="{cta["x"] + 34}" y="{cta["y"] + 39}" class="hero-label white">PARTECIPA ALLA CONVERSAZIONE</text>',
        f'<text x="{cta["x"] + 34}" y="{cta["y"] + 88}" class="white" style="font-size:34px;font-weight:780">Scrivilo nei commenti.</text>',
        fitted_text("Indica il Comune e segui la pagina per il prossimo dato.", cta["x"] + 34, cta["y"] + 125, cta["width"] - 68, 28, "white", 19, 16, 1, "follow-cta", "#FFFFFF"),
    ])


def default_titles(model: dict[str, Any], post: dict[str, Any]) -> tuple[list[str], list[str]]:
    start = post.get("history_from", model["years"][0] if model["years"] else model["year"])
    comparison_spec = post.get("comparison", {})
    if comparison_spec.get("type") == "base_year":
        comparison_subtitle = (
            f"Differenza in punti rispetto al {comparison_spec['year']}"
            if model["unit"] == "percent"
            else f"Differenza percentuale rispetto al {comparison_spec['year']}"
        )
    elif comparison_spec.get("type") == "period_mean":
        base_from, base_to = comparison_spec["base"]
        current_from, current_to = comparison_spec["current"]
        comparison_subtitle = f"Media {base_from}–{base_to} e media {current_from}–{current_to}"
    else:
        comparison_subtitle = "Confronto temporale"
    titles = [
        f"{model['short_label']} oggi",
        f"Dal {start} a oggi" if model["years"] else "Che cosa misura il dato",
        "La variazione per Comune" if model["years"] else "Come leggere il confronto",
        "Cosa vedi nel tuo Comune?",
    ]
    subtitles = [
        f"I sette Comuni a confronto · {model['year']}",
        model["label"],
        comparison_subtitle,
        "I numeri aprono la conversazione. Il territorio la completa.",
    ]
    return post.get("titles", titles), post.get("subtitles", subtitles)


def make_page(index: int, title: str, subtitle: str, model: dict[str, Any], post: dict[str, Any], design: dict[str, Any], theme: dict[str, str], draw: Callable[[list[str], dict[str, float]], None]) -> str:
    parts = svg_start(design)
    frame(parts, index, title, subtitle, model, design, theme)
    box = panel(parts, design, theme, theme["soft"] if index == 4 else None)
    draw(parts, box)
    parts.append("</svg>")
    return "\n".join(parts)


def copy_for_platforms(post: dict[str, Any], model: dict[str, Any], comp: dict[str, Any] | None) -> dict[str, str]:
    current = aggregate([row["value"] for row in model["rows"]], model["aggregate_mode"])
    aggregate_label = "complessivi" if model["aggregate_mode"] == "sum" else "in media tra i sette Comuni"
    fact = f"{model['short_label']}: {fmt_value(current, model['unit'])} {aggregate_label} nel {model['year']}."
    comparison_line = (
        f"Nel confronto {comp['label']}, la variazione complessiva è {fmt_value(comp['display'], comp['display_unit'], True)}."
        if comp else ""
    )
    companion_line = post.get("companion_copy") or ""
    method_line = post.get("context_note") or model["description"]
    question_line = f"{post['questions'][0]} {post['questions'][1]}"
    participation = "Nei commenti indica il Comune a cui fai riferimento e segui la pagina per il prossimo dato."
    source_line = f"Fonte: {model['source']} · {model['year_label']} · dati {model['dataset_version']}"
    link_line = f"Dati, metodo e fonti: {model['link']}"
    observance = post.get("observance") or {}
    observance_line = f"🌍 {observance.get('name')}" if observance.get("name") else "📊 Un dato per leggere la Versilia"
    theme_tag = "".join(word.capitalize() for word in model["theme"].split())
    shared = "\n\n".join(item for item in [
        observance_line,
        f"📌 {fact}",
        f"📈 {comparison_line}" if comparison_line else "",
        f"📈 {companion_line}" if companion_line else "",
        f"🧭 {method_line}",
        f"💬 {question_line}",
        f"👥 {participation}",
        f"🔎 {link_line}",
        f"📚 {source_line}",
    ] if item) + f"\n\n#OsservatorioVersilia #Versilia #{theme_tag} #DatiPubblici {MUNICIPALITY_HASHTAGS}"
    master = shared
    result = {
        "master": master,
        "facebook": shared,
        "instagram": shared,
        "linkedin": shared,
    }
    change = f" Confronto: {fmt_value(comp['display'], comp['display_unit'], True)}." if comp else ""
    x_text = (
        f"{model['short_label']}: {fmt_value(current, model['unit'])} {aggregate_label} nel {model['year']}.{change} "
        f"{post['questions'][0]} {model['link']} #Versilia"
    )
    if len(x_text) > 280:
        x_text = f"{model['short_label']}: {fmt_value(current, model['unit'])} nel {model['year']}.{change} {model['link']} #Versilia"
    if len(x_text) > 280:
        raise ValueError(f"Testo X oltre 280 caratteri: {post['id']}")
    result["x"] = x_text
    return result


def generate_post(post: dict[str, Any], design: dict[str, Any], themes: dict[str, Any], destination: Path) -> dict[str, Any]:
    model = build_model(post)
    if model["dataset_status"] == "draft" and post.get("status") != "draft":
        raise ValueError(f"Dataset draft usato in un contenuto non draft: {post['id']}")
    theme = themes["themes"][post["theme"]]
    years, history = history_slice(model, post)
    comp = comparison(model, post) if model["years"] else None
    history_model = model
    history_years = years
    history_values = history
    history_comp = comp
    context_model: dict[str, Any] | None = None
    if not model["years"] and post.get("history_metric"):
        history_model = build_model({**post, "metric": post["history_metric"]})
        history_post = {
            **post,
            "metric": post["history_metric"],
            "history_from": post.get("history_from_by_metric", {}).get(post["history_metric"], history_model["years"][0]),
            "comparison": post.get("comparison_by_metric", {}).get(
                post["history_metric"], {"type": "base_year", "year": history_model["years"][0]}
            ),
        }
        history_years, history_values = history_slice(history_model, history_post)
        history_comp = comparison(history_model, history_post)
    if not model["years"] and post.get("context_metric"):
        context_model = build_model({**post, "metric": post["context_metric"]})
    companion_parts: list[str] = []
    if history_model is not model and history_years:
        companion_parts.append(
            f"la serie comunale di {history_model['short_label'].lower()} {history_years[0]}–{history_years[-1]}"
        )
    if context_model:
        companion_parts.append(f"{context_model['short_label'].lower()} nel {context_model['year']}")
    copy_post = {**post}
    if companion_parts:
        copy_post["companion_copy"] = "Il carosello affianca " + " e ".join(companion_parts) + "."
    titles, subtitles = default_titles(model, post)
    if len(titles) != 4 or len(subtitles) != 4 or len(post["questions"]) != 2:
        raise ValueError(f"Struttura editoriale incompleta: {post['id']}")
    cards_dir = destination / "cards"
    cards: list[dict[str, str]] = []
    specs: list[tuple[str, Callable[[list[str], dict[str, float]], None], str]] = [
        (
            "01-dato-attuale",
            lambda parts, box: current_slide(parts, box, model, theme),
            f"{model['label']} nel {model['year']}. " + "; ".join(f"{row['town']} {fmt_value(row['value'], model['unit'])}" for row in model["rows"]),
        ),
        (
            "02-andamento-storico" if history_years else "02-cosa-misura",
            (lambda parts, box: history_slide(parts, box, history_model, history_years, history_values, history_comp, theme)) if history_years else (lambda parts, box: context_slides(parts, box, model, theme, "history")),
            (
                f"Evoluzione {history_model['label'].lower()} nei singoli Comuni, {history_years[0]}–{history_years[-1]}: "
                + "; ".join(
                    f"{row['town']}: " + ", ".join(
                        f"{year} {fmt_value(value, history_model['unit'])}"
                        for year, value in zip(history_years, row["series"][history_model["years"].index(history_years[0]):])
                    ) for row in history_model["rows"]
                )
            ) if history_years else model["description"],
        ),
        (
            "03-variazione" if comp else "03-dato-affine" if context_model else "03-come-leggerlo",
            (lambda parts, box: change_slide(parts, box, model, comp, theme)) if comp else (lambda parts, box: current_slide(parts, box, context_model, theme)) if context_model else (lambda parts, box: context_slides(parts, box, model, theme, "change")),
            (f"{comp['label']}: " + "; ".join(f"{row['town']} {fmt_value(row['display'], comp['display_unit'], True)}" for row in comp["rows"])) if comp else (
                f"Dato affine: {context_model['label']} nel {context_model['year']}. "
                + "; ".join(f"{row['town']} {fmt_value(row['value'], context_model['unit'])}" for row in context_model["rows"])
            ) if context_model else "Indicazioni per leggere il confronto senza attribuire cause non dimostrate.",
        ),
        (
            "04-partecipa",
            lambda parts, box: questions_slide(parts, design, post, theme),
            "Due domande aperte: " + " ".join(post["questions"]) + " Invito a commentare indicando il Comune e a seguire la pagina.",
        ),
    ]
    for index, (filename, draw, alt) in enumerate(specs, start=1):
        slide_model = history_model if index == 2 and history_years else context_model if index == 3 and context_model and not comp else model
        if index == 2 and history_years:
            slide_model = {**slide_model, "year_label": f"{history_years[0]}–{history_years[-1]}"}
        slide_title = titles[index - 1]
        slide_subtitle = subtitles[index - 1]
        if index == 2 and history_model is not model:
            slide_title = f"{history_model['short_label']}: {history_years[0]}–{history_years[-1]}"
            slide_subtitle = "Evoluzione dei singoli Comuni"
        if index == 3 and context_model:
            slide_title = context_model["short_label"]
            slide_subtitle = f"Un dato affine per completare la lettura · {context_model['year']}"
        svg = make_page(index, slide_title, slide_subtitle, slide_model, post, design, theme, draw)
        validate_slide_geometry(svg, post["id"], index)
        svg_path = cards_dir / f"{filename}.svg"
        png_path = cards_dir / f"{filename}.png"
        write(svg_path, svg)
        render_png(svg_path, png_path, design["format"]["width"], design["format"]["height"])
        write(destination / "alt" / f"{filename}.txt", alt + "\n")
        cards.append({"slide": index, "filename": filename, "title": titles[index - 1], "alt": alt})
    for platform, copy in copy_for_platforms(copy_post, model, comp).items():
        write(destination / "testi" / f"{platform}.txt", copy + "\n")
    provenance = {
        "status": "draft",
        "post_id": post["id"],
        "date": post["date"],
        "priority": post["priority"],
        "design_system": design["version"],
        "theme": post["theme"],
        "palette": {"accent": theme["accent"], "soft": theme["soft"]},
        "dataset": {
            "path": model["dataset_path"],
            "version": model["dataset_version"],
            "status": model["dataset_status"],
            "updated": model["dataset_updated"],
        },
        "metric": model["metric"],
        "source": model["source"],
        "source_url": model["source_url"],
        "method": model["method"],
        "current_year": model["year"],
        "current_values": {row["town"]: row["value"] for row in model["rows"]},
        "history": {str(year): value for year, value in zip(years, history)},
        "history_by_town": {
            row["town"]: {
                str(year): value
                for year, value in zip(history_years, row["series"][history_model["years"].index(history_years[0]):])
            }
            for row in history_model["rows"]
        } if history_years else {},
        "slide_metrics": {
            "1": model["metric"],
            "2": history_model["metric"] if history_years else model["metric"],
            "3": context_model["metric"] if context_model else model["metric"],
            "4": model["metric"],
        },
        "companion_values": {
            context_model["metric"]: {row["town"]: row["value"] for row in context_model["rows"]}
        } if context_model else {},
        "comparison": comp,
        "questions": post["questions"],
        "context_note": post.get("context_note"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    write(destination / "provenienza.json", json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    manifest = {
        "status": "draft",
        "method": "four-slide-carousel",
        "design_system": design["version"],
        "post_id": post["id"],
        "date": post["date"],
        "format": "1080x1350",
        "platforms": design["format"]["platforms"],
        "outputs": ["png", "svg"],
        "cards": cards,
    }
    write(destination / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def gallery(manifests: list[dict[str, Any]]) -> str:
    sections = []
    for manifest in manifests:
        figures = "".join(
            f'<figure><img src="{esc(manifest["post_id"])}/cards/{esc(card["filename"])}.png" alt=""><figcaption>{esc(card["title"])}</figcaption></figure>'
            for card in manifest["cards"]
        )
        sections.append(f'<section><h2>{esc(manifest["post_id"])}</h2><div class="grid">{figures}</div></section>')
    return (
        '<!doctype html><html lang="it"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Social Kit · bozze</title><style>body{margin:0;background:#102F45;color:#fff;font-family:Arial,sans-serif}'
        'main{max-width:1280px;margin:auto;padding:36px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}'
        'figure{margin:0;background:#fff;padding:10px;border-radius:16px}img{display:block;width:100%;height:auto}figcaption{color:#102F45;padding:10px;font-weight:700}'
        '@media(max-width:760px){.grid{grid-template-columns:1fr}}</style><main><h1>Osservatorio Versilia · Social Kit</h1>'
        + "".join(sections) + "</main></html>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--post-id", help="Genera una sola voce del calendario")
    parser.add_argument("--list-posts", action="store_true", help="Elenca le voci configurate")
    args = parser.parse_args()
    design = load(KIT / "config" / "design-system.json")
    themes = load(KIT / "config" / "themes.json")
    calendar = load(KIT / "config" / "editorial-calendar.json")
    if args.list_posts:
        for post in calendar["posts"]:
            print(f"{post['date']}\t{post['id']}\t{post['theme']}\t{post['metric']}\t{post['status']}")
        return 0
    posts = calendar["posts"]
    if args.post_id:
        posts = [post for post in posts if post["id"] == args.post_id]
        if not posts:
            raise ValueError(f"Voce non trovata: {args.post_id}")
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    manifests = [generate_post(post, design, themes, DIST / post["id"]) for post in posts]
    write(DIST / "index.html", gallery(manifests))
    weeks = Counter(datetime.fromisoformat(post["date"]).isocalendar()[:2] for post in posts)
    root_manifest = {
        "status": "draft",
        "method": "two-carousels-per-week",
        "design_system": design["version"],
        "posts": len(posts),
        "slides": len(posts) * 4,
        "weekly_counts": {f"{year}-W{week:02d}": count for (year, week), count in sorted(weeks.items())},
        "items": manifests,
    }
    write(DIST / "manifest.json", json.dumps(root_manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Social Kit: {len(posts)} caroselli · {len(posts) * 4} tavole 1080×1350 · solo bozze")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
