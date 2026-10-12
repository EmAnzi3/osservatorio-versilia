#!/usr/bin/env python3
"""Derive an actionable owner inbox without changing publication decisions.

Every unique signal remains accounted for. Catalog/navigation sections, exact
published references and expired structured records are separated from requests
for human verification. No dates or eligibility are inferred from headlines.
"""
from __future__ import annotations

import html
import hashlib
import json
from pathlib import Path
import re
import time
from collections import Counter
from datetime import date
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

import opportunity_pdf_evidence as pdf
from opportunity_discovery_noise import GENERIC, classify_signal, unrelated_document

LABELS = {"human": "Verifica di persona", "retry": "Ritentativo automatico", "technical": "Intervento sul Radar",
          "covered": "Già rappresentata", "expired": "Termine concluso",
          "monitor": "Pagina di monitoraggio"}


def normalized_url(value):
    try:
        p = urlsplit(str(value or ""))
        if p.scheme not in ("http", "https") or not p.hostname or p.username:
            return ""
        query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                 if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), unquote(p.path).rstrip("/") or "/", urlencode(query), ""))
    except ValueError:
        return ""


def _diagnosis(check, item):
    errors = list(check.get("errors") or [])
    errors += [d["error"] for d in check.get("documents") or [] if d.get("error")]
    text = " ".join(errors).casefold()
    rules = [
        ("scansionato", "scanned_pdf", "Il PDF non contiene testo sufficiente per una lettura automatica.",
         "Leggere il PDF collegato e verificare beneficiari, territorio, requisiti e termini; occorre una trascrizione controllata."),
        ("territorial", "territory", "I requisiti territoriali non sono risolti.",
         "Verificare nel documento se almeno un Comune della Versilia o il suo progetto rientra nel territorio ammesso."),
        ("ammissibilità", "applicants", "Il ruolo o l’ammissibilità dell’ente locale non sono dimostrati.",
         "Controllare gli articoli sui beneficiari e distinguere candidatura comunale, partenariato e destinatari finali."),
        ("ruolo comunale", "applicants", "Il ruolo comunale e la destinazione dell’intervento non sono dimostrati.",
         "Controllare beneficiari e requisiti dell’intervento nel documento collegato."),
        ("finestra", "application_window", "La finestra di candidatura è assente o ambigua.",
         "Controllare apertura, scadenza e ora, distinguendole dai termini di esecuzione e dalle eventuali proroghe."),
        ("struttura", "unsupported_layout", "Il documento ha una struttura non ancora interpretabile automaticamente.",
         "Leggere gli articoli su beneficiari, requisiti e domanda e verificare se esistono allegati o rettifiche."),
        ("famiglia documentale", "unsupported_family", "Questa famiglia di avviso non ha ancora un lettore verificato.",
         "Verificare beneficiari, requisiti, territorio e finestra di candidatura nel documento collegato."),
        ("oltre il limite", "document_limit", "Il documento supera il limite di lettura integrale del Radar.",
         "Consultare integralmente il PDF e gli allegati: il Radar non ne ha usato una lettura parziale per pubblicare."),
        ("articoli ripetuti", "compound_document", "Il PDF contiene articoli ripetuti o documenti composti.",
         "Separare avviso, allegati e rettifiche e ricostruire quale testo e quali termini siano vigenti."),
    ]
    for probe, code, reason, action in rules:
        if probe in text:
            return ("human" if code == "scanned_pdf" else "technical"), code, reason, (action if code == "scanned_pdf" else "Responsabilità del Radar: " + action)
    if check.get("status") == "deferred" or any(x in text for x in ("timeout", "timed out", "budget", "urlopen", "http error", "acquisizione fallita")):
        return "retry", "transport_or_budget", "L’acquisizione non è conclusa o il budget del run è esaurito.", "Il Radar ritenterà nei run successivi. Se urgente, aprire i collegamenti disponibili e verificare il documento di persona."
    if "nessun pdf" in text:
        return "technical", "missing_document", "Nessun avviso PDF su una fonte documentale consentita è stato individuato.", "Responsabilità del Radar: individuare e acquisire il documento ufficiale che disciplina l’avviso; i collegamenti individuati sono riportati qui sotto."
    if errors:
        return "technical", "document_evidence", "La verifica del documento non è completa.", "Responsabilità del Radar: verificare autore, integrità del documento, requisiti e termini prima della pubblicazione."
    return "technical", "unverified_signal", "La segnalazione non ha ancora una verifica documentale sufficiente per pubblicare una scheda.", "Responsabilità del Radar: completare la verifica documentale di beneficiari, ruolo comunale, territorio, requisiti e termini. La disponibilità di un PDF leggibile non richiede un controllo del proprietario."


