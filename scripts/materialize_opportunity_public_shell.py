#!/usr/bin/env python3
"""Materializza il Radar come elemento pubblico della shell canonica."""
from __future__ import annotations
import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "opportunity-public-release-v1"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: punto di aggancio non univoco ({count}) in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def materialize_economia_atlas_release_if_needed() -> None:
    """Materializza v1.31.0 nel checkout effimero usato dal deploy Pages di main."""
    if not (
        os.environ.get("GITHUB_WORKFLOW") == "Deploy GitHub Pages"
        and os.environ.get("GITHUB_EVENT_NAME") in {"push", "workflow_dispatch"}
        and os.environ.get("GITHUB_REF") == "refs/heads/main"
    ):
        return

    for script in (
        "prepare_economy_atlas_build.py",
        "materialize_economy_atlas_release.py",
        "refine_economy_atlas_release.py",
        "refine_economy_atlas_tooltips.py",
        "refine_economy_atlas_exports.py",
    ):
        runpy.run_path(str(ROOT / "scripts" / script), run_name="__main__")


def main() -> None:
    core = ROOT / "assets/app-parts/00.txt"
    replace_once(core,
        '              <a href="${route(\'#comuni\')}">Comuni</a>\n              <a href="${route(\'progetto/\')}">Il progetto</a>',
        '              <a href="${route(\'#comuni\')}">Comuni</a>\n              <a href="${route(\'opportunita/\')}">Opportunità</a>\n              <a href="${route(\'progetto/\')}">Il progetto</a>',
        "header Opportunità")
    replace_once(core,
        '          <a href="${route(\'stato-dati/\')}" data-data-status-nav="footer">Stato dei dati</a>\n          <a href="${route(\'progetto/#metodo\')}">Metodo</a>',
        '          <a href="${route(\'stato-dati/\')}" data-data-status-nav="footer">Stato dei dati</a>\n          <a href="${route(\'opportunita/\')}">Opportunità</a>\n          <a href="${route(\'progetto/#metodo\')}">Metodo</a>',
        "footer Opportunità")

    home = ROOT / "assets/app-parts/01.txt"
    replace_once(home,
        '''        <div class="town-card-grid">${data.towns.map(t => townCard(data, t)).join('')}</div></section>
      <section class="method-section page-width" id="metodo">''',
        '''        <div class="town-card-grid">${data.towns.map(t => townCard(data, t)).join('')}</div></section>
      <section class="project-callout page-width opportunity-home-callout" aria-labelledby="opportunita-home-title">
        <div><span class="overline">Opportunità per il territorio</span><h2 id="opportunita-home-title">Radar Opportunità</h2></div>
        <div><p>Bandi, avvisi, incentivi e programmi utili ai Comuni della Versilia, raccolti da fonti pubbliche e accompagnati dal rimando alla fonte ufficiale.</p><a class="text-link" href="${route('opportunita/')}">Esplora le opportunità <b>→</b></a></div></section>
      <section class="method-section page-width" id="metodo">''',
        "Radar in home")

    chrome = ROOT / "scripts/site_chrome.py"
    replace_once(chrome,
        'HEADER_LINK_LABELS = ("Temi", "Comuni", "Il progetto", "Stato dati", "Segnala")',
        'HEADER_LINK_LABELS = ("Temi", "Comuni", "Opportunità", "Il progetto", "Stato dati", "Segnala")',
        "contratto header")
    replace_once(chrome, '    "Stato dei dati",\n    "Metodo",', '    "Stato dei dati",\n    "Opportunità",\n    "Metodo",', "contratto footer")

    t = ROOT / "scripts/test_site_chrome.py"
    replace_once(t,
        '<a href="../#temi">Temi</a><a href="../#comuni">Comuni</a><a href="../progetto/">Il progetto</a>',
        '<a href="../#temi">Temi</a><a href="../#comuni">Comuni</a><a href="../opportunita/">Opportunità</a><a href="../progetto/">Il progetto</a>',
        "fixture header")
    replace_once(t,
        '<a href="../stato-dati/" data-data-status-nav="footer">Stato dei dati</a><a href="../progetto/#metodo">Metodo</a>',
        '<a href="../stato-dati/" data-data-status-nav="footer">Stato dei dati</a><a href="../opportunita/">Opportunità</a><a href="../progetto/#metodo">Metodo</a>',
        "fixture footer")

    c = ROOT / "scripts/test_site_consistency.py"
    replace_once(c, '    Path("stato-dati/index.html"),\n    Path("percorsi/index.html"),', '    Path("stato-dati/index.html"),\n    Path("opportunita/index.html"),\n    Path("percorsi/index.html"),', "inventario")
    replace_once(c, '        ("Comuni", BASE_URL + "#comuni"),\n        ("Il progetto", BASE_URL + "progetto/"),', '        ("Comuni", BASE_URL + "#comuni"),\n        ("Opportunità", BASE_URL + "opportunita/"),\n        ("Il progetto", BASE_URL + "progetto/"),', "header consistency")
    replace_once(c, '            ("Stato dei dati", BASE_URL + "stato-dati/"),\n            ("Metodo", BASE_URL + "progetto/#metodo"),', '            ("Stato dei dati", BASE_URL + "stato-dati/"),\n            ("Opportunità", BASE_URL + "opportunita/"),\n            ("Metodo", BASE_URL + "progetto/#metodo"),', "footer consistency")

    b = ROOT / "scripts/test_site_chrome_browser.py"
    replace_once(b, '    "pnrr/",\n    "percorsi/",', '    "pnrr/",\n    "opportunita/",\n    "percorsi/",', "browser route")
    replace_once(b, 'from test_lighthouse_budget import run_budget\n', 'from test_lighthouse_budget import run_budget\nfrom test_opportunity_release_browser import verify_release as verify_opportunity_release\n', "browser import")
    replace_once(b, '    verify_custom_404(base)\n    print("Chrome browser gate passed:', '    verify_custom_404(base)\n    verify_opportunity_release(base)\n    print("Chrome browser gate passed:', "browser release gate")

    css = ROOT / "assets/fidelity.css"
    text = css.read_text(encoding="utf-8")
    if MARK not in text:
        text += '''\n\n/* opportunity-public-release-v1 */
@media (max-width:700px){
.site-header-inner{gap:10px}.site-header-actions{flex:1 1 auto;min-width:0;gap:6px}
.site-header nav{flex:1 1 auto;min-width:0;gap:8px;overflow-x:auto;overflow-y:hidden;white-space:nowrap;scrollbar-width:none;-webkit-overflow-scrolling:touch;scroll-snap-type:x proximity;font-size:10px}
.site-header nav::-webkit-scrollbar{display:none}.site-header nav a,.site-header nav a:nth-child(n+3){display:inline-flex;flex:0 0 auto;scroll-snap-align:start}
.global-search-trigger{flex:0 0 38px}.site-brand{gap:8px}.site-brand-copy strong{font-size:12px}}
@media (max-width:380px){.site-brand-copy{display:none}.site-header-inner{width:min(100% - 20px,1240px)}}
'''
        css.write_text(text, encoding="utf-8")

    materialize_economia_atlas_release_if_needed()
    print("Shell pubblica Opportunità materializzata.")


if __name__ == "__main__":
    main()
