"""Rilettura quotidiana delle pagine ufficiali di ogni scheda pubblica del Radar.

Le schede che arrivano da corpora statici (matrice comunale, corpus audit) e da
evidenze versionate hanno date scritte a mano: senza una rilettura restano
ferme anche quando la fonte proroga, apre o fissa una scadenza. Questo modulo,
eseguito a ogni refresh live prima dell'archiviazione delle scadute:

1. legge la pagina ufficiale della scheda (più eventuali ``official_urls``);
2. estrae dal testo le date con il loro ruolo, deciso dalla parola chiave più
   vicina che le precede (proroga, scadenza, apertura) o da un intervallo
   esplicito «dal … al …» / «from … to …»;
3. applica una regola unica, uguale per tutte le schede:
   - una proroga successiva alla scadenza corrente la sostituisce;
   - una scadenza corrente ritrovata nella pagina è confermata;
   - se la scadenza non è nella pagina e la pagina ne indica una sola futura,
     vale quella della pagina; con più candidate la scheda resta invariata e
     segnalata come non confermata;
   - una data di apertura passata con scadenza futura rende la scheda aperta,
     una data futura la rende «in arrivo»;
4. rende ``verified_at`` onesto: è la data dell'ultima lettura riuscita della
   fonte ufficiale. Se oggi la pagina non risponde restano i fatti e la data
   dell'ultima lettura riuscita (dallo snapshot precedente), mai la data odierna.

Nessuna correzione per singolo bando: la regola è la stessa per ogni scheda.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlsplit
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any, Callable, Iterable

SCHEMA_VERSION = "official-recheck-v1"
STATIC_SOURCES = {"municipal-matrix-v1", "audit-corpus-v1"}
STALE_AFTER_DAYS = 7
MAX_EXTENSION_DAYS = 550
HTTP_WORKERS = 10
BROWSER_BUDGET_SECONDS = 240

_IT_MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
    "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}
_EN_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
_MONTHS = {**_IT_MONTHS, **_EN_MONTHS}
_MONTH_RE = "|".join(sorted(_MONTHS, key=len, reverse=True))

_DATE_PATTERNS = (
    # 10 dicembre 2026 · 1° gennaio 2027 · 21 December 2026
    re.compile(rf"\b(?P<d>\d{{1,2}})(?:°|º|st|nd|rd|th)?\s+(?P<m>{_MONTH_RE})\s+(?P<y>20\d\d)\b", re.I),
    # December 21, 2026
    re.compile(rf"\b(?P<m>{_MONTH_RE})\s+(?P<d>\d{{1,2}})(?:st|nd|rd|th)?,?\s+(?P<y>20\d\d)\b", re.I),
    # 10/12/2026 · 10.12.2026 · 10-12-2026
    re.compile(r"\b(?P<d>\d{1,2})[./-](?P<mn>\d{1,2})[./-](?P<y>20\d\d)\b"),
    # 2026-12-10
    re.compile(r"\b(?P<y>20\d\d)-(?P<mn>\d{2})-(?P<d>\d{2})\b"),
)
_DAY_MONTH = re.compile(rf"\b(?P<d>\d{{1,2}})(?:°|º|st|nd|rd|th)?\s+(?P<m>{_MONTH_RE})\b", re.I)
_TIME_AFTER = re.compile(
    r"^[\s,]*(?:\(|-|–)?\s*(?:ore|h\.?|alle(?:\s+ore)?|at|entro\s+le(?:\s+ore)?|by)?\s*"
    r"(?P<h>[01]?\d|2[0-3])[:.](?P<mi>[0-5]\d)\b",
    re.I,
)
# Parola chiave più vicina prima della data: decide il ruolo della data.
_ROLE_KEYWORDS = (
    ("extension", re.compile(r"prorogat\w*|prorogh\w*|proroga|posticipat\w*|differit\w*|"
                             r"extended|extension|postponed", re.I)),
    ("deadline", re.compile(r"scadenz\w*|scade\b|scadr\w*|entro\b|termine\b|deadline|"
                            r"\bclos(?:e|es|ing)\b|until\b|\bby\b|fino\s+al|chiusur\w*|"
                            r"\bdue\b|non\s+oltre", re.I)),
    ("opening", re.compile(r"apertur\w*|\bapre\b|aprir\w*|si\s+apr\w*|a\s+partire\s+dal|"
                           r"\bopens?\b|opening|\bfrom\b|starting|launch\w*|\bdal\b", re.I)),
)
_RANGE = re.compile(
    r"(?:\bdal\b|\bfrom\b|\bbetween\b)\s*(?P<a>[^\n]{6,40}?)\s*"
    r"(?:\bal\b|\bto\b|\buntil\b|\band\b|–|—|-)\s*(?P<b>[^\n]{6,40})",
    re.I,
)
_BREAK = re.compile(r"[\n•|]|(?<=[a-zà-ù\)])\.\s")
_PREFIX_CHARS = 70
_CONTEXT_CHARS = 260
_ERROR_PAGE = re.compile(r"\b(404|pagina non trovata|page not found|not found|access denied|"
                         r"forbidden|errore\s+del\s+server)\b", re.I)
_STOP = {
    "della", "delle", "dello", "degli", "dell", "nella", "nelle", "comuni", "comune", "bando", "avviso",
    "call", "programma", "progetti", "progetto", "ministero", "regione", "toscana", "european",
    "europe", "with", "from", "this", "that", "and", "for", "the", "per", "con", "dei", "del",
}


def _to_date(day: str, month: int, year: str) -> date | None:
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def _iter_dates(text: str) -> Iterable[tuple[int, int, date]]:
    seen: set[int] = set()
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            if match.start() in seen:
                continue
            groups = match.groupdict()
            month = groups.get("mn")
            month_value = int(month) if month else _MONTHS.get(str(groups.get("m") or "").casefold())
            if not month_value:
                continue
            value = _to_date(groups["d"], month_value, groups["y"])
            if value is None:
                continue
            seen.add(match.start())
            yield match.start(), match.end(), value


def _role(prefix: str) -> str | None:
    tail = _BREAK.split(prefix)[-1]
    best: tuple[int, str] | None = None
    for role, pattern in _ROLE_KEYWORDS:
        for match in pattern.finditer(tail):
            if best is None or match.end() > best[0]:
                best = (match.end(), role)
    return best[1] if best else None


def _time_after(text: str, end: int) -> str | None:
    match = _TIME_AFTER.match(text[end:end + 32])
    if not match:
        return None
    return f"{int(match.group('h')):02d}:{match.group('mi')}"


def extract_facts(text: str) -> dict[str, Any]:
    """Date con ruolo trovate nel testo visibile di una pagina ufficiale."""
    text = re.sub(r"[ \t\r\f\v]+", " ", text or "")
    found: list[dict[str, Any]] = []
    positions: dict[int, dict[str, Any]] = {}
    previous_end = 0
    for start, end, value in sorted(_iter_dates(text)):
        # Il contesto non scavalca la data precedente: una parola chiave riferita
        # a un'altra data (es. elenchi di notizie datate) non si trasferisce.
        role = _role(text[max(previous_end, start - _PREFIX_CHARS):start])
        previous_end = end
        row = {"date": value, "role": role, "time": _time_after(text, end), "at": start,
               "context": text[max(0, start - _CONTEXT_CHARS):start].casefold()}
        found.append(row)
        positions[start] = row
    # Intervalli espliciti: la prima data apre, la seconda chiude.
    for match in _RANGE.finditer(text):
        b = next(iter(_iter_dates(match.group("b"))), None)
        if not b:
            continue
        second = positions.get(match.start("b") + b[0])
        if not second:
            continue
        a = next(iter(_iter_dates(match.group("a"))), None)
        if a:
            first = positions.get(match.start("a") + a[0])
        else:
            # «dal 26 ottobre al 21 dicembre 2026»: l'anno della prima data è implicito.
            partial = _DAY_MONTH.search(match.group("a"))
            first = None
            if partial and partial.start() < 4:
                month = _MONTHS[partial.group("m").casefold()]
                value = _to_date(partial.group("d"), month, str(b[2].year))
                if value and value > b[2]:
                    value = _to_date(partial.group("d"), month, str(b[2].year - 1))
                if value:
                    first = {"date": value, "role": "opening", "time": None,
                             "at": match.start("a") + partial.start(), "context": ""}
                    found.append(first)
        if not first or not first["date"] < second["date"]:
            continue
        first["role"] = "opening"
        if second["role"] != "extension":
            second["role"] = "deadline"
    return {"dates": found}


def item_tokens(item: dict[str, Any]) -> list[str]:
    return [t for t in re.findall(r"[\wà-ù]{3,}", str(item.get("title") or "").casefold())
            if t not in _STOP and not t.isdigit()]


def section_root(url: str) -> str | None:
    """Pagina di sezione del sito ufficiale (host + primo segmento), dove le fonti
    pubblicano proroghe e avvisi che la pagina originale del bando non riporta."""
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None
    segments = [x for x in parts.path.split("/") if x]
    if parts.path.casefold().endswith(".pdf") and len(segments) <= 1:
        return f"{parts.scheme}://{parts.netloc}/"
    root = f"{parts.scheme}://{parts.netloc}/" + (f"{segments[0]}/" if len(segments) > 1 else "")
    return None if root.rstrip("/") == url.rstrip("/") else root


def page_matches_item(text: str, item: dict[str, Any]) -> bool:
    """La pagina letta è davvero quella della scheda, non un errore o un portale vuoto."""
    if len(text.strip()) < 200:
        return False
    head = text[:600]
    if _ERROR_PAGE.search(head) and len(text) < 3000:
        return False
    folded = text.casefold()
    tokens = item_tokens(item)
    if not tokens:
        return True
    return any(t in folded for t in tokens)


def _iso(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def decide(item: dict[str, Any], facts: dict[str, Any], today: date) -> dict[str, Any]:
    """Applica la regola unica e restituisce i campi da aggiornare e il perché."""
    rows = facts.get("dates") or []
    current = _iso(item.get("deadline_at"))
    opens_current = _iso(item.get("opens_at"))
    horizon = today.toordinal() + MAX_EXTENSION_DAYS
    update: dict[str, Any] = {}
    reasons: list[str] = []
    outcome = "confirmed"

    def in_horizon(value: date) -> bool:
        return value.toordinal() <= horizon

    extensions = [r for r in rows if r["role"] == "extension" and in_horizon(r["date"])
                  and r["date"] >= today and (current is None or r["date"] > current)]
    deadlines = [r for r in rows if r["role"] == "deadline" and in_horizon(r["date"])]
    future_deadlines = sorted({r["date"] for r in deadlines if r["date"] >= today})
    page_dates = {r["date"] for r in rows}

    deadline = current
    deadline_row = None
    if extensions:
        deadline_row = max(extensions, key=lambda r: (r["date"], r["time"] or ""))
        deadline = deadline_row["date"]
        reasons.append(f"proroga indicata dalla fonte al {deadline.isoformat()}")
    elif current is not None and current in page_dates:
        deadline_row = next((r for r in rows if r["date"] == current and r["time"]), None)
    elif current is not None and current < today:
        # Una scheda già scaduta torna aperta solo con una proroga esplicita:
        # altre date future della pagina (nuovi cicli, validità) non bastano.
        pass
    elif len(future_deadlines) == 1:
        deadline = future_deadlines[0]
        deadline_row = next(r for r in deadlines if r["date"] == deadline)
        reasons.append(f"scadenza indicata dalla fonte: {deadline.isoformat()}")
    elif current is not None or future_deadlines:
        outcome = "unconfirmed"
        reasons.append(
            "scadenza della scheda non ritrovata nella pagina"
            if current is not None else "più scadenze future nella pagina: scheda invariata"
        )

    if deadline != current and deadline is not None:
        update["deadline_at"] = deadline.isoformat()
        update["deadline_time"] = deadline_row["time"] if deadline_row else None
    elif deadline_row and deadline_row.get("time") and not item.get("deadline_time"):
        update["deadline_time"] = deadline_row["time"]

    openings = sorted({r["date"] for r in rows if r["role"] == "opening"
                       and (deadline is None or r["date"] <= deadline)
                       and r["date"].toordinal() >= today.toordinal() - 400})
    opens = opens_current
    if openings:
        future_openings = [d for d in openings if d > today]
        candidate = future_openings[0] if future_openings and (deadline is None or deadline > today) else openings[-1]
        if opens_current is None or (opens_current > today and candidate <= today) or candidate == opens_current:
            opens = candidate
    if opens != opens_current and opens is not None:
        update["opens_at"] = opens.isoformat()
        reasons.append(f"apertura indicata dalla fonte: {opens.isoformat()}")

    stage = str(item.get("lifecycle_stage") or "")
    effective_deadline = _iso(update.get("deadline_at")) or current
    if opens is not None and opens > today:
        new_stage = "announced_upcoming"
    elif effective_deadline is not None:
        new_stage = "application_open"
    elif stage == "announced_upcoming" and opens is not None and opens <= today:
        new_stage = "rolling_open"
    else:
        new_stage = stage or "rolling_open"
    if new_stage != stage:
        update["lifecycle_stage"] = new_stage
        update["status"] = "upcoming" if new_stage == "announced_upcoming" else "open"
        reasons.append(f"stato dalla fonte: {new_stage}")

    if update and outcome == "confirmed":
        outcome = "updated"
    return {"outcome": outcome, "update": update, "reasons": reasons}


def _identity(item: dict[str, Any]) -> str:
    return str(item.get("coverage_id") or item.get("rule_id") or item.get("id") or item.get("url") or "")


def _previous_index(previous: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in (previous or {}).get("opportunities") or []:
        index[_identity(row)] = row
    return index


def _registered_official_urls(coverage_id: str) -> tuple[str, ...]:
    """Pagine ufficiali equivalenti già registrate per la stessa scheda."""
    try:
        import opportunity_daily_refresh_revalidated as revalidated
    except Exception:  # pragma: no cover - dipendenze del motore assenti
        return ()
    return (tuple(revalidated._OFFICIAL_ALTERNATE_URLS.get(coverage_id, ()))
            + tuple(revalidated._OFFICIAL_EVIDENCE_SETS.get(coverage_id, ())))


def _urls(item: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    registered = _registered_official_urls(str(item.get("coverage_id") or ""))
    for url in [item.get("url"), *(item.get("official_urls") or []), *registered]:
        url = str(url or "").strip()
        if url.startswith(("http://", "https://")) and url not in urls:
            urls.append(url)
    return urls


def _section_urls(item: dict[str, Any]) -> list[str]:
    own = set(_urls(item))
    roots = []
    for url in own:
        root = section_root(url)
        if root and root not in own and root not in roots:
            roots.append(root)
    return roots


def _section_extensions(item: dict[str, Any], texts: dict[str, str]) -> list[dict[str, Any]]:
    """Solo proroghe dalla pagina di sezione, e solo se il contesto nomina la scheda."""
    tokens = [t for t in item_tokens(item) if len(t) >= 3]
    rows = []
    for url in _section_urls(item):
        if url not in texts:
            continue
        for row in extract_facts(texts[url])["dates"]:
            if row["role"] == "extension" and any(re.search(rf"\b{re.escape(t)}\b", row["context"]) for t in tokens):
                rows.append(row)
    return rows


def default_fetchers() -> tuple[Callable[[str], str], Callable[[str], str]]:
    """Trasporti già usati dal Radar: HTTP con intestazioni browser/PDF, poi Chromium."""
    import opportunity_daily_refresh_revalidated as revalidated
    import opportunity_pdf_evidence as pdf_evidence
    import opportunity_radar as radar_base

    def http(url: str) -> str:
        if revalidated._is_pdf_url(url):
            return pdf_evidence.fetch_pdf_text(url, max_pages=24, max_chars=120000)
        return radar_base.visible(revalidated._fetch_browser_html(url, timeout=15, attempts=2))

    def browser(url: str) -> str:
        return revalidated._fetch_playwright_text(url, timeout_ms=30_000)

    return http, browser


def read_pages(items: list[dict[str, Any]], http: Callable[[str], str],
               browser: Callable[[str], str] | None) -> dict[str, dict[str, str]]:
    """Legge in parallelo tutte le pagine ufficiali; Chromium solo per chi fallisce."""
    urls = sorted({url for item in items for url in [*_urls(item), *_section_urls(item)]})
    texts: dict[str, str] = {}
    errors: dict[str, str] = {}

    def one(url: str) -> tuple[str, str | None, str | None]:
        try:
            return url, http(url), None
        except Exception as exc:  # pragma: no cover - rete live
            return url, None, f"{type(exc).__name__}: {exc}"

    with ThreadPoolExecutor(max_workers=HTTP_WORKERS) as pool:
        for url, text, error in pool.map(one, urls):
            if text:
                texts[url] = text
            else:
                errors[url] = error or "vuota"
    if browser is not None:
        started = time.monotonic()
        for url in sorted(errors):
            if url.casefold().split("?", 1)[0].endswith(".pdf"):
                continue
            if time.monotonic() - started > BROWSER_BUDGET_SECONDS:
                break
            try:
                text = browser(url)
            except Exception as exc:  # pragma: no cover - rete live
                errors[url] = f"{errors[url]}; Chromium: {type(exc).__name__}: {exc}"
                continue
            if text:
                texts[url] = text
                errors.pop(url, None)
    return {"texts": texts, "errors": errors}


def apply(items: list[dict[str, Any]], today: date, *, previous: dict[str, Any] | None = None,
          pages: dict[str, dict[str, str]] | None = None,
          http: Callable[[str], str] | None = None,
          browser: Callable[[str], str] | None = None) -> dict[str, Any]:
    """Rilegge ogni scheda dalla fonte ufficiale e la aggiorna in place."""
    if pages is None:
        if http is None:
            http, browser = default_fetchers()
        pages = read_pages(items, http, browser)
    texts = pages.get("texts") or {}
    errors = pages.get("errors") or {}
    prior = _previous_index(previous)
    summary = {"schemaVersion": SCHEMA_VERSION, "checked": 0, "confirmed": 0, "updated": 0,
               "unconfirmed": 0, "unreachable": 0, "stale": 0, "changes": [], "unreachableItems": []}

    for item in items:
        summary["checked"] += 1
        before = {k: item.get(k) for k in ("deadline_at", "deadline_time", "opens_at", "lifecycle_stage", "status")}
        old = prior.get(_identity(item)) or {}
        old_check = old.get("official_recheck") or {}
        read = [(url, texts[url]) for url in _urls(item) if url in texts and page_matches_item(texts[url], item)]
        static = str(item.get("source_id") or "") in STATIC_SOURCES or bool(item.get("audit_promotion_version"))

        if read:
            facts = {"dates": [row for _, text in read for row in extract_facts(text)["dates"]]
                     + _section_extensions(item, texts)}
            decision = decide(item, facts, today)
            item.update(decision["update"])
            item["verified_at"] = today.isoformat()
            check = {
                "schemaVersion": SCHEMA_VERSION,
                "checked_at": today.isoformat(),
                "last_ok_at": today.isoformat(),
                "outcome": decision["outcome"],
                "urls": [url for url, _ in read],
                "reasons": decision["reasons"],
                "facts": {k: item.get(k) for k in ("deadline_at", "deadline_time", "opens_at", "lifecycle_stage", "status")},
            }
        else:
            # Pagina non raggiungibile oggi: restano i fatti dell'ultima lettura riuscita.
            last_ok = old_check.get("last_ok_at")
            facts = old_check.get("facts") or {}
            if last_ok and facts:
                for key, value in facts.items():
                    item[key] = value
            if static or last_ok:
                item["verified_at"] = last_ok
            check = {
                "schemaVersion": SCHEMA_VERSION,
                "checked_at": today.isoformat(),
                "last_ok_at": last_ok,
                "outcome": "unreachable",
                "urls": _urls(item),
                "reasons": [errors.get(url) or "pagina senza riferimenti alla scheda" for url in _urls(item)][:3],
                "facts": facts,
            }
            summary["unreachableItems"].append({"title": item.get("title"), "url": item.get("url"), "last_ok_at": last_ok})
        item["official_recheck"] = check
        summary[check["outcome"]] += 1
        last_ok_date = _iso(check.get("last_ok_at"))
        if last_ok_date is None or (today - last_ok_date).days > STALE_AFTER_DAYS:
            if check["outcome"] == "unreachable":
                summary["stale"] += 1
        after = {k: item.get(k) for k in before}
        if after != before:
            summary["changes"].append({
                "title": item.get("title"),
                "url": item.get("url"),
                "before": before,
                "after": after,
                "reasons": check["reasons"],
            })
    return summary
