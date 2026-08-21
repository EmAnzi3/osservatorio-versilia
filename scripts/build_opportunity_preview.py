#!/usr/bin/env python3
"""Materializza la preview browser del Radar Opportunità v0.2.3.

Da eseguire dopo ``scripts/build_static.py`` e dopo il probe v0.2.2.
La route generata è intenzionalmente noindex e non viene aggiunta alla sitemap.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

from site_chrome import synchronize_native_page

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = ROOT / "dist"
DEFAULT_DATA = ROOT / "reports" / "runtime" / "opportunities-v022.json"
TARGET_ROUTE = "opportunita-preview"
TOWNS = (
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
)

STATUS_LABELS = {
    "eligible": "Opportunità diretta",
    "conditional": "Da verificare",
}
ROLE_LABELS = {
    "direct_applicant": "Candidatura diretta",
    "partner": "Partecipazione come partner",
    "implementing_body": "Ente attuatore / proponente",
    "system_member": "Tramite sistema / aggregazione",
    "lead_applicant": "Capofila",
    "intermediary": "Intermediario / attuatore",
}


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def slug(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def fmt_date(value: Any) -> str:
    text = str(value or "").strip()
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return text or "Non rilevata"
    return f"{parsed.day:02d}/{parsed.month:02d}/{parsed.year}"


def load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"JSON radar non valido: {path}")
    opportunities = payload.get("opportunities")
    if not isinstance(opportunities, list):
        raise SystemExit("Output radar privo della lista opportunities")
    return payload


def town_matrix(item: dict[str, Any]) -> dict[str, dict[str, Any]]:
    matrix = item.get("municipality_eligibility") or {}
    return matrix if isinstance(matrix, dict) else {}


def eligible_town_slugs(item: dict[str, Any]) -> list[str]:
    matrix = town_matrix(item)
    return [
        slug(town)
        for town in TOWNS
        if (matrix.get(town) or {}).get("status") in {"eligible", "conditional"}
    ]


def render_town_chips(item: dict[str, Any]) -> str:
    matrix = town_matrix(item)
    chips = []
    for town in TOWNS:
        entry = matrix.get(town) or {}
        status = str(entry.get("status") or "not_eligible")
        reason = str(entry.get("reason") or "Nessuna ammissibilità documentata per il prototipo.")
        chips.append(
            f'<li class="op-town-chip" data-town-chip="{esc(slug(town))}" '
            f'data-town-status="{esc(status)}" title="{esc(reason)}">{esc(town)}</li>'
        )
    return "".join(chips)


def evidence_text(item: dict[str, Any]) -> str:
    evidence = item.get("eligibility_evidence")
    if isinstance(evidence, dict):
        return str(evidence.get("text") or "")
    return ""


def card_markup(item: dict[str, Any]) -> str:
    status = str(item.get("eligibility") or "conditional")
    role = str(item.get("municipality_role") or "unknown")
    role_label = ROLE_LABELS.get(role, role.replace("_", " ").strip().capitalize() or "Da verificare")
    towns = eligible_town_slugs(item)
    requirements = str(item.get("project_requirements") or "").strip()
    evidence = evidence_text(item).strip()
    source_name = str(item.get("source_name") or item.get("publisher") or item.get("source_id") or "Fonte")
    scope = str(item.get("geographic_scope") or "Ambito non determinato")
    final_beneficiaries = str(item.get("final_beneficiaries") or "Non determinati")
    source_url = str(item.get("url") or (item.get("eligibility_evidence") or {}).get("source_url") or "#")
    search_blob = " ".join(
        str(value or "")
        for value in (
            item.get("title"), source_name, role_label, requirements, evidence, scope, final_beneficiaries,
        )
    )
    condition = (
        f'<div class="op-condition"><strong>Condizioni da verificare</strong>{esc(requirements)}</div>'
        if requirements and status == "conditional"
        else (
            f'<div class="op-condition"><strong>Condizione operativa</strong>{esc(requirements)}</div>'
            if requirements else ""
        )
    )
    evidence_markup = (
        f'<span class="op-evidence"><strong>Perché compare:</strong> {esc(evidence)}</span>'
        if evidence else '<span class="op-evidence"><strong>Perché compare:</strong> regola documentale validata nel prototipo.</span>'
    )
    return f'''<article class="op-card" data-opportunity-card data-status="{esc(status)}" data-towns="{esc('|'.join(towns))}" data-search="{esc(search_blob)}">
      <div class="op-card-top">
        <div class="op-card-heading">
          <span class="op-card-source">{esc(source_name)}</span>
          <h3>{esc(item.get('title'))}</h3>
        </div>
        <span class="op-status op-status-{esc(status)}">{esc(STATUS_LABELS.get(status, status))}</span>
      </div>
      <dl class="op-card-grid">
        <div><dt>Scadenza</dt><dd>{esc(fmt_date(item.get('deadline_at')))}</dd></div>
        <div><dt>Ruolo del Comune</dt><dd>{esc(role_label)}</dd></div>
        <div><dt>Ambito</dt><dd>{esc(scope)}</dd></div>
        <div><dt>Richiedente</dt><dd>{esc(item.get('applicant_type') or 'Da verificare')}</dd></div>
        <div><dt>Beneficiari finali</dt><dd>{esc(final_beneficiaries)}</dd></div>
        <div><dt>Quality gate</dt><dd>{esc((item.get('quality_gate') or {}).get('status') if isinstance(item.get('quality_gate'), dict) else 'pass')}</dd></div>
      </dl>
      {condition}
      <div class="op-town-block">
        <h4>Comuni della Versilia</h4>
        <ul class="op-town-list">{render_town_chips(item)}</ul>
      </div>
      <div class="op-card-foot">
        {evidence_markup}
        <a class="op-source-link" href="{esc(source_url)}" target="_blank" rel="noopener noreferrer">Apri fonte ufficiale</a>
      </div>
    </article>'''


def render_page(payload: dict[str, Any]) -> str:
    opportunities = list(payload.get("opportunities") or [])
    opportunities.sort(key=lambda item: (str(item.get("deadline_at") or "9999-99-99"), str(item.get("title") or "")))
    eligible = sum(1 for item in opportunities if item.get("eligibility") == "eligible")
    conditional = sum(1 for item in opportunities if item.get("eligibility") == "conditional")
    cards = "\n".join(card_markup(item) for item in opportunities)
    town_options = "".join(f'<option value="{esc(slug(town))}">{esc(town)}</option>' for town in TOWNS)
    reference = fmt_date(payload.get("referenceDate"))

    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Anteprima Radar Opportunità · Osservatorio Versilia</title>
  <meta name="description" content="Anteprima non pubblica del Radar Opportunità Versilia v0.2.3.">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="manifest" href="../site.webmanifest">
  <link rel="stylesheet" href="../assets/opportunity-preview.css">
  <meta name="theme-color" content="#0F3654">
</head>
<body class="antialiased" data-page="special" data-theme="" data-town="" data-prerendered="true">
  <div id="site-header-mount"></div>
  <div id="app"><main class="editorial-page op-preview-main" data-opportunity-preview>
    <section class="editorial-hero page-width op-preview-hero">
      <span class="overline">Radar opportunità · Anteprima v0.2.3</span>
      <h1>Opportunità per i Comuni della Versilia.</h1>
      <p>Questa vista mostra soltanto le opportunità che hanno superato il controllo su <strong>richiedente</strong>, <strong>ruolo del Comune</strong>, <strong>geografia</strong>, <strong>pertinenza territoriale</strong> e <strong>completezza minima</strong>.</p>
      <div class="op-preview-banner"><strong>Anteprima tecnica, non pubblicata.</strong> Questa route non entra nella sitemap e non deve essere considerata una sezione attiva del sito.</div>
      <div class="op-preview-meta"><div><span>Dati verificati al</span><strong>{esc(reference)}</strong></div><div><span>Versione motore</span><strong>Radar v0.2.2 · UI v0.2.3</strong></div></div>
    </section>

    <section class="method-detail page-width" aria-label="Riepilogo opportunità">
      <div class="section-heading"><div><span class="section-number">01</span><h2>Quadro operativo</h2></div><p>Il conteggio riguarda il campione corrente del prototipo, non l'universo di tutti i bandi disponibili.</p></div>
      <ol class="principles-grid op-preview-summary">
        <li><span>01</span><h3>Opportunità</h3><strong>{len(opportunities)}</strong></li>
        <li><span>02</span><h3>Dirette</h3><strong>{eligible}</strong></li>
        <li><span>03</span><h3>Condizionate</h3><strong>{conditional}</strong></li>
        <li><span>04</span><h3>Review residua</h3><strong>{int((payload.get('counts') or {}).get('reviewInternal', 0))}</strong></li>
      </ol>
    </section>

    <section class="method-detail page-width">
      <div class="section-heading"><div><span class="section-number">02</span><h2>Filtra le opportunità</h2></div><p>Selezionando un Comune restano visibili solo i bandi per cui quel Comune ha un canale operativo documentato.</p></div>
      <div class="op-preview-controls">
        <label>Comune<select data-op-town><option value="">Tutta la Versilia</option>{town_options}</select></label>
        <label>Stato<select data-op-status><option value="">Tutti gli stati</option><option value="eligible">Opportunità dirette</option><option value="conditional">Da verificare</option></select></label>
        <label class="op-search-field">Cerca<input type="search" data-op-search placeholder="Titolo, fonte, ambito…" autocomplete="off"></label>
        <button class="op-preview-reset" type="button" data-op-reset>Reimposta</button>
      </div>
      <div class="op-preview-resultbar" aria-live="polite"><strong data-op-visible>{len(opportunities)} opportunità visibili</strong><span data-op-context>Tutta la Versilia · tutti gli stati</span></div>
    </section>

    <section class="method-detail page-width" aria-label="Elenco opportunità">
      <div class="section-heading"><div><span class="section-number">03</span><h2>Scadenze e condizioni</h2></div><p>Le schede sono ordinate per scadenza. Passando sui Comuni si legge la motivazione puntuale della classificazione.</p></div>
      <div class="op-preview-list">{cards}</div>
      <div class="op-preview-empty" data-op-empty hidden>Nessuna opportunità corrisponde ai filtri selezionati.</div>
      <div class="op-preview-legend">
        <article><h3><span class="op-status op-status-eligible">Opportunità diretta</span></h3><p>Il Comune ha un ruolo operativo documentato e i requisiti generali risultano compatibili, fermo restando il controllo del progetto concreto.</p></article>
        <article><h3><span class="op-status op-status-conditional">Da verificare</span></h3><p>Il Comune può lavorare l'opportunità, ma deve soddisfare una condizione specifica: partenariato, bene ammissibile, appartenenza a un sistema o altro requisito sostanziale.</p></article>
      </div>
    </section>
  </main></div>
  <div id="site-footer-mount"></div>
  <noscript><div class="app-error">I filtri della preview richiedono JavaScript; tutte le schede restano comunque leggibili.</div></noscript>
  <script src="../assets/opportunity-preview.js" defer></script>
</body>
</html>
'''


def build(payload_path: Path, dist: Path) -> Path:
    if not (dist / "progetto" / "index.html").exists():
        raise SystemExit("Build statica canonica assente: eseguire prima scripts/build_static.py")
    payload = load_payload(payload_path)
    target = dist / TARGET_ROUTE / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_page(payload), encoding="utf-8")
    try:
        synchronize_native_page(dist, target)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8") if (dist / "sitemap.xml").exists() else ""
    if "opportunita-preview" in sitemap:
        raise SystemExit("La preview non deve comparire nella sitemap")
    text = target.read_text(encoding="utf-8")
    if 'name="robots" content="noindex,nofollow,noarchive"' not in text:
        raise SystemExit("Meta robots noindex assente dalla preview")
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = build(args.data, args.dist)
    print(f"Preview opportunità v0.2.3 materializzata: {target}")


if __name__ == "__main__":
    main()
