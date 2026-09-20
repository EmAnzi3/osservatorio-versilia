#!/usr/bin/env python3
"""A4 visual regression on a representative, catalog-derived sample."""
from __future__ import annotations

import argparse
import base64
import json
import re
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
    page.wait_for_selector("#compare-bars .topic-bars", state="visible")
    stable_page(page)


def screenshot_locator(locator: Locator) -> bytes:
    locator.wait_for(state="visible")
    return locator.screenshot(animations="disabled")


def canvas_diff(page: Page, actual: bytes, expected: bytes, channel_threshold: int) -> dict:
    payload = {
        "actual": base64.b64encode(actual).decode("ascii"),
        "expected": base64.b64encode(expected).decode("ascii"),
        "channelThreshold": channel_threshold,
    }
    return page.evaluate(
        """async ({actual, expected, channelThreshold}) => {
          const load = source => new Promise((resolve, reject) => {
            const image = new Image();
            image.onload = () => resolve(image);
            image.onerror = reject;
            image.src = 'data:image/png;base64,' + source;
          });
          const [a, b] = await Promise.all([load(actual), load(expected)]);
          if (a.width !== b.width || a.height !== b.height) {
            return {
              dimensionsMatch: false,
              actualWidth: a.width,
              actualHeight: a.height,
              expectedWidth: b.width,
              expectedHeight: b.height,
              changedPixelRatio: 1,
              meanAbsoluteChannelDifference: 255,
              maxChannelDifference: 255,
            };
          }
          const canvasA = document.createElement('canvas');
          const canvasB = document.createElement('canvas');
          canvasA.width = canvasB.width = a.width;
          canvasA.height = canvasB.height = a.height;
          const ctxA = canvasA.getContext('2d', {willReadFrequently: true});
          const ctxB = canvasB.getContext('2d', {willReadFrequently: true});
          ctxA.drawImage(a, 0, 0);
          ctxB.drawImage(b, 0, 0);
          const da = ctxA.getImageData(0, 0, a.width, a.height).data;
          const db = ctxB.getImageData(0, 0, b.width, b.height).data;
          const pixels = a.width * a.height;
          let changed = 0;
          let sum = 0;
          let max = 0;
          for (let i = 0; i < da.length; i += 4) {
            let pixelMax = 0;
            for (let channel = 0; channel < 4; channel += 1) {
              const delta = Math.abs(da[i + channel] - db[i + channel]);
              sum += delta;
              if (delta > pixelMax) pixelMax = delta;
              if (delta > max) max = delta;
            }
            if (pixelMax > channelThreshold) changed += 1;
          }
          return {
            dimensionsMatch: true,
            actualWidth: a.width,
            actualHeight: a.height,
            expectedWidth: b.width,
            expectedHeight: b.height,
            changedPixelRatio: changed / pixels,
            meanAbsoluteChannelDifference: sum / (pixels * 4),
            maxChannelDifference: max,
          };
        }""",
        payload,
    )


class Regression:
    def __init__(self, contract: dict, page: Page, *, record: bool = False) -> None:
        self.contract = contract
        self.page = page
        self.record = record
        self.baseline_dir = ROOT / contract["baselineDirectory"]
        self.output_dir = ROOT / contract["outputDirectory"]
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.expected_names: set[str] = set()
        self.results: list[dict] = []
        self.failures: list[str] = []

    def check(self, name: str, image: bytes, metadata: dict) -> None:
        filename = f"{name}.png"
        self.expected_names.add(filename)
        baseline = self.baseline_dir / filename
        candidate = self.output_dir / filename

        if self.record:
            baseline.write_bytes(image)
            self.results.append({"sample": name, "status": "recorded", **metadata})
            return

        if not baseline.exists():
            candidate.write_bytes(image)
            self.failures.append(f"baseline mancante: {filename}")
            self.results.append({"sample": name, "status": "missing-baseline", "candidate": str(candidate), **metadata})
            return

        expected = baseline.read_bytes()
        comparison = canvas_diff(
            self.page,
            image,
            expected,
            int(self.contract["comparison"]["channelThreshold"]),
        )
        allowed_ratio = float(self.contract["comparison"]["maxChangedPixelRatio"])
        allowed_mean = float(self.contract["comparison"]["maxMeanAbsoluteChannelDifference"])
        dimensions_ok = comparison["dimensionsMatch"] or not self.contract["comparison"].get("dimensionsMustMatch", True)
        passed = (
            dimensions_ok
            and comparison["changedPixelRatio"] <= allowed_ratio
            and comparison["meanAbsoluteChannelDifference"] <= allowed_mean
        )
        status = "match" if passed else "mismatch"
        entry = {"sample": name, "status": status, "comparison": comparison, **metadata}
        self.results.append(entry)
        if not passed:
            candidate = self.output_dir / f"actual--{filename}"
            candidate.write_bytes(image)
            self.failures.append(
                f"{filename}: ratio={comparison['changedPixelRatio']:.4%}, "
                f"mean={comparison['meanAbsoluteChannelDifference']:.3f}, "
                f"size={comparison['actualWidth']}x{comparison['actualHeight']} "
                f"vs {comparison['expectedWidth']}x{comparison['expectedHeight']}"
            )

    def finish(self) -> None:
        actual_names = {path.name for path in self.baseline_dir.glob("*.png")}
        stale = sorted(actual_names - self.expected_names)
        if stale and not self.record:
            self.failures.append(f"baseline obsolete: {', '.join(stale)}")

        report = {
            "schemaVersion": 1,
            "sampleCount": len(self.expected_names),
            "baselineCount": len(actual_names),
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


def activate_history(page: Page, scope: str) -> None:
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
        reg = Regression(contract, page, record=args.record_baselines)

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