def publication_exclusion(item):
    """Exact reviewed calls excluded by the owner's territorial publication scope."""
    path = Path(__file__).resolve().parents[1] / "data/opportunity-audit-fixes-v1.json"
    for entry in json.loads(path.read_text(encoding="utf-8")).get("publicationExclusions", []):
        if (item.get("coverage_id") == entry["coverage_id"] or
                any(normalized_url(item.get(field)) == normalized_url(entry["url"])
                    for field in ("url", "discovery_url") if item.get(field))):
            return entry
    return None


def source_text_hash(page):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page, "html.parser")
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def reviewed_source(page, url):
    path = Path(__file__).resolve().parents[1] / "data/opportunity-audit-fixes-v1.json"
    assessments = json.loads(path.read_text(encoding="utf-8")).get("reviewAssessments", [])
    for entry in assessments:
        if normalized_url(entry["url"]) == normalized_url(url) and source_text_hash(page) == entry["sourceTextSha256"]:
            return entry
    return None


def is_administrative_update(page, url=""):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page, "html.parser")
    for el in soup(["script", "style", "nav", "header", "footer"]):
        el.decompose()
    text = soup.get_text(" ", strip=True)
    # An explicit application window takes precedence over an allocation report.
    if re.search(r"(?:presentare|inviare)\s+(?:le\s+)?(?:domande|candidature)|riapert[ui]|riapertura|nuova\s+finestra|apert[uo]\s+(?:il\s+)?bando", text, re.I):
        return False
    if re.search(r"(?:approvata\s+la\s+graduatoria\s+definitiva|approvate\s+le\s+graduatorie\s+definitive)", text, re.I):
        return True
    # Prefecture headlines report named municipalities' existing projects.
    # Do not extrapolate this rule to other publishers or generic funding news.
    if urlsplit(url).hostname != "prefettura.interno.gov.it":
        return False
    heading = soup.find("h1")
    headline = heading.get_text(" ", strip=True) if heading else text
    return bool(re.search(r"videosorveglianza", headline, re.I) and re.search(
        r"approvat[io]\b.*progetti|approvazione\s+(?:graduatoria|progetti)|assegnazione\s+fondi|comuni\s+\w*\s*candidano\s+progetti", headline, re.I))


