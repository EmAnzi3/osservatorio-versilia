#!/usr/bin/env python3
"""Materializza il Radar nella route definitiva, ma solo nella build di collaudo.

La route resta noindex e fuori dalla sitemap. Per rendere il collaudo utile, la
build locale simula anche la futura collocazione pubblica del Radar in header,
home e footer. Il normale workflow Pages non invoca questo script.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import build_opportunity_preview_v04 as route_builder
import build_opportunity_preview_v043 as radar_v043

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "reports" / "runtime" / "opportunities-v04.json"
DEFAULT_DIST = ROOT / "dist"
TARGET_ROUTE = "opportunita"
RUNTIME_ASSET = "opportunity-integration-runtime.js"


def _route_href(path: Path, dist: Path) -> str:
    relative = os.path.relpath(dist / TARGET_ROUTE, path.parent).replace(os.sep, "/")
    if relative == ".":
        return "./"
    return relative.rstrip("/") + "/"


def _runtime_href(path: Path, dist: Path) -> str:
    return os.path.relpath(dist / "assets" / RUNTIME_ASSET, path.parent).replace(os.sep, "/")


def _inject_header_link(text: str, href: str, *, current: bool = False) -> str:
    if 'data-opportunity-nav="header"' in text:
        return text
    current_attr = ' aria-current="page"' if current else ""
    link = f'<a href="{href}" data-opportunity-nav="header"{current_attr}>Opportunità</a>'
    pattern = re.compile(
        r'(<nav\b[^>]*aria-label="Navigazione principale"[^>]*>.*?<a\b[^>]*>\s*Comuni\s*</a>)',
        flags=re.IGNORECASE | re.DOTALL,
    )
    text, count = pattern.subn(rf"\1\n              {link}", text, count=1)
    if count != 1:
        raise RuntimeError("Impossibile collocare Opportunità dopo Comuni nell'header")
    return text


def _inject_footer_link(text: str, href: str, *, current: bool = False) -> str:
    if 'data-opportunity-nav="footer"' in text:
        return text
    current_attr = ' aria-current="page"' if current else ""
    link = f'<a href="{href}" data-opportunity-nav="footer"{current_attr}>Opportunità</a>'
    text = text.replace(
        'class="footer-links" aria-label="Informazioni sul progetto"',
        'class="footer-links" aria-label="Navigazione e informazioni"',
        1,
    )
    pattern = re.compile(
        r'(<nav\b[^>]*class="[^"]*footer-links[^"]*"[^>]*>)',
        flags=re.IGNORECASE,
    )
    text, count = pattern.subn(rf"\1\n          {link}", text, count=1)
    if count != 1:
        raise RuntimeError("Impossibile collocare Opportunità nel footer")
    return text


def _home_callout(total: int, configured: int, *, absolute_href: bool = False) -> str:
    source_copy = f"{configured} fonti monitorate" if configured else "una rete di fonti pubbliche monitorate"
    href = "/opportunita/" if absolute_href else "opportunita/"
    return f"""<section class="project-callout page-width opportunity-home-callout" aria-labelledby="opportunita-home-title" data-opportunity-home-link>
      <div><span class="overline">Nuovo strumento</span><h2 id="opportunita-home-title">Radar Opportunità</h2></div>
      <div><p>Finanziamenti, bandi e programmi utili ai Comuni della Versilia. Oggi il Radar raccoglie <strong>{total} opportunità correnti</strong> da <strong>{source_copy}</strong>, con fonte ufficiale e requisiti di accesso.</p><a class="text-link" href="{href}">Esplora le opportunità <b>→</b></a></div>
    </section>"""


def _inject_home_callout(text: str, total: int, configured: int) -> str:
    if "data-opportunity-home-link" in text:
        return text
    pattern = re.compile(
        r'(<section\b[^>]*class="[^"]*towns-section[^"]*"[^>]*id="comuni"[^>]*>.*?</section>)',
        flags=re.IGNORECASE | re.DOTALL,
    )
    text, count = pattern.subn(rf"\1\n{_home_callout(total, configured)}", text, count=1)
    if count != 1:
        raise RuntimeError("Impossibile collocare il Radar in home dopo i Comuni")
    return text


def _runtime_script(total: int, configured: int) -> str:
    """Mantiene la simulazione dopo il mount JS dell'app, solo nel dist di collaudo."""
    callout = json.dumps(_home_callout(total, configured, absolute_href=True), ensure_ascii=False)
    return f"""(() => {{
  'use strict';

  const OPPORTUNITY_PATH = '/opportunita/';
  const HOME_CALLOUT = {callout};
  const clean = value => String(value || '').replace(/\\s+/g, ' ').trim();
  const current = () => {{
    const path = location.pathname.replace(/\\/index\\.html$/, '/').replace(/\\/+$/, '/') || '/';
    return path === OPPORTUNITY_PATH;
  }};

  function ensureHeader() {{
    const nav = document.querySelector('header nav[aria-label="Navigazione principale"]');
    if (!nav) return false;
    const links = [...nav.querySelectorAll('a')];
    let opportunity = links.find(a => clean(a.textContent) === 'Opportunità');
    if (!opportunity) {{
      const comuni = links.find(a => clean(a.textContent) === 'Comuni');
      if (!comuni) return false;
      opportunity = document.createElement('a');
      opportunity.href = OPPORTUNITY_PATH;
      opportunity.dataset.opportunityNav = 'header';
      opportunity.textContent = 'Opportunità';
      comuni.insertAdjacentElement('afterend', opportunity);
    }}
    opportunity.dataset.opportunityNav = 'header';
    if (current()) opportunity.setAttribute('aria-current', 'page');
    else opportunity.removeAttribute('aria-current');
    return true;
  }}

  function ensureFooter() {{
    const nav = document.querySelector('footer .footer-links');
    if (!nav) return false;
    const links = [...nav.querySelectorAll('a')];
    let opportunity = links.find(a => clean(a.textContent) === 'Opportunità');
    if (!opportunity) {{
      opportunity = document.createElement('a');
      opportunity.href = OPPORTUNITY_PATH;
      opportunity.dataset.opportunityNav = 'footer';
      opportunity.textContent = 'Opportunità';
      nav.insertBefore(opportunity, nav.firstElementChild);
    }}
    opportunity.dataset.opportunityNav = 'footer';
    if (current()) opportunity.setAttribute('aria-current', 'page');
    else opportunity.removeAttribute('aria-current');
    return true;
  }}

  function ensureHome() {{
    if ((document.body?.dataset.page || '') !== 'home') return true;
    if (document.querySelector('section.opportunity-home-callout')) return true;
    const towns = document.querySelector('section.towns-section#comuni');
    if (!towns) return false;
    const template = document.createElement('template');
    template.innerHTML = HOME_CALLOUT.trim();
    const callout = template.content.firstElementChild;
    if (!callout) return false;
    towns.insertAdjacentElement('afterend', callout);
    return true;
  }}

  let scheduled = false;
  function ensurePlacement() {{
    scheduled = false;
    const ok = ensureHeader() && ensureFooter() && ensureHome();
    if (ok) document.documentElement.dataset.opportunityIntegrationReady = '1';
  }}
  function schedule() {{
    if (scheduled) return;
    scheduled = true;
    queueMicrotask(ensurePlacement);
  }}

  new MutationObserver(schedule).observe(document.documentElement, {{ childList: true, subtree: true }});
  document.addEventListener('DOMContentLoaded', schedule, {{ once: true }});
  window.addEventListener('load', schedule, {{ once: true }});
  schedule();
}})();
"""


