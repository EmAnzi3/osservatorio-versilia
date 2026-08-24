#!/usr/bin/env python3
"""Materializza la preview v0.4.2 coverage-first sopra il renderer v0.3."""
from __future__ import annotations

import argparse
import html
import re
import shutil
from pathlib import Path
from typing import Any

import build_opportunity_preview_v03 as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "reports" / "runtime" / "opportunities-v04.json"
DEFAULT_DIST = ROOT / "dist"
TARGET_ROUTE = "opportunita-preview"

_ORIGINAL_BASE_CARD = base.BASE_CARD
LIFECYCLE = {
    "application_open": ("Aperta", "open"),
    "rolling_open": ("A sportello", "rolling"),
    "announced_upcoming": ("In arrivo", "upcoming"),
}


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def lifecycle_card(item: dict[str, Any]) -> str:
    text = _ORIGINAL_BASE_CARD(item)
    stage = str(item.get("lifecycle_stage") or "application_open")
    label, css = LIFECYCLE.get(stage, (stage, "neutral"))
    text = text.replace(
        '<article class="op-card"',
        f'<article class="op-card" data-lifecycle="{esc(stage)}"',
        1,
    )
    badge = f'<span class="op-lifecycle op-lifecycle-{css}">{esc(label)}</span>'
    text = text.replace('<div class="op-card-heading">', f'<div class="op-card-heading">{badge}', 1)
    if stage == "rolling_open":
        text = text.replace(
            '<div class="op-deadline"><dt>Scadenza</dt><dd>Non rilevata</dd></div>',
            '<div class="op-deadline"><dt>Accesso</dt><dd>A sportello</dd></div>',
            1,
        )
    elif stage == "announced_upcoming":
        text = text.replace(
            '<div class="op-deadline"><dt>Scadenza</dt><dd>Non rilevata</dd></div>',
            '<div class="op-deadline"><dt>Stato</dt><dd>In arrivo</dd></div>',
            1,
        )
    return text


def _overview(payload: dict[str, Any]) -> str:
    opportunities = list(payload.get("opportunities") or [])
    archive = list(payload.get("archive") or [])
    coverage = payload.get("sourceCoverage") or {}
    summary = coverage.get("summary") or {}
    audit = payload.get("coverageAudit") or {}
    independent = payload.get("independentAudit") or {}
    gap = independent.get("knownGapClosure") or {}
    prospective = independent.get("prospective") or {}
    holdouts = independent.get("holdouts") or {}
    stages = payload.get("lifecycleSummary") or {}
    opened = int(stages.get("application_open") or sum(str(x.get("lifecycle_stage") or "application_open") == "application_open" for x in opportunities))
    rolling = int(stages.get("rolling_open") or sum(str(x.get("lifecycle_stage")) == "rolling_open" for x in opportunities))
    upcoming = int(stages.get("announced_upcoming") or sum(str(x.get("lifecycle_stage")) == "announced_upcoming" for x in opportunities))
    monitored = int(summary.get("configured") or len(coverage.get("rows") or []))
    required_families = int(audit.get("requiredFamilies") or 0)
    covered_families = max(0, required_families - len(audit.get("missingFamilies") or []))
    holdout_count = int(holdouts.get("configured") or 0)
    holdout_healthy = int(holdouts.get("healthy") or 0)
    closed = int(gap.get("closed") or 0)
    gap_total = int(gap.get("total") or 0)
    sample = int(prospective.get("sampleSize") or 0)
    minimum = int(prospective.get("minimumSample") or 0)
    rate = prospective.get("captureRate")
    rate_text = "in raccolta" if rate is None else f"{float(rate):.1%}"
    icons = base.ICONS
    return f'''<section class="method-detail page-width op-overview" aria-label="Quadro operativo"><div class="op-overview-shell"><div class="op-overview-heading"><div><span class="section-number">01</span><h2>Quadro operativo</h2></div><p>Aperte, misure a sportello e procedure annunciate. La copertura è verificata anche con fonti di controllo che non alimentano il radar.</p></div><div class="op-overview-grid op-overview-grid-v04"><article class="op-stat op-stat-open"><span class="op-stat-icon">{icons['briefcase']}</span><div><small>Aperte</small><strong>{opened}</strong><span>Finestra di candidatura attiva</span></div></article><article class="op-stat"><span class="op-stat-icon">{icons['calendar']}</span><div><small>A sportello</small><strong>{rolling}</strong><span>Misure senza singola scadenza</span></div></article><article class="op-stat"><span class="op-stat-icon">{icons['radar']}</span><div><small>In arrivo</small><strong>{upcoming}</strong><span>Procedure annunciate ufficialmente</span></div></article><article class="op-stat op-stat-sources"><span class="op-stat-icon">{icons['radar']}</span><div><small>Rete di raccolta</small><strong>{monitored}</strong><span>{required_families} famiglie · {holdout_count} fonti di controllo separate</span></div></article><article class="op-stat op-stat-towns"><span class="op-stat-icon">{icons['map']}</span><div><small>Famiglie presidiate</small><strong>{covered_families}/{required_families}</strong><span>Il dato non equivale alla completezza del web</span></div></article><article class="op-stat op-stat-archive"><span class="op-stat-icon">{icons['archive']}</span><div><small>In archivio</small><strong>{len(archive)}</strong><span>Opportunità chiuse con fonte ufficiale</span></div></article></div><div class="op-audit-summary"><strong>Audit indipendente</strong><span>{closed}/{gap_total} buchi baseline chiusi · capture rate prospettico: {rate_text} ({sample}/{minimum}) · fonti di controllo raggiungibili: {holdout_healthy}/{holdout_count}</span></div></div></section>'''