def build_actions(payload):
    lookups = {normalized_url(x.get("url")): x for x in payload.get("reviewDocumentLookup") or []}
    checks = {}
    for check in (payload.get("documentPromotion") or {}).get("checks") or []:
        checks.setdefault(normalized_url(check.get("url")), []).append(check)
    represented = {}
    for item in payload.get("opportunities") or []:
        for field in ("url", "discovery_url"):
            key = normalized_url(item.get(field))
            if key:
                represented[key] = item.get("title", "Scheda pubblicata")
    groups = {}
    signals = [*(payload.get("discoveryQueue") or []), *(payload.get("reviewQueue") or []),
               *(payload.get("qualityHold") or []), *(payload.get("discoveryNoise") or [])]
    if payload.get("publicationBlocked"):
        represented_ids = {x.get("coverage_id") for x in payload.get("opportunities") or []}
        for check_rows in checks.values():
            for check in check_rows:
                identity = check.get("coverage_id")
                if check.get("status") != "published_candidate" or not identity or identity in represented_ids:
                    continue
                represented_ids.add(identity)
                signals.append({"url": check.get("url"), "title": check.get("title"), "source_label": "MIM · Avviso documentale verificato",
                                "deadline_at": next((d.get("deadline") for d in check.get("documents") or [] if d.get("status") == "verified"), ""),
                                "_verifiedPublicationPending": True})
    for item in signals:
        key = normalized_url(item.get("url")) or str(item.get("id") or item.get("title") or "Senza riferimento")
        groups.setdefault(key, []).append(item)
    rows = []
    for key, items in groups.items():
        # Prefer a specific headline over navigation fragments at the same URL.
        item = max(items, key=lambda x: (not bool(GENERIC.fullmatch(str(x.get("title") or ""))), len(str(x.get("title") or ""))))
        check_rows = [c for c in checks.get(key, []) if not (
            c.get("documents") and all(unrelated_document(d.get("url", "")) for d in c["documents"]))]
        documents = {}
        lookup = lookups.get(key, {})
        for document in lookup.get("documents") or []:
            if normalized_url(document.get("url")) and not unrelated_document(document["url"]):
                documents[normalized_url(document["url"])] = document
        for check in check_rows:
            for document in check.get("documents") or []:
                if normalized_url(document.get("url")) and not unrelated_document(document["url"]):
                    documents[normalized_url(document["url"])] = document
        check = {"errors": [e for c in check_rows for e in c.get("errors") or []] + list(lookup.get("errors") or []), "documents": list(documents.values())}
        if any(c.get("status") == "deferred" for c in check_rows):
            check["status"] = "deferred"
        deadline = str(item.get("deadline_at") or "")
        expired = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline) and deadline < str(payload.get("referenceDate") or ""))
        exclusion = next((publication_exclusion(x) for x in items if publication_exclusion(x)), None)
        noise_reason = classify_signal(item, payload.get("referenceDate"))
        if exclusion:
            status, code, reason, action = "monitor", exclusion["reasonCode"], exclusion["reason"], "Esclusa dal Radar pubblico per il perimetro concreto dei Comuni della Versilia; nessuna ricerca documentale richiesta."
        elif any(x.get("_verifiedPublicationPending") for x in items):
            status, code, reason, action = "retry", "publication_blocked", "Il documento è verificato, ma la pubblicazione è bloccata da un altro controllo del run.", "Il Radar ritenterà la pubblicazione. Se il blocco persiste, correggere il controllo segnalato in cima al rapporto: il documento è già collegato qui e non va ricercato nuovamente."
        elif key in represented:
            status, code, reason, action = "covered", "exact_public_reference", "La stessa fonte è già associata a una scheda del Radar.", "Gli eventuali aggiornamenti restano soggetti alla riconferma della scheda; non è una nuova opportunità da inserire."
        elif expired or (check_rows and all(c.get("status") == "expired" for c in check_rows)):
            status, code, reason, action = "expired", "verified_expiry", "Il termine strutturato di candidatura risulta concluso.", "Nessun inserimento tra le opportunità aperte; verificare solo eventuali successive proroghe."
        elif noise_reason:
            status, code = "monitor", noise_reason
            reason = {"catalog_or_navigation": "È una pagina di catalogo o navigazione, non una scheda di bando.",
                      "archive_page": "È una pagina di archivio, non una nuova finestra di candidatura verificata.",
                      "procurement_notice": "È una procedura di acquisto della Prefettura, non un contributo per i Comuni.",
                      "administrative_update": "È un resoconto amministrativo, non una nuova candidatura.",
                      "informational_event": "È la pagina di un evento informativo, non un bando."}[code]
            action = "Esclusa dalla coda di verifica documentale; il monitoraggio della fonte resta attivo."
        elif lookup.get("assessment"):
            assessment = lookup["assessment"]
            status, code, reason, action = assessment["status"], assessment["reasonCode"], assessment["reason"], assessment["action"]
            deadline = assessment.get("deadline") or deadline
            if status == "covered" and not any(x.get("coverage_id") == assessment.get("representedCoverageId") for x in payload.get("opportunities") or []):
                status, code, reason, action = "technical", "published_reference_missing", "La scheda precedentemente verificata non è presente nello snapshot corrente.", "Responsabilità del Radar: verificare il motivo della mancata pubblicazione."
        elif is_administrative_update(str(item.get("title") or ""), str(item.get("url") or "")) or lookup.get("classification") == "administrative_update" or (check_rows and all(c.get("status") == "administrative_update" for c in check_rows)):
            status, code, reason, action = "monitor", "administrative_update", "La notizia riguarda progetti già candidati, approvati o fondi assegnati; non documenta una nuova candidatura.", "Nessuna nuova candidatura da pubblicare. Il Radar continua a monitorare eventuali riaperture."
        else:
            status, code, reason, action = _diagnosis(check, item)
        document_lookup = "found" if documents else ("not_attempted" if check.get("status") == "deferred" else "failed" if lookup.get("status") == "error" or (status == "retry" and check_rows) else "not_found" if check_rows or lookup.get("status") == "ok" else "not_attempted")
        if status == "technical" and code == "unverified_signal" and document_lookup == "not_attempted" and normalized_url(item.get("url")):
            status, code = "retry", "document_lookup_pending"
            reason = "La ricerca automatica degli allegati deve ancora essere eseguita."
            action = "Attendere il tentativo automatico: i riferimenti rinviati hanno priorità nei run successivi. Il rapporto segnalerà l’eventuale verifica di persona con il documento individuato o il motivo della mancata acquisizione."
        rows.append({"title": str(item.get("title") or "Segnalazione senza titolo"),
                     "url": str(item.get("url") or ""), "source": str(item.get("source_label") or item.get("source_id") or "Fonte non indicata"),
                     "deadline": deadline, "status": status, "statusLabel": LABELS[status], "reasonCode": code,
                     "reason": reason, "action": action, "documents": list(documents.values()),
                     "documentLookup": document_lookup,
                     "technicalDetails": check["errors"], "signalCount": len(items),
                     "representedBy": represented.get(key)})
    discarded = [x for x in rows if x["status"] == "expired" or x["reasonCode"] in {
        "outside_municipal_call", "reviewed_closed_catalogue", "administrative_update",
        "catalog_or_navigation", "archive_page", "procurement_notice", "informational_event"}]
    rows = [x for x in rows if x not in discarded]
    order = {"human": 0, "technical": 1, "retry": 2, "covered": 3, "expired": 4, "monitor": 5}
    rows.sort(key=lambda x: (order[x["status"]], x["deadline"] or "9999-99-99", x["title"].casefold()))
    return {"version": 1, "signalCount": sum(x["signalCount"] for x in rows), "uniqueCount": len(rows),
            "duplicatesGrouped": sum(x["signalCount"]-1 for x in rows),
            "discardedCount": len(discarded), "discarded": discarded, "counts": dict(Counter(x["status"] for x in rows)), "items": rows}