def _inject_runtime_script(text: str, src: str) -> str:
    marker = f'<script src="{src}" data-opportunity-integration-runtime defer></script>'
    if "data-opportunity-integration-runtime" in text:
        return text
    if "</body>" not in text:
        raise RuntimeError("Pagina HTML senza </body>: impossibile iniettare il runtime di collaudo")
    return text.replace("</body>", f"  {marker}\n</body>", 1)


def _simulate_public_placement(dist: Path, total: int, configured: int) -> None:
    """Mostra nello ZIP la futura collocazione anche dopo il mount client-side."""
    asset_dir = dist / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / RUNTIME_ASSET).write_text(_runtime_script(total, configured), encoding="utf-8")

    target = (dist / TARGET_ROUTE / "index.html").resolve()
    for path in dist.rglob("*.html"):
        if path.name == "offline.html":
            continue
        text = path.read_text(encoding="utf-8")
        href = _route_href(path, dist)
        current_page = path.resolve() == target
        if 'aria-label="Navigazione principale"' in text:
            text = _inject_header_link(text, href, current=current_page)
        if "footer-links" in text:
            text = _inject_footer_link(text, href, current=current_page)
        if path.resolve() == (dist / "index.html").resolve():
            text = _inject_home_callout(text, total, configured)
        text = _inject_runtime_script(text, _runtime_href(path, dist))
        path.write_text(text, encoding="utf-8")