def _recent_controls(payload: dict[str, Any]) -> str:
    opportunities = list(payload.get("opportunities") or [])
    if not any(item.get("first_seen_at") or item.get("is_new") for item in opportunities):
        return ""
    return (
        '<label>Novità<select data-op-new>'
        '<option value="">Tutte</option>'
        '<option value="new">Solo nuove</option>'
        '</select></label>'
        '<label>Ordina<select data-op-sort>'
        '<option value="deadline">Scadenza</option>'
        '<option value="recent">Più recenti</option>'
        '</select></label>'
    )


def render_page(payload: dict[str, Any]) -> str:
    previous = base.BASE_CARD
    base.BASE_CARD = lifecycle_card
    base.old.ROLE_LABELS["direct_or_partner"] = "Candidatura diretta (ove ammessa) o partner"
    try:
        page = base.render_page(payload)
    finally:
        base.BASE_CARD = previous

    page = page.replace("v0.3", "v0.4.2")
    page = page.replace(
        '<link rel="stylesheet" href="../assets/opportunity-preview-v03.css">',
        '<link rel="stylesheet" href="../assets/opportunity-preview-v03.css">\n  <link rel="stylesheet" href="../assets/opportunity-preview-v04.css">',
        1,
    )
    page = re.sub(
        r'\s*<script src="\.\./assets/opportunity-preview(?:-v03)?\.js" defer></script>',
        "",
        page,
    )
    page = page.replace("</body>", '  <script src="../assets/opportunity-preview-v04.js" defer></script>\n</body>', 1)
    page = re.sub(
        r'<section class="method-detail page-width op-overview" aria-label="Quadro operativo">.*?</section>',
        _overview(payload),
        page,
        count=1,
        flags=re.S,
    )
    page = re.sub(
        r'\s*<div class="op-source-shortcuts".*?</div>\s*(?=<div class="op-preview-controls">)',
        "\n      ",
        page,
        count=1,
        flags=re.S,
    )
    lifecycle_filter = (
        '<label>Stato<select data-op-lifecycle>'
        '<option value="">Tutti gli stati</option>'
        '<option value="application_open">Aperte</option>'
        '<option value="rolling_open">A sportello</option>'
        '<option value="announced_upcoming">In arrivo</option>'
        '</select></label>'
    )
    page = page.replace('<label>Modalità<select data-op-access>', lifecycle_filter + '<label>Modalità<select data-op-access>', 1)
    recent_controls = _recent_controls(payload)
    if recent_controls:
        page = page.replace('<label class="op-search-field">Cerca<input type="search"', recent_controls + '<label class="op-search-field">Cerca<input type="search"', 1)
    page = page.replace(
        'Filtra per Comune, fonte o modalità di partecipazione.',
        'Filtra per Comune, stato, modalità, fonte o ricerca libera.',
        1,
    )
    page = page.replace(
        'Bandi e linee di finanziamento con un <strong>ruolo operativo documentato</strong> per almeno un Comune della Versilia.',
        'Bandi, avvisi, incentivi e opportunità operative con un <strong>ruolo documentato</strong> per almeno un Comune della Versilia.',
        1,
    )
    return page


def build(payload_path: Path, dist: Path) -> Path:
    if not (dist / "progetto" / "index.html").exists():
        raise SystemExit("Build statica canonica assente: eseguire prima scripts/build_static_brand.py")
    payload = base.old.load_payload(payload_path)
    target = dist / TARGET_ROUTE / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_page(payload), encoding="utf-8")

    assets_dir = dist / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for name in ("opportunity-preview-v04.css", "opportunity-preview-v04.js"):
        shutil.copy2(ROOT / "assets" / name, assets_dir / name)

    try:
        base.synchronize_native_page(dist, target)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8") if (dist / "sitemap.xml").exists() else ""
    if TARGET_ROUTE in sitemap:
        raise SystemExit("La preview non deve comparire nella sitemap")
    text = target.read_text(encoding="utf-8")
    if 'Anteprima v0.4.2' not in text or 'name="robots" content="noindex,nofollow,noarchive"' not in text:
        raise SystemExit("Preview v0.4.2/noindex non materializzata correttamente")
    for token in ("Quality gate", ">Da verificare<", "discoveryQueue", "coverageHold"):
        if token in text:
            raise SystemExit(f"La preview espone ancora un concetto tecnico interno: {token}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()
    print(f"Preview opportunità v0.4.2 materializzata: {build(args.data, args.dist)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