def collect_document_links(payload, *, previous=None, budget=None, loader=None, max_pages=24, max_seconds=90):
    """Locate attachments before requesting human work, within the live budget.

    This gathers links only. HTML text never bypasses the PDF publication gates.
    Previous lookups are retained with dates and refreshed after seven days;
    unfetched signals are prioritised so the cap does not starve the same pages.
    """
    from opportunity_document_promotion import HOSTS, trusted
    previous_rows = {normalized_url(x.get("url")): x for x in (previous or {}).get("reviewDocumentLookup") or []}
    actions = build_actions(payload)
    promotion_urls = {normalized_url(c.get("url")) for c in (payload.get("documentPromotion") or {}).get("checks") or [] if c.get("documents")}
    assessment_path = Path(__file__).resolve().parents[1] / "data/opportunity-audit-fixes-v1.json"
    reviewed_urls = {normalized_url(x["url"]) for x in json.loads(assessment_path.read_text(encoding="utf-8")).get("reviewAssessments", [])}
    candidates = [x for x in actions["items"] + actions["discarded"] if (x["status"] in ("human", "technical", "retry") or normalized_url(x["url"]) in reviewed_urls)
                  and (normalized_url(x["url"]) not in promotion_urls or normalized_url(x["url"]) in reviewed_urls)]
    today = date.fromisoformat(payload["referenceDate"])
    result = {}
    # Keep located attachments even when a later diagnostic changes category.
    for row in actions["items"] + actions["discarded"]:
        key = normalized_url(row["url"])
        if key in previous_rows:
            result[key] = {**previous_rows[key], "documents": [d for d in previous_rows[key].get("documents") or []
                           if not unrelated_document(d.get("url", ""))]}
    hosts = HOSTS | ({urlsplit("https://"+h).hostname for h in budget.hosts} if budget is not None else set())
    def fetch(url, cap):
        if loader is not None:
            return loader(url)
        cached = budget.cache.get(("discovery", url, "{}"))
        if cached and isinstance(cached[0], str) and "<a" in cached[0]:
            return {"text": cached[0], "resolvedUrl": cached[1].get("resolvedUrl") or url}
        receipt, trace = budget.fetch(url, kind="review_page", timeout=5, attempts=1,
                                     options={"allowedHosts": sorted(hosts)}, max_seconds=cap)
        if receipt is None:
            raise ValueError("; ".join(trace.get("errors") or ["Acquisizione fallita"]))
        return receipt
    def fresh(row):
        old = previous_rows.get(normalized_url(row["url"]), {})
        try:
            return (old.get("status") == "ok"
                    and old.get("extractorVersion") == pdf.LINK_EXTRACTOR_VERSION
                    and 0 <= (today-date.fromisoformat(old["checkedAt"])).days < 7)
        except (ValueError, KeyError):
            return False
    # Oldest attempts first; pages never attempted come before failed retries.
    candidates.sort(key=lambda row: (normalized_url(row["url"]) not in reviewed_urls, previous_rows.get(normalized_url(row["url"]), {}).get("checkedAt", ""),
                                     row["deadline"] or "9999-99-99", row["title"].casefold()))
    until = time.monotonic() + max_seconds
    attempted = 0
    for row in candidates:
        key = normalized_url(row["url"])
        if fresh(row) or not trusted(row["url"], hosts):
            continue
        remaining = min(until-time.monotonic(), budget.deadline-time.monotonic() if budget is not None else max_seconds)
        if attempted >= max_pages or remaining <= 0 or (loader is None and budget is None):
            break
        attempted += 1
        old_docs = [{**d, "status": "previously_located"} for d in (result.get(key, {}).get("documents") or [])]
        entry = {"url": row["url"], "checkedAt": today.isoformat(), "status": "error", "documents": old_docs, "errors": [],
                 "extractorVersion": pdf.LINK_EXTRACTOR_VERSION}
        result[key] = entry
        try:
            if re.search(r"\.pdf(?:$|[?#])", row["url"], re.I):
                urls, text = [row["url"]], ""
            else:
                acquired = fetch(row["url"], min(8, remaining))
                page = acquired["text"] if isinstance(acquired, dict) else acquired
                base = acquired.get("resolvedUrl") or row["url"] if isinstance(acquired, dict) else row["url"]
                urls = pdf.pdf_links(page, base, limit=8)
                text = page
            entry.update(status="ok", documents=[{"url": u, "status": "located", "lastSeen": today.isoformat()} for u in urls if normalized_url(u)])
            assessment = reviewed_source(text, row["url"])
            if assessment:
                entry["assessment"] = assessment
            if is_administrative_update(text, row["url"]):
                entry["classification"] = "administrative_update"
        except Exception as exc:
            entry["errors"].append(str(exc))
    payload["reviewDocumentLookup"] = list(result.values())
    return payload