def build(payload_path: Path, dist: Path) -> Path:
    route_builder.TARGET_ROUTE = TARGET_ROUTE
    target = radar_v043.build(payload_path, dist)

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    total = len(payload.get("opportunities") or [])
    configured = int((((payload.get("sourceCoverage") or {}).get("summary") or {}).get("configured")) or 0)

    text = target.read_text(encoding="utf-8")
    text = text.replace(
        "<title>Anteprima Radar Opportunità · Osservatorio Versilia</title>",
        "<title>Radar Opportunità · Collaudo · Osservatorio Versilia</title>",
        1,
    )
    text = text.replace(
        'content="Anteprima non pubblica del Radar Opportunità Versilia v0.4.3."',
        'content="Collaudo non pubblico del Radar Opportunità per i Comuni della Versilia."',
        1,
    )
    text = text.replace(
        "Radar opportunità · Anteprima v0.4.3",
        "Radar opportunità · Collaudo integrazione",
        1,
    )
    text = text.replace(
        "<strong>Anteprima tecnica, non pubblicata.</strong> La route è fuori dalla sitemap e dalla navigazione pubblica.",
        "<strong>Pagina di collaudo, non pubblicata.</strong> In questo ZIP vedi la futura collocazione in header, home e footer; il sito pubblico non è stato modificato.",
        1,
    )
    target.write_text(text, encoding="utf-8")

    _simulate_public_placement(dist, total, configured)

    check = target.read_text(encoding="utf-8")
    if 'name="robots" content="noindex,nofollow,noarchive"' not in check:
        raise SystemExit("Il Radar di collaudo deve restare noindex/nofollow/noarchive")
    if "Radar opportunità · Collaudo integrazione" not in check:
        raise SystemExit("Etichetta di collaudo non materializzata")
    if "Tutte le fonti monitorate" not in check:
        raise SystemExit("Filtro Fonti completo assente")
    if 'data-opportunity-nav="header"' not in check or 'data-opportunity-nav="footer"' not in check:
        raise SystemExit("Collocazione futura del Radar non visibile in header/footer")
    if "data-opportunity-integration-runtime" not in check:
        raise SystemExit("Runtime di collocazione futura non iniettato")

    runtime = dist / "assets" / RUNTIME_ASSET
    if not runtime.exists() or runtime.stat().st_size == 0:
        raise SystemExit("Runtime di integrazione non materializzato")

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8") if (dist / "sitemap.xml").exists() else ""
    if "https://osservatorioversilia.it/opportunita/" in sitemap:
        raise SystemExit("/opportunita/ non deve ancora comparire nella sitemap")

    home = dist / "index.html"
    home_text = home.read_text(encoding="utf-8") if home.exists() else ""
    if 'data-opportunity-home-link' not in home_text or 'href="opportunita/"' not in home_text:
        raise SystemExit("La simulazione deve mostrare il Radar anche in home")
    if "data-opportunity-integration-runtime" not in home_text:
        raise SystemExit("Runtime di integrazione assente dalla home")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()
    print(f"Radar integrato in modalità collaudo: {build(args.data, args.dist)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
