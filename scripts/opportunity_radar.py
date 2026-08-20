#!/usr/bin/env python3
"""Prototipo del Radar Opportunità Versilia.

Il modulo raccoglie opportunità da poche fonti ufficiali, le normalizza e applica
un filtro prudenziale per i sette Comuni della Versilia. Non pubblica dati sul sito.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "data" / "opportunity-sources.json"
DEFAULT_TIMEOUT = 25
USER_AGENT = "OsservatorioVersilia-OpportunityRadar/0.1 (+https://osservatorioversilia.it/)"

MONTHS_IT = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}

DIRECT_BENEFICIARY_PATTERNS = (
    r"\benti locali\b",
    r"\bcomuni\b",
    r"\bamministrazioni pubbliche locali\b",
    r"\bunioni dei comuni\b",
)
CONDITIONAL_BENEFICIARY_PATTERNS = (
    r"\benti pubblici\b",
    r"\bsoggetti pubblici\b",
    r"\bamministrazioni pubbliche\b",
    r"\bpartnership\b.*\bsoggetti pubblici\b",
)
EXCLUSION_PATTERNS = (
    r"\bliber[ei] professionist",
    r"\bimprese\b",
    r"\bscuole\b",
    r"\buniversit",
    r"\bstudent",
    r"\baziende\b",
)

THEME_RULES = {
    "ambiente": ("ambiente", "amianto", "rifiuti", "energia", "clima", "bonifica"),
    "opere-pubbliche": ("opere pubbliche", "edifici pubblici", "infrastrutture", "sism"),
    "digitale": ("digitale", "cloud", "pagopa", "app io", "pdnd", "notifiche"),
    "sociale": ("sociale", "welfare", "giovani", "comunità", "comunita"),
    "cultura": ("cultura", "culturale", "patrimonio", "restauro"),
}


@dataclass
class Opportunity:
    id: str
    source_id: str
    source_name: str
    publisher: str
    title: str
    url: str
    summary: str = ""
    status: str = "open"
    opens_at: str | None = None
    deadline_at: str | None = None
    published_at: str | None = None
    beneficiary_text: str = ""
    municipalities: list[str] = field(default_factory=list)
    eligibility: str = "review"
    eligibility_reason: str = "Destinatari non determinabili automaticamente."
    themes: list[str] = field(default_factory=list)
    funding_total_eur: float | None = None
    max_contribution_eur: float | None = None
    cofunding_text: str | None = None
    priority: str = "medium"
    detected_at: str = ""
    fingerprint: str = ""


@dataclass
class Card:
    heading: str
    href: str | None
    body: str


class HeadingCardParser(HTMLParser):
    """Estrae blocchi introdotti da h2/h3/h4 senza dipendere da classi CSS."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[Card] = []
        self._in_heading = False
        self._heading_parts: list[str] = []
        self._heading_href: str | None = None
        self._body_parts: list[str] = []
        self._current_heading: str | None = None
        self._current_href: str | None = None

    def _flush(self) -> None:
        if self._current_heading:
            body = clean_text(" ".join(self._body_parts))
            self.cards.append(Card(self._current_heading, self._current_href, body))
        self._body_parts = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"h2", "h3", "h4"}:
            self._flush()
            self._in_heading = True
            self._heading_parts = []
            self._heading_href = None
        if self._in_heading and tag == "a":
            self._heading_href = dict(attrs).get("href")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"h2", "h3", "h4"} and self._in_heading:
            self._current_heading = clean_text(" ".join(self._heading_parts))
            self._current_href = self._heading_href
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading_parts.append(data)
        elif self._current_heading:
            self._body_parts.append(data)

    def close(self) -> None:
        super().close()
        self._flush()


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def normalize_for_match(value: str) -> str:
    value = clean_text(value).casefold()
    return value.replace("’", "'")