def _link(url, label):
    if not normalized_url(url):
        return html.escape(label)
    return f'<a href="{html.escape(url, quote=True)}" rel="noopener noreferrer">{html.escape(label)}</a>'


def document_label(document, index):
    name = unquote(urlsplit(document["url"]).path.rsplit("/", 1)[-1])
    label = name if name.lower().endswith(".pdf") else f"Documento {index+1}"
    return label + (" (riferimento precedente)" if document.get("status") == "previously_located" else "")


def render_actions_html(actions):
    counts = actions.get("counts") or {}
    blocks = []
    for status in LABELS:
        rows = [x for x in actions.get("items") or [] if x["status"] == status]
        if not rows:
            continue
        cards = []
        for row in rows:
            docs = " · ".join(_link(d["url"], document_label(d, i)) for i, d in enumerate(row["documents"]))
            lookup = {"not_found": "Documento ufficiale non individuato dal Radar.", "not_attempted": "Ricerca degli allegati non ancora eseguita.", "failed": "Ricerca degli allegati non riuscita."}.get(row["documentLookup"], "")
            technical = "" if not row["technicalDetails"] else '<details><summary>Dettaglio del controllo</summary><p>' + html.escape("; ".join(row["technicalDetails"])) + '</p></details>'
            cards.append('<article class="review-action"><h3>' + _link(row["url"], row["title"]) + '</h3><p>' + html.escape(row["source"]) + '</p><p><strong>Motivo:</strong> ' + html.escape(row["reason"]) + '</p><p><strong>Cosa fare:</strong> ' + html.escape(row["action"]) + '</p><p>' + _link(row["url"], "Pagina sorgente") + (' · '+docs if docs else ' · '+lookup) + '</p>' + technical + '</article>')
        body = ''.join(cards)
        if status in ("covered", "expired", "monitor"):
            body = f'<details><summary>{html.escape(LABELS[status])}: {len(rows)}</summary>{body}</details>'
        else:
            body = f'<h3>{html.escape(LABELS[status])}: {len(rows)}</h3>{body}'
        blocks.append(body)
    return ('<section id="verifiche-richieste"><h2>Verifiche richieste</h2><p><strong>' + str(counts.get("human", 0)) + ' verifiche di persona</strong> · ' + str(counts.get("retry", 0)) + ' ritentativi automatici · ' + str(counts.get("technical", 0)) + ' interventi sul Radar. Queste segnalazioni non sono opportunità pubblicate.</p><p>' + str(actions.get("duplicatesGrouped", 0)) + ' ripetizioni raggruppate; ogni segnalazione resta contabilizzata.</p>' + ''.join(blocks) + '</section>')


