#!/usr/bin/env python3
"""Materializza la preview browser del Radar Opportunità v0.2.4.

La route è noindex e non viene aggiunta alla sitemap. I concetti interni
(review, quality gate, evidenza tecnica) non sono esposti nella UI.
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
DEFAULT_DATA = ROOT / "reports" / "runtime" / "opportunities-v024.json"
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

ROLE_LABELS = {
    "direct_applicant": "Candidatura diretta",
    "partner": "Partecipazione come partner",
    "implementing_body": "Ente attuatore / proponente",
    "system_member": "Partecipazione tramite sistema",
    "lead_applicant": "Capofila",
    "intermediary": "Ente intermediario / attuatore",
}
ACCESS_LABELS = {
    "direct": "Candidatura diretta",
    "specific_requirement": "Con requisito specifico",
}


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def slug(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def display_value(value: Any, fallback: str = "Non specificato") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return fallback
    return text[0].upper() + text[1:]


def fmt_date(value: Any, time_value: Any = None) -> str:
    text = str(value or "").strip()
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        formatted = text or "Non rilevata"
    else:
        formatted = f"{parsed.day:02d}/{parsed.month:02d}/{parsed.year}"
    time_text = str(time_value or "").strip()
    if re.fullmatch(r"\d{2}:\d{2}", time_text):
        formatted += f" · ore {time_text}"
    return formatted


def load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"JSON radar non valido: {path}")
    if not isinstance(payload.get("opportunities"), list):
        raise SystemExit("Output radar privo della lista opportunities")
    payload.setdefault("archive", [])
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
        reason = str(entry.get("reason") or "Nessuna ammissibilità documentata.")
        chips.append(
            f'<li class="op-town-chip" data-town-chip="{esc(slug(town))}" '
            f'data-town-status="{esc(status)}" title="{esc(reason)}">{esc(town)}</li>'
        )
    return "".join(chips)


def presentation(item: dict[str, Any]) -> dict[str, str]:
    meta = item.get("presentation") or {}
    source_label = str(meta.get("source_label") or item.get("publisher") or item.get("source_name") or "Fonte")
    mark = str(meta.get("source_mark") or "".join(part[0].upper() for part in source_label.split()[:3]))
    return {
        "source_label": source_label,
        "source_mark": mark or "F",
        "source_class": str(meta.get("source_class") or "other"),
        "category": str(meta.get("category") or "generale"),
        "description": str(meta.get("description") or item.get("summary") or "Consulta la fonte ufficiale per i dettagli."),
        "condition_label": str(meta.get("condition_label") or ""),
    }


def card_markup(item: dict[str, Any]) -> str:
    meta = presentation(item)
    access = str(item.get("access_mode") or ("specific_requirement" if item.get("eligibility") == "conditional" else "direct"))
    role = str(item.get("municipality_role") or "unknown")
    role_label = ROLE_LABELS.get(role, display_value(role.replace("_", " "), "Non specificato"))
    towns = eligible_town_slugs(item)
    requirements = display_value(item.get("project_requirements"), "")
    source_url = str(item.get("url") or (item.get("eligibility_evidence") or {}).get("source_url") or "#")
    applicant = display_value(item.get("applicant_type"))
    scope = display_value(item.get("geographic_scope"))
    final_beneficiaries = display_value(item.get("final_beneficiaries"))
    description = display_value(meta["description"], "")
    condition_label = display_value(meta["condition_label"], "") if access == "specific_requirement" else ""
    source_slug = slug(str(item.get("source_id") or meta["source_label"]))
    search_blob = " ".join(
        str(value or "")
        for value in (
            item.get("title"), meta["source_label"], meta["category"], role_label,
            requirements, applicant, scope, final_beneficiaries, description, condition_label,
        )
    )

    access_badge = (
        f'<span class="op-access op-access-specific">{esc(condition_label or ACCESS_LABELS["specific_requirement"])}</span>'
        if access == "specific_requirement"
        else '<span class="op-access op-access-direct">Candidatura diretta</span>'
    )
    condition = ""
    if access == "specific_requirement" and requirements:
        condition = (
            '<div class="op-condition">'
            f'<strong>{esc(condition_label or "Requisito specifico")}</strong>'
            f'<span>{esc(requirements)}</span>'
            "</div>"
        )

    return f"""<article class="op-card" data-opportunity-card data-category="{esc(meta['category'])}" data-source="{esc(source_slug)}" data-access="{esc(access)}" data-towns="{esc('|'.join(towns))}" data-search="{esc(search_blob)}">
      <div class="op-card-accent" aria-hidden="true"></div>
      <div class="op-card-top">
        <div class="op-source-id">
          <span class="op-source-mark op-source-{esc(meta['source_class'])}" aria-hidden="true">{esc(meta['source_mark'])}</span>
          <div><span class="op-source-kicker">Fonte</span><strong>{esc(meta['source_label'])}</strong></div>
        </div>
        {access_badge}
      </div>
      <div class="op-card-heading">
        <h3>{esc(item.get('title'))}</h3>
        <p class="op-description">{esc(description)}</p>
      </div>
      <dl class="op-card-grid">
        <div class="op-deadline"><dt>Scadenza</dt><dd>{esc(fmt_date(item.get('deadline_at'), item.get('deadline_time')))}</dd></div>
        <div><dt>Ruolo del Comune</dt><dd>{esc(role_label)}</dd></div>
        <div><dt>Chi presenta domanda</dt><dd>{esc(applicant)}</dd></div>
        <div><dt>Ambito</dt><dd>{esc(scope)}</dd></div>
      </dl>
      {condition}
      <div class="op-town-block">
        <h4>Comuni della Versilia</h4>
        <ul class="op-town-list">{render_town_chips(item)}</ul>
      </div>
      <div class="op-card-foot">
        <span class="op-final"><strong>Destinatari finali</strong>{esc(final_beneficiaries)}</span>
        <a class="op-source-link" href="{esc(source_url)}" target="_blank" rel="noopener noreferrer">Apri fonte ufficiale</a>
      </div>
    </article>"""


def archive_markup(item: dict[str, Any]) -> str:
    source = display_value(item.get("source_label") or item.get("source_id"), "Fonte")
    mark = display_value(item.get("source_mark"), "F")
    source_class = slug(str(item.get("source_class") or "other"))
    return f"""<li class="op-archive-row">
      <span class="op-source-mark op-source-{esc(source_class)}" aria-hidden="true">{esc(mark)}</span>
      <div class="op-archive-copy"><strong>{esc(item.get('title'))}</strong><span>{esc(source)} · Scadenza {esc(fmt_date(item.get('deadline_at'), item.get('deadline_time')))}</span></div>
      <a href="{esc(item.get('url') or '#')}" target="_blank" rel="noopener noreferrer">Fonte ufficiale</a>
    </li>"""


def render_page(payload: dict[str, Any]) -> str:
    opportunities = list(payload.get("opportunities") or [])
    opportunities.sort(key=lambda item: (str(item.get("deadline_at") or "9999-99-99"), str(item.get("title") or "")))
    archive = list(payload.get("archive") or [])
    cards = "\n".join(card_markup(item) for item in opportunities)
    archived = "\n".join(archive_markup(item) for item in archive)
    town_options = "".join(f'<option value="{esc(slug(town))}">{esc(town)}</option>' for town in TOWNS)

    sources: dict[str, str] = {}
    for item in opportunities:
        meta = presentation(item)
        sources[slug(str(item.get("source_id") or meta["source_label"]))] = meta["source_label"]
    source_options = "".join(
        f'<option value="{esc(key)}">{esc(label)}</option>' for key, label in sorted(sources.items(), key=lambda pair: pair[1])
    )
    reference = fmt_date(payload.get("referenceDate"))
    source_count = len(sources)

    archive_section = (
        f"""<details class="op-archive"><summary><span>Archivio bandi chiusi</span><strong>{len(archive)}</strong></summary><ul>{archived}</ul></details>"""
        if archive
        else """<div class="op-archive-empty"><strong>Archivio bandi chiusi</strong><span>Nessun bando archiviato nello stato disponibile per questa anteprima.</span></div>"""
    )

    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Anteprima Radar Opportunità · Osservatorio Versilia</title>
  <meta name="description" content="Anteprima non pubblica del Radar Opportunità Versilia v0.2.4.">
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
      <span class="overline">Radar opportunità · Anteprima v0.2.4</span>
      <h1>Opportunità per i Comuni della Versilia.</h1>
      <p>Bandi e linee di finanziamento con un <strong>ruolo operativo documentato</strong> per almeno un Comune della Versilia. Le incertezze del motore restano nella revisione interna e non vengono mostrate qui.</p>
      <div class="op-preview-banner"><strong>Anteprima tecnica, non pubblicata.</strong> La route è fuori dalla sitemap e dalla navigazione pubblica.</div>
      <div class="op-preview-meta"><div><span>Dati verificati al</span><strong>{esc(reference)}</strong></div><div><span>Versione</span><strong>Radar / UI v0.2.4</strong></div></div>
    </section>

    <section class="method-detail page-width" aria-label="Riepilogo opportunità">
      <div class="section-heading"><div><span class="section-number">01</span><h2>Quadro operativo</h2></div><p>Il conteggio riguarda le fonti attualmente integrate nel prototipo.</p></div>
      <ol class="principles-grid op-preview-summary">
        <li><span>01</span><h3>Opportunità aperte</h3><strong>{len(opportunities)}</strong></li>
        <li><span>02</span><h3>Fonti attive</h3><strong>{source_count}</strong></li>
        <li><span>03</span><h3>Comuni coperti</h3><strong>{len(TOWNS)}</strong></li>
        <li><span>04</span><h3>In archivio</h3><strong>{len(archive)}</strong></li>
      </ol>
    </section>

    <section class="method-detail page-width">
      <div class="section-heading"><div><span class="section-number">02</span><h2>Filtra le opportunità</h2></div><p>Filtra per Comune, fonte o modalità di partecipazione. I requisiti specifici sono esplicitati nelle singole schede.</p></div>
      <div class="op-preview-controls">
        <label>Comune<select data-op-town><option value="">Tutta la Versilia</option>{town_options}</select></label>
        <label>Fonte<select data-op-source><option value="">Tutte le fonti</option>{source_options}</select></label>
        <label>Modalità<select data-op-access><option value="">Tutte le modalità</option><option value="direct">Candidatura diretta</option><option value="specific_requirement">Con requisito specifico</option></select></label>
        <label class="op-search-field">Cerca<input type="search" data-op-search placeholder="Titolo, fonte, ambito…" autocomplete="off"></label>
        <button class="op-preview-reset" type="button" data-op-reset>Reimposta</button>
      </div>
      <div class="op-preview-resultbar" aria-live="polite"><strong data-op-visible>{len(opportunities)} opportunità visibili</strong></div>
    </section>

    <section class="method-detail page-width" aria-label="Elenco opportunità">
      <div class="section-heading"><div><span class="section-number">03</span><h2>Opportunità aperte</h2></div><p>Le schede sono ordinate per scadenza. Colore e segno grafico aiutano a distinguere ambito e provenienza.</p></div>
      <div class="op-preview-list">{cards}</div>
      <div class="op-preview-empty" data-op-empty hidden>Nessuna opportunità corrisponde ai filtri selezionati.</div>
    </section>

    <section class="method-detail page-width" aria-label="Archivio bandi">
      <div class="section-heading"><div><span class="section-number">04</span><h2>Archivio</h2></div><p>I bandi non più aperti restano consultabili in forma compatta, con il collegamento alla fonte ufficiale.</p></div>
      {archive_section}
    </section>
  </main></div>
  <div id="site-footer-mount"></div>
  <noscript><div class="app-error">I filtri della preview richiedono JavaScript; le schede restano comunque leggibili.</div></noscript>
  <script src="../assets/opportunity-preview.js" defer></script>
</body>
</html>
"""


def build(payload_path: Path, dist: Path) -> Path:
    if not (dist / "progetto" / "index.html").exists():
        raise SystemExit("Build statica canonica assente: eseguire prima scripts/build_static_brand.py")
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
    forbidden_ui = ("Quality gate", "Perché compare:", ">Da verificare<")
    if any(token in text for token in forbidden_ui):
        raise SystemExit("La preview espone ancora concetti tecnici interni.")
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = build(args.data, args.dist)
    print(f"Preview opportunità v0.2.4 materializzata: {target}")


if __name__ == "__main__":
    main()
