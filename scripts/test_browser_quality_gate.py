#!/usr/bin/env python3
"""Gate browser trasversale per overflow, errori runtime e clipping dei grafici."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = ROOT / "dist"
VIEWPORTS = (
    ("mobile", 375, 812, True),
    ("tablet", 768, 1024, False),
    ("laptop", 1024, 768, False),
    ("desktop", 1440, 900, True),
)
EXCLUDED_HTML = {"offline.html"}
INTERMEDIATE_INDICATOR_SAMPLE = 12


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def route_for(path: Path, dist: Path) -> str | None:
    rel = path.relative_to(dist).as_posix()
    if rel in EXCLUDED_HTML or rel == "404.html":
        return None
    if rel == "index.html":
        return ""
    if rel.endswith("/index.html"):
        return rel[: -len("index.html")]
    return rel


def discover_routes(dist: Path) -> list[str]:
    routes = sorted(
        route
        for path in dist.rglob("*.html")
        if (route := route_for(path, dist)) is not None
    )
    require(routes, f"Nessuna pagina HTML trovata in {dist}")
    return routes


def representative_routes(routes: list[str]) -> list[str]:
    """Copre tutte le famiglie non-indicatore e un campione distribuito delle pagine indicatore."""
    regular = [route for route in routes if not route.startswith("indicatori/")]
    indicators = [route for route in routes if route.startswith("indicatori/")]
    if len(indicators) <= INTERMEDIATE_INDICATOR_SAMPLE:
        return sorted(set(regular + indicators))

    count = INTERMEDIATE_INDICATOR_SAMPLE
    indexes = {
        round(index * (len(indicators) - 1) / (count - 1))
        for index in range(count)
    }
    sampled = [indicators[index] for index in sorted(indexes)]
    return sorted(set(regular + sampled))


def safe_name(route: str) -> str:
    value = route.strip("/") or "home"
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value)
    return value[:120] or "page"


def wait_for_page(page: Page) -> None:
    page.wait_for_function("document.fonts ? document.fonts.status === 'loaded' : true")
    # Due frame sono sufficienti per applicare layout e rendering client-side senza pagare
    # il costo di networkidle su centinaia di route statiche.
    page.evaluate(
        "() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))"
    )


def browser_findings(page: Page) -> dict[str, object]:
    return page.evaluate(
        """() => {
          const EPS = 2;
          const width = window.innerWidth;
          const root = document.documentElement;
          const body = document.body;

          function visible(el) {
            const style = getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            return style.display !== 'none' && style.visibility !== 'hidden' &&
              Number(style.opacity || 1) !== 0 && rect.width > 0 && rect.height > 0;
          }

          function insideHorizontalScroller(el) {
            let node = el.parentElement;
            while (node && node !== document.body) {
              const style = getComputedStyle(node);
              const overflowX = style.overflowX;
              if ((overflowX === 'auto' || overflowX === 'scroll') && node.scrollWidth > node.clientWidth + EPS) {
                return true;
              }
              node = node.parentElement;
            }
            return false;
          }

          const svgTextOutsideViewport = [];
          for (const el of document.querySelectorAll('svg text')) {
            if (!visible(el) || insideHorizontalScroller(el)) continue;
            const rect = el.getBoundingClientRect();
            if (rect.left < -EPS || rect.right > width + EPS) {
              svgTextOutsideViewport.push({
                text: (el.textContent || '').trim().slice(0, 80),
                left: Math.round(rect.left), right: Math.round(rect.right),
                top: Math.round(rect.top), bottom: Math.round(rect.bottom)
              });
            }
          }

          const nowrapOverflow = [];
          const candidates = document.querySelectorAll('button, a, th, td, label, summary, .stat-value, .metric-value, .topic-value, .town-value');
          for (const el of candidates) {
            if (!visible(el) || insideHorizontalScroller(el)) continue;
            const style = getComputedStyle(el);
            if (style.whiteSpace !== 'nowrap') continue;
            if (el.scrollWidth > el.clientWidth + EPS) {
              nowrapOverflow.push({
                tag: el.tagName.toLowerCase(),
                text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 100),
                clientWidth: el.clientWidth,
                scrollWidth: el.scrollWidth
              });
            }
          }

          const fixedOutsideViewport = [];
          for (const el of document.querySelectorAll('button, input, select, textarea, [role="button"]')) {
            if (!visible(el) || insideHorizontalScroller(el)) continue;
            const rect = el.getBoundingClientRect();
            const style = getComputedStyle(el);
            if (style.position !== 'fixed' && style.position !== 'sticky') continue;
            if (rect.left < -EPS || rect.right > width + EPS || rect.top < -EPS || rect.bottom > window.innerHeight + EPS) {
              fixedOutsideViewport.push({
                tag: el.tagName.toLowerCase(),
                text: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 80),
                left: Math.round(rect.left), right: Math.round(rect.right),
                top: Math.round(rect.top), bottom: Math.round(rect.bottom)
              });
            }
          }

          return {
            viewport: {width, height: window.innerHeight},
            documentWidth: root.scrollWidth,
            bodyWidth: body ? body.scrollWidth : 0,
            horizontalOverflow: Math.max(root.scrollWidth, body ? body.scrollWidth : 0) > width + EPS,
            svgTextOutsideViewport,
            nowrapOverflow,
            fixedOutsideViewport
          };
        }"""
    )


def audit_page(page: Page, base: str, route: str) -> dict[str, object]:
    runtime_errors: list[str] = []
    console_errors: list[str] = []
    failed_local_requests: list[str] = []

    def on_page_error(error: object) -> None:
        runtime_errors.append(str(error))

    def on_console(message: object) -> None:
        if getattr(message, "type", "") == "error":
            text = getattr(message, "text", "")
            if text and "favicon" not in text.lower():
                console_errors.append(text)

    def on_request_failed(request: object) -> None:
        url = getattr(request, "url", "")
        if url.startswith(base):
            failure = getattr(request, "failure", None)
            failed_local_requests.append(f"{url}: {failure or 'request failed'}")

    page.on("pageerror", on_page_error)
    page.on("console", on_console)
    page.on("requestfailed", on_request_failed)

    response = page.goto(urljoin(base, route), wait_until="domcontentloaded", timeout=15000)
    require(response is not None, f"{route or '/'}: nessuna risposta HTTP")
    require(response.status < 400, f"{route or '/'}: HTTP {response.status}")
    wait_for_page(page)

    findings = browser_findings(page)
    require(not findings["horizontalOverflow"], f"{route or '/'}: overflow orizzontale del documento: {findings}")
    require(not findings["svgTextOutsideViewport"], f"{route or '/'}: testo SVG fuori viewport: {findings['svgTextOutsideViewport'][:8]}")
    require(not findings["nowrapOverflow"], f"{route or '/'}: testo nowrap troncato: {findings['nowrapOverflow'][:8]}")
    require(not findings["fixedOutsideViewport"], f"{route or '/'}: controllo fixed/sticky fuori viewport: {findings['fixedOutsideViewport'][:8]}")
    require(not runtime_errors, f"{route or '/'}: errori JavaScript: {runtime_errors[:5]}")
    require(not failed_local_requests, f"{route or '/'}: risorse locali fallite: {failed_local_requests[:5]}")

    findings["consoleErrors"] = console_errors
    return findings


def run_gate(base: str, dist: Path, output_dir: Path) -> None:
    routes = discover_routes(dist)
    middle_routes = representative_routes(routes)
    output_dir.mkdir(parents=True, exist_ok=True)
    failures: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    audited = 0
    coverage: dict[str, int] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for viewport_name, width, height, full_coverage in VIEWPORTS:
            routes_for_viewport = routes if full_coverage else middle_routes
            coverage[viewport_name] = len(routes_for_viewport)
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
                reduced_motion="reduce",
            )
            for route in routes_for_viewport:
                audited += 1
                label = route or "/"
                page = context.new_page()
                page.set_default_timeout(6000)
                try:
                    findings = audit_page(page, base, route)
                    if findings.get("consoleErrors"):
                        warnings.append({
                            "route": label,
                            "viewport": viewport_name,
                            "consoleErrors": findings["consoleErrors"],
                        })
                except Exception as exc:  # noqa: BLE001 - raccogliamo tutte le regressioni in una sola esecuzione
                    shot = output_dir / f"{viewport_name}-{safe_name(route)}.png"
                    try:
                        page.screenshot(path=str(shot), full_page=True, animations="disabled")
                    except Exception:
                        shot = None
                    failures.append({
                        "route": label,
                        "viewport": viewport_name,
                        "width": width,
                        "height": height,
                        "error": str(exc),
                        "screenshot": str(shot) if shot else None,
                    })
                finally:
                    page.close()
            context.close()
        browser.close()

    report = {
        "totalPublicRoutes": len(routes),
        "coverageByViewport": coverage,
        "auditedCombinations": audited,
        "failures": failures,
        "warnings": warnings,
    }
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if failures:
        preview = "\n".join(
            f"- {item['viewport']} {item['route']}: {item['error']}"
            for item in failures[:20]
        )
        raise AssertionError(
            f"Browser Quality Gate fallito: {len(failures)} regressioni su {audited} combinazioni.\n{preview}\n"
            f"Report completo: {output_dir / 'report.json'}"
        )

    print(
        "Browser Quality Gate passed: "
        f"{len(routes)} pagine complete su mobile+desktop; "
        f"{len(middle_routes)} route rappresentative su tablet+laptop; "
        f"{audited} controlli complessivi."
    )
    if warnings:
        print(f"Avvisi console non bloccanti registrati: {len(warnings)} (vedi report.json).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Base URL del server locale, es. http://127.0.0.1:8123/")
    parser.add_argument("--dist", default=str(DEFAULT_DIST), help="Directory della build statica")
    parser.add_argument("--output-dir", default="reports/browser-quality", help="Directory report e screenshot")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_gate(
        args.base.rstrip("/") + "/",
        Path(args.dist).resolve(),
        Path(args.output_dir).resolve(),
    )


if __name__ == "__main__":
    main()