def render_actions_markdown(actions):
    counts = actions.get("counts") or {}
    lines = ["", "## Verifiche richieste", "", f"**Di persona: {counts.get('human', 0)} · Ritentativi automatici: {counts.get('retry', 0)} · Interventi sul Radar: {counts.get('technical', 0)}**. Le segnalazioni non sono opportunità pubblicate.", "", f"{actions.get('signalCount', 0)} segnalazioni, {actions.get('uniqueCount', 0)} riferimenti distinti; {actions.get('duplicatesGrouped', 0)} ripetizioni raggruppate."]
    def link(url, label):
        label = re.sub(r"[\[\]<>\r\n|]", " ", label)
        safe_url = str(url)
        for char, escaped in (("<", "%3C"), (">", "%3E"), ("|", "%7C"), ("\r", "%0D"), ("\n", "%0A")):
            safe_url = safe_url.replace(char, escaped)
        return f"[{label}](<{safe_url}>)" if normalized_url(url) else label
    groups = {}
    for row in actions.get("items") or []:
        if row["status"] in ("human", "technical", "retry"):
            groups.setdefault((row["status"], row["reasonCode"]), []).append(row)
    for rows in groups.values():
        first = rows[0]
        lines += ["", f"### {first['statusLabel']} · {first['reason']}", "", f"**Cosa fare:** {first['action']}", "", "| Segnalazione e pagina sorgente | Documenti individuati | Termine indicato |", "|---|---|---|"]
        for row in rows:
            docs = " · ".join(link(d["url"], document_label(d, i)) for i, d in enumerate(row["documents"]))
            if not docs:
                docs = {"not_found": "Non individuato", "failed": "Ricerca non riuscita"}.get(row["documentLookup"], "Ricerca non eseguita")
            lines.append(f"| {link(row['url'], row['title']).replace('|', ' ')} | {docs.replace('|', ' ')} | {row['deadline'] or 'Da verificare'} |")
    lines += ["", f"Già rappresentate: {counts.get('covered', 0)} · Termini conclusi: {counts.get('expired', 0)} · Pagine di monitoraggio: {counts.get('monitor', 0)}. Dettagli completi nel rapporto HTML/JSON."]
    return "\n".join(lines) + "\n"