def stable_id(source_id: str, title: str, url: str) -> str:
    digest = hashlib.sha256(f"{source_id}|{title.casefold()}|{url}".encode("utf-8")).hexdigest()[:14]
    return f"opp-{digest}"


def fingerprint_payload(parts: Iterable[Any]) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_date_token(value: str) -> date | None:
    value = clean_text(value).strip(" .,")
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    match = re.fullmatch(r"(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})", value)
    if not match:
        return None
    day, month_name, year = match.groups()
    month = MONTHS_IT.get(month_name.casefold())
    if month is None:
        return None
    try:
        return date(int(year), month, int(day))
    except ValueError:
        return None


def extract_dates(text: str) -> tuple[str | None, str | None, str | None]:
    compact = clean_text(text)
    published = None
    deadline = None
    opens = None

    pub_match = re.search(r"Pubblicato il\s+(\d{1,2}[./]\d{1,2}[./]\d{4})", compact, re.I)
    if pub_match:
        parsed = parse_date_token(pub_match.group(1).replace("/", "."))
        published = parsed.isoformat() if parsed else None

    deadline_match = re.search(
        r"Scadenza(?:\s+presentazione\s+domande)?\s+(\d{1,2}[./]\d{1,2}[./]\d{4})",
        compact,
        re.I,
    )
    if deadline_match:
        parsed = parse_date_token(deadline_match.group(1).replace("/", "."))
        deadline = parsed.isoformat() if parsed else None

    range_match = re.search(
        r"\bdal\s+(\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+al\s+(\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})",
        compact,
        re.I,
    )
    if range_match:
        start = parse_date_token(range_match.group(1))
        end = parse_date_token(range_match.group(2))
        opens = start.isoformat() if start else opens
        deadline = end.isoformat() if end else deadline

    return opens, deadline, published


def extract_money(text: str) -> tuple[float | None, float | None]:
    compact = clean_text(text)
    total = None
    maximum = None
    total_match = re.search(r"(?:risorse|dotazione|budget)[^€\d]{0,40}(?:€\s*)?([\d.]+(?:,\d+)?)\s*(milion[ei])?", compact, re.I)
    max_match = re.search(r"(?:importo massimo|max(?:imum)?)[^€\d]{0,40}(?:€\s*)?([\d.]+(?:,\d+)?)", compact, re.I)

    def amount(match: re.Match[str] | None) -> float | None:
        if not match:
            return None
        value = float(match.group(1).replace(".", "").replace(",", "."))
        if match.lastindex and match.lastindex >= 2 and match.group(2):
            value *= 1_000_000
        return value

    total = amount(total_match)
    if max_match:
        maximum = float(max_match.group(1).replace(".", "").replace(",", "."))
    return total, maximum


def classify_themes(text: str) -> list[str]:
    haystack = normalize_for_match(text)
    return [theme for theme, terms in THEME_RULES.items() if any(term in haystack for term in terms)]


def classify_eligibility(text: str, municipalities: list[str]) -> tuple[str, list[str], str]:
    haystack = normalize_for_match(text)
    direct = any(re.search(pattern, haystack, re.I) for pattern in DIRECT_BENEFICIARY_PATTERNS)
    conditional = any(re.search(pattern, haystack, re.I) for pattern in CONDITIONAL_BENEFICIARY_PATTERNS)
    excluded = any(re.search(pattern, haystack, re.I) for pattern in EXCLUSION_PATTERNS)

    if direct:
        return "eligible", municipalities[:], "Il testo della fonte indica esplicitamente Comuni o enti locali tra i destinatari."
    if conditional:
        return "conditional", municipalities[:], "La fonte ammette soggetti pubblici, ma sono presenti condizioni da verificare sul bando completo."
    if excluded:
        return "not_relevant", [], "I destinatari espliciti non sono amministrazioni comunali."
    return "review", [], "Il testo disponibile non consente di confermare i destinatari comunali."


