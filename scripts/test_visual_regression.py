#!/usr/bin/env python3
"""A4 visual regression on a representative, catalog-derived sample."""
from __future__ import annotations

import argparse
import base64
import json
import re
import struct
import zlib
from pathlib import Path
from urllib.parse import quote, urljoin

from playwright.sync_api import Locator, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CONTRACT_PATH = ROOT / "ci" / "visual-regression-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def load_contract() -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    require(contract.get("schemaVersion") == 1, "Visual regression contract: schemaVersion != 1")
    require(contract.get("scope", {}).get("noMetricInventory") is True, "Il contratto non deve inventariare metriche")
    return contract


def load_catalog() -> dict:
    path = DIST / "data" / "site-data.json"
    require(path.exists(), "Effective Public Catalog assente da dist/data/site-data.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data.get("themes"), dict) and data["themes"], "Catalogo privo di temi")
    require(isinstance(data.get("metrics"), dict) and data["metrics"], "Catalogo privo di metriche")
    return data


def ordered_metric_keys(data: dict) -> list[str]:
    metrics = data["metrics"]
    ordered: list[str] = []
    seen: set[str] = set()
    for theme in data["themes"].values():
        for key in theme.get("metrics") or []:
            if key in metrics and key not in seen:
                ordered.append(key)
                seen.add(key)
    for key in metrics:
        if key not in seen:
            ordered.append(key)
            seen.add(key)
    return ordered


def metric_theme(data: dict, metric_key: str) -> str:
    meta = data["metrics"][metric_key].get("meta") or {}
    theme = str(meta.get("theme") or "").strip()
    if theme:
        return theme
    for theme_key, theme_data in data["themes"].items():
        if metric_key in (theme_data.get("metrics") or []):
            return theme_key
    raise AssertionError(f"Tema non risolto per {metric_key}")


def metric_url(base: str, data: dict, metric_key: str) -> str:
    theme = metric_theme(data, metric_key)
    return urljoin(base, f"confronta/{quote(theme)}/?indicatore={quote(metric_key)}")


def series_points(metric: dict) -> int:
    lengths: list[int] = []
    for row in metric.get("rows") or []:
        series = row.get("series") or {}
        values = series.get("values")
        if isinstance(values, list) and values:
            lengths.append(len(values))
    return max(lengths, default=0)


def stable_page(page: Page) -> None:
    page.evaluate("() => document.fonts?.ready || Promise.resolve()")
    page.add_style_tag(
        content="""
          *, *::before, *::after {
            animation: none !important;
            transition: none !important;
            caret-color: transparent !important;
          }
        """
    )
    page.wait_for_timeout(80)


def open_metric(page: Page, base: str, data: dict, metric_key: str) -> None:
    response = page.goto(metric_url(base, data, metric_key), wait_until="networkidle")
    require(response is None or response.ok, f"Route non disponibile per {metric_key}")
    # La vista corrente o storico può persistere tra metriche. Il contenitore
    # deve esistere, ma può essere intenzionalmente nascosto se lo storico è attivo.
    page.wait_for_selector("#compare-bars .topic-bars", state="attached")
    stable_page(page)


def screenshot_locator(locator: Locator) -> bytes:
    locator.wait_for(state="visible")
    return locator.screenshot(animations="disabled")


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_png_rgb(data: bytes) -> tuple[int, int, list[bytes]]:
    require(data[:8] == b"\\x89PNG\\r\\n\\x1a\\n", "Screenshot PNG non valido")
    position = 8
    idat: list[bytes] = []
    width = height = bit_depth = color_type = interlace = None
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        chunk_type = data[position + 4:position + 8]
        chunk = data[position + 8:position + 8 + length]
        position += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
        elif chunk_type == b"IDAT":
            idat.append(chunk)
        elif chunk_type == b"IEND":
            break

    require(
        bit_depth == 8 and color_type in {2, 6} and interlace == 0,
        f"Formato PNG screenshot non supportato: depth={bit_depth}, type={color_type}, interlace={interlace}",
    )
    require(isinstance(width, int) and isinstance(height, int), "IHDR PNG assente")

    bytes_per_pixel = 3 if color_type == 2 else 4
    raw = zlib.decompress(b"".join(idat))
    stride = width * bytes_per_pixel
    offset = 0
    previous = bytearray(stride)
    rows: list[bytes] = []

    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        scanline = raw[offset:offset + stride]
        offset += stride
        reconstructed = bytearray(stride)
        for index, value in enumerate(scanline):
            left = reconstructed[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            up = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                decoded = value
            elif filter_type == 1:
                decoded = (value + left) & 255
            elif filter_type == 2:
                decoded = (value + up) & 255
            elif filter_type == 3:
                decoded = (value + ((left + up) // 2)) & 255
            elif filter_type == 4:
                decoded = (value + _paeth(left, up, upper_left)) & 255
            else:
                raise AssertionError(f"Filtro PNG inatteso: {filter_type}")
            reconstructed[index] = decoded

        if bytes_per_pixel == 3:
            rows.append(bytes(reconstructed))
        else:
            rgb = bytearray(width * 3)
            for pixel in range(width):
                rgb[pixel * 3:pixel * 3 + 3] = reconstructed[pixel * 4:pixel * 4 + 3]
            rows.append(bytes(rgb))
        previous = reconstructed

    return width, height, rows


def _grid_rgb(width: int, height: int, rows: list[bytes], grid_size: int) -> list[tuple[int, int, int]]:
    sums = [0] * (grid_size * grid_size * 3)
    counts = [0] * (grid_size * grid_size)
    for y, row in enumerate(rows):
        gy = min(grid_size - 1, y * grid_size // height)
        for x in range(width):
            gx = min(grid_size - 1, x * grid_size // width)
            cell = gy * grid_size + gx
            source = x * 3
            target = cell * 3
            sums[target] += row[source]
            sums[target + 1] += row[source + 1]
            sums[target + 2] += row[source + 2]
            counts[cell] += 1

    result: list[tuple[int, int, int]] = []
    for cell, count in enumerate(counts):
        target = cell * 3
        result.append(
            (
                round(sums[target] / count),
                round(sums[target + 1] / count),
                round(sums[target + 2] / count),
            )
        )
    return result


def _pack_bits(bits: list[bool]) -> str:
    output = bytearray((len(bits) + 7) // 8)
    for index, enabled in enumerate(bits):
        if enabled:
            output[index // 8] |= 1 << (7 - (index % 8))
    return base64.b64encode(bytes(output)).decode("ascii")


def visual_signature(image: bytes, grid_size: int) -> dict:
    require(grid_size % 8 == 0, "hashGridSize deve essere divisibile per 8")
    width, height, rows = decode_png_rgb(image)
    rgb = _grid_rgb(width, height, rows, grid_size)
    luminance = [round(0.2126 * red + 0.7152 * green + 0.0722 * blue) for red, green, blue in rgb]
    mean_luminance = sum(luminance) / len(luminance)

    average_hash = _pack_bits([value >= mean_luminance for value in luminance])
    difference_hash = _pack_bits(
        [
            luminance[y * grid_size + x] >= luminance[y * grid_size + x + 1]
            for y in range(grid_size)
            for x in range(grid_size - 1)
        ]
    )

    block = grid_size // 8
    coarse = bytearray()
    for by in range(8):
        for bx in range(8):
            cells = [
                rgb[(by * block + yy) * grid_size + (bx * block + xx)]
                for yy in range(block)
                for xx in range(block)
            ]
            for channel in range(3):
                average = sum(value[channel] for value in cells) / len(cells)
                coarse.append(round(average / 255 * 31))

    return {
        "width": width,
        "height": height,
        "aHash": average_hash,
        "dHash": difference_hash,
        "color8x8": base64.b64encode(bytes(coarse)).decode("ascii"),
    }


def _hamming_ratio(left: str, right: str) -> float:
    a = base64.b64decode(left)
    b = base64.b64decode(right)
    require(len(a) == len(b), "Hash visuali con lunghezza diversa")
    changed = sum((x ^ y).bit_count() for x, y in zip(a, b))
    return changed / (len(a) * 8)


def compare_signatures(actual: dict, expected: dict, contract: dict) -> dict:
    actual_color = base64.b64decode(actual["color8x8"])
    expected_color = base64.b64decode(expected["color8x8"])
    require(len(actual_color) == len(expected_color), "Fingerprint colore con lunghezza diversa")
    color_mean = sum(abs(a - b) for a, b in zip(actual_color, expected_color)) / len(actual_color)
    return {
        "dimensionsMatch": actual["width"] == expected["width"] and actual["height"] == expected["height"],
        "actualWidth": actual["width"],
        "actualHeight": actual["height"],
        "expectedWidth": expected["width"],
        "expectedHeight": expected["height"],
        "aHashHammingRatio": _hamming_ratio(actual["aHash"], expected["aHash"]),
        "dHashHammingRatio": _hamming_ratio(actual["dHash"], expected["dHash"]),
        "colorMeanAbsoluteDifference": color_mean,
    }


class Regression:
    def __init__(self, contract: dict, *, record: bool = False) -> None:
        self.contract = contract
        self.record = record
        self.baseline_dir = ROOT / contract["baselineDirectory"]
        self.output_dir = ROOT / contract["outputDirectory"]
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.expected_names: set[str] = set()
        self.results: list[dict] = []
        self.failures: list[str] = []
        self.recorded: dict[str, dict] = {}

        self.baselines: dict[str, dict] = {}
        self.grid_size = int(contract["hashGridSize"])
        require(self.baseline_dir.exists(), f"Directory baseline assente: {self.baseline_dir}")
        baseline_files = sorted(self.baseline_dir.glob("*.json"))
        require(baseline_files, f"Nessuna baseline JSON in {self.baseline_dir}")
        for path in baseline_files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            require(payload.get("schemaVersion") == 1, f"Baseline schema invalido: {path}")
            require(int(payload.get("hashGridSize", 0)) == self.grid_size, f"Grid baseline incoerente: {path}")
            samples = payload.get("samples")
            require(isinstance(samples, dict) and samples, f"Baseline vuota: {path}")
            overlap = set(samples) & set(self.baselines)
            require(not overlap, f"Baseline duplicate tra file: {sorted(overlap)}")
            self.baselines.update(samples)

    def check(self, name: str, image: bytes, metadata: dict) -> None:
        self.expected_names.add(name)
        actual = visual_signature(image, self.grid_size)

        if self.record:
            self.recorded[name] = actual
            self.results.append({"sample": name, "status": "recorded", **metadata})
            (self.output_dir / f"record--{name}.png").write_bytes(image)
            return

        expected = self.baselines.get(name)
        if expected is None:
            candidate = self.output_dir / f"actual--{name}.png"
            candidate.write_bytes(image)
            self.failures.append(f"baseline mancante: {name}")
            self.results.append({"sample": name, "status": "missing-baseline", "candidate": str(candidate), **metadata})
            return

        comparison = compare_signatures(actual, expected, self.contract)
        cfg = self.contract["comparison"]
        dimensions_ok = comparison["dimensionsMatch"] or not cfg.get("dimensionsMustMatch", True)
        passed = (
            dimensions_ok
            and comparison["aHashHammingRatio"] <= float(cfg["maxAverageHashHammingRatio"])
            and comparison["dHashHammingRatio"] <= float(cfg["maxDifferenceHashHammingRatio"])
            and comparison["colorMeanAbsoluteDifference"] <= float(cfg["maxColorMeanAbsoluteDifference"])
        )
        status = "match" if passed else "mismatch"
        self.results.append({"sample": name, "status": status, "comparison": comparison, **metadata})
        if not passed:
            candidate = self.output_dir / f"actual--{name}.png"
            candidate.write_bytes(image)
            self.failures.append(
                f"{name}: aHash={comparison['aHashHammingRatio']:.2%}, "
                f"dHash={comparison['dHashHammingRatio']:.2%}, "
                f"color={comparison['colorMeanAbsoluteDifference']:.3f}, "
                f"size={comparison['actualWidth']}x{comparison['actualHeight']} "
                f"vs {comparison['expectedWidth']}x{comparison['expectedHeight']}"
            )

    def finish(self) -> None:
        stale = sorted(set(self.baselines) - self.expected_names)
        if stale and not self.record:
            self.failures.append(f"baseline obsolete: {', '.join(stale)}")

        if self.record:
            candidate = {
                "schemaVersion": 1,
                "hashGridSize": self.grid_size,
                "samples": dict(sorted(self.recorded.items())),
            }
            (self.output_dir / "recorded-baselines.json").write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        report = {
            "schemaVersion": 1,
            "sampleCount": len(self.expected_names),
            "baselineCount": len(self.baselines),
            "recordMode": self.record,
            "failures": self.failures,
            "results": self.results,
        }
        (self.output_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if self.failures:
            raise AssertionError(
                "Visual regression fallita:\n- "
                + "\n- ".join(self.failures)
                + f"\nReport: {self.output_dir / 'report.json'}"
            )


def viewport(contract: dict, key: str) -> dict[str, int]:
    raw = contract["viewports"][key]
    return {"width": int(raw["width"]), "height": int(raw["height"])}


def capture_theme_samples(reg: Regression, page: Page, base: str, data: dict, contract: dict) -> None:
    cfg = contract["samples"]["themes"]
    page.set_viewport_size(viewport(contract, cfg["viewport"]))
    metrics = data["metrics"]
    for theme_key, theme in data["themes"].items():
        key = next((candidate for candidate in (theme.get("metrics") or []) if candidate in metrics), None)
        require(key is not None, f"Tema {theme_key} privo di metrica renderizzabile")
        open_metric(page, base, data, key)
        image = screenshot_locator(page.locator(cfg["selector"]).first)
        reg.check(
            f"theme--{slug(theme_key)}--{cfg['viewport']}",
            image,
            {"kind": "theme", "theme": theme_key, "metric": key, "viewport": cfg["viewport"]},
        )


def capture_generic_families(reg: Regression, page: Page, base: str, data: dict, contract: dict) -> None:
    cfg = contract["samples"]["genericFamilies"]
    pending = set(cfg["requiredDataViz"])
    page.set_viewport_size(viewport(contract, cfg["viewport"]))
    for key in ordered_metric_keys(data):
        if not pending:
            break
        open_metric(page, base, data, key)
        chart = page.locator("#compare-bars .comparison-bars").first
        if chart.count() != 1:
            continue
        family = chart.get_attribute("data-viz")
        if family not in pending:
            continue
        image = screenshot_locator(page.locator(cfg["selector"]).first)
        reg.check(
            f"generic--{slug(family)}--{cfg['viewport']}",
            image,
            {"kind": "generic-family", "family": family, "metric": key, "viewport": cfg["viewport"]},
        )
        pending.remove(family)
    require(not pending, f"Famiglie data-viz non risolte: {sorted(pending)}")


def capture_composite_families(reg: Regression, page: Page, base: str, data: dict, contract: dict) -> None:
    cfg = contract["samples"]["compositeFamilies"]
    page.set_viewport_size(viewport(contract, cfg["viewport"]))
    selected: dict[str, str] = {}
    for key in ordered_metric_keys(data):
        composite = str((data["metrics"][key].get("meta") or {}).get("compositeType") or "").strip()
        if composite and composite not in selected:
            selected[composite] = key
    require(selected, "Nessun compositeType nel catalogo effettivo")
    for composite, key in selected.items():
        open_metric(page, base, data, key)
        image = screenshot_locator(page.locator(cfg["selector"]).first)
        reg.check(
            f"composite--{slug(composite)}--{cfg['viewport']}",
            image,
            {"kind": "composite-family", "family": composite, "metric": key, "viewport": cfg["viewport"]},
        )


def history_candidate(data: dict, variant: dict) -> str:
    for key in ordered_metric_keys(data):
        points = series_points(data["metrics"][key])
        if "seriesPoints" in variant and points == int(variant["seriesPoints"]):
            return key
        if "minimumSeriesPoints" in variant and points >= int(variant["minimumSeriesPoints"]):
            return key
    raise AssertionError(f"Nessuna metrica per variante storico {variant}")


def activate_current(page: Page, scope: str) -> None:
    button = page.locator(f"{scope} [data-view-mode='current']").first
    require(button.count() == 1, f"Comando corrente assente in {scope}")
    if not button.is_disabled():
        button.click()
        page.wait_for_timeout(120)


def activate_history(page: Page, scope: str) -> None:
    history = page.locator(f"{scope} .ux-history-card").first
    if history.count() == 1 and history.is_visible():
        return
    button = page.locator(f"{scope} [data-view-mode='history']").first
    require(button.count() == 1, f"Comando storico assente in {scope}")
    require(not button.is_disabled(), f"Comando storico disabilitato in {scope}")
    button.click()
    page.wait_for_timeout(120)


def capture_history_families(reg: Regression, page: Page, base: str, data: dict, contract: dict) -> None:
    cfg = contract["samples"]["historyFamilies"]
    page.set_viewport_size(viewport(contract, cfg["viewport"]))
    for variant in cfg["variants"]:
        key = history_candidate(data, variant)
        open_metric(page, base, data, key)
        activate_history(page, "#compare-bars")
        card = page.locator(cfg["selector"]).first
        card.wait_for(state="visible")
        stable_page(page)
        image = screenshot_locator(card)
        reg.check(
            f"history--{slug(variant['id'])}--{cfg['viewport']}",
            image,
            {"kind": "history-family", "family": variant["id"], "metric": key, "viewport": cfg["viewport"]},
        )


def capture_town_history(reg: Regression, page: Page, base: str, data: dict, contract: dict) -> None:
    cfg = contract["samples"]["townHistory"]
    if not cfg.get("enabled"):
        return
    towns = data.get("towns") or []
    require(towns, "Catalogo privo di comuni")
    town = towns[0]
    town_slug = town.get("slug") or slug(str(town.get("name") or ""))
    require(town_slug, "Slug del primo comune non risolto")
    key = next(
        candidate
        for candidate in ordered_metric_keys(data)
        if series_points(data["metrics"][candidate]) >= 3
    )
    theme = metric_theme(data, key)
    page.set_viewport_size(viewport(contract, cfg["viewport"]))
    url = urljoin(base, f"comuni/{quote(town_slug)}/?tema={quote(theme)}&indicatore={quote(key)}")
    response = page.goto(url, wait_until="networkidle")
    require(response is None or response.ok, f"Route comunale non disponibile: {url}")
    panel = page.locator(cfg["selector"]).first
    panel.wait_for(state="visible")
    activate_current(page, cfg["selector"])
    stable_page(page)
    reg.check(
        f"town--current--{cfg['viewport']}",
        screenshot_locator(panel),
        {"kind": "town-history", "state": "current", "town": town_slug, "metric": key, "viewport": cfg["viewport"]},
    )
    activate_history(page, cfg["selector"])
    page.locator(f"{cfg['selector']} .ux-history-card").first.wait_for(state="visible")
    stable_page(page)
    reg.check(
        f"town--history--{cfg['viewport']}",
        screenshot_locator(panel),
        {"kind": "town-history", "state": "history", "town": town_slug, "metric": key, "viewport": cfg["viewport"]},
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    parser.add_argument(
        "--record-baselines",
        action="store_true",
        help="Registra le baseline correnti; non viene usato dal preflight canonico.",
    )
    args = parser.parse_args()

    contract = load_contract()
    data = load_catalog()
    base = args.base.rstrip("/") + "/"
    chromium_path = __import__("os").environ.get("CHROMIUM_PATH")
    launch_args: dict[str, object] = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_args)
        context = browser.new_context(
            viewport=viewport(contract, "desktop"),
            color_scheme="light",
            reduced_motion="reduce",
            locale="it-IT",
        )
        page = context.new_page()
        page.set_default_timeout(15000)
        reg = Regression(contract, record=args.record_baselines)

        capture_theme_samples(reg, page, base, data, contract)
        capture_generic_families(reg, page, base, data, contract)
        capture_composite_families(reg, page, base, data, contract)
        capture_history_families(reg, page, base, data, contract)
        capture_town_history(reg, page, base, data, contract)
        reg.finish()

        context.close()
        browser.close()

    print(f"Visual regression A4: {len(reg.expected_names)} baseline rappresentative verificate.")


if __name__ == "__main__":
    main()