def provisional_priority(eligibility: str, deadline: str | None, themes: list[str], today: date) -> str:
    if eligibility == "not_relevant":
        return "low"
    days = None
    if deadline:
        try:
            days = (date.fromisoformat(deadline) - today).days
        except ValueError:
            pass
    if eligibility == "eligible" and (days is None or days >= 10) and themes:
        return "high"
    if eligibility in {"eligible", "conditional"}:
        return "medium"
    return "low"


def fetch_text(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def collect_html_cards(source: dict[str, Any], municipalities: list[str], today: date, payload: str) -> list[Opportunity]:
    parser = HeadingCardParser()
    parser.feed(payload)
    parser.close()
    results: list[Opportunity] = []
    for card in parser.cards:
        title = clean_text(card.heading)
        body = clean_text(card.body)
        if len(title) < 8 or title.casefold() in {"filtra la ricerca", "cerca nel sito", "bandi in corso e in arrivo"}:
            continue
        full_text = f"{title}. {body}"
        eligibility, towns, reason = classify_eligibility(full_text, municipalities)
        if eligibility == "not_relevant":
            continue
        opens, deadline, published = extract_dates(full_text)
        if deadline and date.fromisoformat(deadline) < today:
            continue
        url = urljoin(source["url"], card.href) if card.href else source["url"]
        themes = classify_themes(full_text)
        total, maximum = extract_money(full_text)
        detected = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        results.append(
            Opportunity(
                id=stable_id(source["id"], title, url),
                source_id=source["id"],
                source_name=source["name"],
                publisher=source["publisher"],
                title=title,
                url=url,
                summary=body[:700],
                opens_at=opens,
                deadline_at=deadline,
                published_at=published,
                beneficiary_text=body[:900],
                municipalities=towns,
                eligibility=eligibility,
                eligibility_reason=reason,
                themes=themes,
                funding_total_eur=total,
                max_contribution_eur=maximum,
                priority=provisional_priority(eligibility, deadline, themes, today),
                detected_at=detected,
                fingerprint=fingerprint_payload((source["id"], title, body, deadline, eligibility)),
            )
        )
    return results


def collect_padigitale(source: dict[str, Any], municipalities: list[str], today: date, payload: str) -> list[Opportunity]:
    raw = json.loads(payload)
    if not isinstance(raw, list):
        raise ValueError("Il dataset PA digitale non è una lista JSON.")
    results: list[Opportunity] = []
    detected = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for item in raw:
        if not isinstance(item, dict):
            continue
        recipients = clean_text(str(item.get("soggetti_destinatari") or ""))
        if "comuni" not in recipients.casefold():
            continue
        status_raw = clean_text(str(item.get("stato") or ""))
        end = clean_text(str(item.get("data_fine_bando") or "")) or None
        if status_raw.casefold() in {"terminato", "chiuso"}:
            continue
        if end:
            try:
                if date.fromisoformat(end) < today:
                    continue
            except ValueError:
                pass
        title = clean_text(str(item.get("titolo") or ""))
        if not title:
            continue
        measure = clean_text(str(item.get("misura") or ""))
        total = item.get("totale_importo_stanziato")
        total_float = float(total) if isinstance(total, (int, float)) else None
        url = "https://www.padigitale2026.gov.it/enti/comuni"
        full_text = f"{title}. {measure}. Destinatari: {recipients}"
        themes = classify_themes(full_text)
        results.append(
            Opportunity(
                id=stable_id(source["id"], title, url),
                source_id=source["id"],
                source_name=source["name"],
                publisher=source["publisher"],
                title=title,
                url=url,
                summary=measure,
                status="open",
                opens_at=clean_text(str(item.get("data_inizio_bando") or "")) or None,
                deadline_at=end,
                beneficiary_text=recipients,
                municipalities=municipalities[:],
                eligibility="eligible",
                eligibility_reason="Il dataset ufficiale PA digitale 2026 indica i Comuni tra i soggetti destinatari.",
                themes=themes or ["digitale"],
                funding_total_eur=total_float,
                priority=provisional_priority("eligible", end, themes or ["digitale"], today),
                detected_at=detected,
                fingerprint=fingerprint_payload((source["id"], title, measure, end, total_float)),
            )
        )
    return results


def deduplicate(items: Iterable[Opportunity]) -> list[Opportunity]:
    chosen: dict[tuple[str, str], Opportunity] = {}
    for item in items:
        key = (item.source_id, normalize_for_match(item.title))
        existing = chosen.get(key)
        if existing is None or len(item.summary) > len(existing.summary):
            chosen[key] = item
    return sorted(chosen.values(), key=lambda item: (item.deadline_at or "9999-12-31", item.title.casefold()))


def run(config_path: Path, today: date, payloads: dict[str, str] | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    municipalities = list(config["municipalities"])
    payloads = payloads or {}
    collected: list[Opportunity] = []
    source_results: list[dict[str, Any]] = []

    for source in config["sources"]:
        try:
            payload = payloads.get(source["id"])
            if payload is None:
                payload = fetch_text(source["url"])
            if source["type"] == "html_cards":
                items = collect_html_cards(source, municipalities, today, payload)
            elif source["type"] == "padigitale_json":
                items = collect_padigitale(source, municipalities, today, payload)
            else:
                raise ValueError(f"Tipo di fonte non supportato: {source['type']}")
            collected.extend(items)
            source_results.append({"sourceId": source["id"], "status": "ok", "count": len(items), "error": None})
        except (ValueError, json.JSONDecodeError, urllib.error.URLError, TimeoutError) as exc:
            source_results.append({"sourceId": source["id"], "status": "error", "count": 0, "error": str(exc)})

    items = deduplicate(collected)
    counts = {
        "total": len(items),
        "eligible": sum(item.eligibility == "eligible" for item in items),
        "conditional": sum(item.eligibility == "conditional" for item in items),
        "review": sum(item.eligibility == "review" for item in items),
        "highPriority": sum(item.priority == "high" for item in items),
    }
    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "referenceDate": today.isoformat(),
        "municipalities": municipalities,
        "counts": counts,
        "sources": source_results,
        "opportunities": [asdict(item) for item in items],
    }


def render_markdown(result: dict[str, Any]) -> str:
    counts = result["counts"]
    lines = [
        "# Radar Opportunità Versilia — prototipo",
        "",
        f"Data di riferimento: **{result['referenceDate']}**",
        "",
        f"Opportunità trattenute: **{counts['total']}** · ammissibili: **{counts['eligible']}** · condizionate: **{counts['conditional']}** · da verificare: **{counts['review']}**.",
        "",
        "## Fonti",
        "",
    ]
    for source in result["sources"]:
        marker = "OK" if source["status"] == "ok" else "ERRORE"
        extra = f" — {source['error']}" if source["error"] else ""
        lines.append(f"- **{marker}** `{source['sourceId']}`: {source['count']} opportunità{extra}")
    lines.extend(["", "## Opportunità", ""])
    if not result["opportunities"]:
        lines.append("Nessuna opportunità è stata classificata come pertinente nel campione.")
    for item in result["opportunities"]:
        deadline = item["deadline_at"] or "non rilevata"
        lines.extend(
            [
                f"### {item['title']}",
                f"- Fonte: {item['source_name']}",
                f"- Ammissibilità: **{item['eligibility']}** — {item['eligibility_reason']}",
                f"- Priorità provvisoria: **{item['priority']}**",
                f"- Scadenza: **{deadline}**",
                f"- Temi: {', '.join(item['themes']) if item['themes'] else 'da classificare'}",
                f"- URL: {item['url']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--date", default=date.today().isoformat(), help="Data YYYY-MM-DD usata per scadenze e filtri.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    today = date.fromisoformat(args.date)
    result = run(args.config, today=today)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_markdown(result), encoding="utf-8")
    return 1 if any(source["status"] == "error" for source in result["sources"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
