#!/usr/bin/env python3
"""Conservative exclusions for discovery leads, never publication decisions."""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import unquote, urlsplit

GENERIC = re.compile(
    r"^(?:aggiornamenti da .+|navigazione(?: principale)?|main navigation|footer\b.*|"
    r"menu bottom|briciole di pane|breadcrumb|cerca nel sito|sezione link utili|"
    r"seguici su|siti collegati|non hai trovato quello che cerchi\?|"
    r"identità e loghi|guide e risorse|notizie|latest news|related content|"
    r"bandi e avvisi(?: pubblici)?|avvisi e bandi|archivio bandi|calls? for proposals|"
    r"amministrazione trasparente|organizzazione|lista dei comunicati|"
    r"ultime comunicazioni|ultimi aggiornamenti per i comuni|big picture|"
    r"bonus e contributi attivi|prefetture - ministero dell.interno|"
    r"osservatorio sulla finanza e la contabilità degli enti locali|"
    r"strong interreg, strong regions, strong europe|"
    r"come mettersi in comunicazione con il ministero .+|our topics|"
    r"(?:ciao,\s*)?questa pagina . stata utile\?|progetti e finanziamenti per il pnrr)$", re.I)
REOPENING = re.compile(r"prorog\w*|riapert\w*|nuova\s+finestra|"
                      r"(?:presentare|inviare)\s+(?:le\s+)?(?:domande|candidature)|"
                      r"(?:aperto|apertura)\s+(?:il\s+|del\s+)?bando", re.I)


def classify_signal(item, reference_date=None):
    from opportunity_review_actions import publication_exclusion
    if publication_exclusion(item):
        return "outside_municipal_scope"
    title = re.sub(r"\s+", " ", str(item.get("title") or "")).strip()
    location = urlsplit(str(item.get("url") or ""))
    path = unquote(location.path).casefold().rstrip("/")
    context = title + " " + str(item.get("summary") or "")
    if title.casefold() == "call for proposals" and path not in {
        "/en/activities/digital-programme", "/en/activities/get-funding-digital"}:
        return None
    if GENERIC.fullmatch(title):
        return "catalog_or_navigation"
    if (location.hostname == "www.artea.toscana.it" and path.startswith("/fondo/")
            and re.fullmatch(r"FEASR-PSR \d{4}-\d{4} Fondo europeo agricolo per lo sviluppo rurale", title, re.I)):
        return "catalog_or_navigation"
    if (location.hostname == "cinea.ec.europa.eu" and path == "/programmes/life/clean-energy-transition_en"
            and title == "LIFE Clean Energy Transition sub-programme"):
        return "catalog_or_navigation"
    if (location.hostname == "www.regione.toscana.it" and re.search(
            r"^Posizioni di elevata qualificazione: avvisi interni per incarichi|"
            r"^Domanda per l.esercizio temporaneo della professione infermieristica$", title, re.I)):
        return "outside_municipal_scope"
    if (location.hostname == "www.sport.governo.it" and re.search(
            r"^Borse di studio per studenti universitari|^Sostegno alla maternità delle atlete$", title, re.I)):
        return "outside_municipal_scope"
    if (location.hostname == "prefettura.interno.gov.it" and re.search(
            r"^Ordinanza prefettizia (?:divieto vetro|prescrizioni)|"
            r"^Misure sulla movida, chiusi|"
            r"^(?:AVVISO:\s*)?Chiusura temporanea degli uffici|"
            r"^(?:Esito sorteggio revisore|Pubblicazione data sorteggio nomina dell.organo)|"
            r"^Sequestro/fermo veicoli|^DECRETO FLUSSI\b|"
            r"^Videosorveglianza urbana Protocolli fra sale operative", title, re.I)):
        return "administrative_update"
    if (location.hostname == "prefettura.interno.gov.it" and
            re.search(r"^Avviso pubblico iscrizione Depositerie e Centri di Raccolta$", title, re.I)):
        return "outside_municipal_scope"
    if (location.hostname == "www.casaitalia.governo.it" and
            re.search(r"^Avviso Isole minori marine", title, re.I)):
        return "outside_municipal_scope"
    if ((location.hostname == "www.padigitale2026.gov.it" and path == "/enti/comuni"
         and title == "Avvisi di finanziamento") or
        (location.hostname == "dait.interno.gov.it" and path == "/finanza-locale"
         and title == "Banche dati degli enti locali") or
        (location.hostname == "www.masaf.gov.it" and path == "/svilupporurale"
         and title.startswith("Valutazione Ambientale Strategica"))):
        return "catalog_or_navigation"
    if ((location.hostname == "www.sport.governo.it" and path == "/it/bandi-e-avvisi/sport-e-periferie"
         and title == "Sport e periferie") or
        (location.hostname == "urbact.eu" and path == "/get-involved"
         and title == "Discover URBACT's latest opportunities and get involved!") or
        (location.hostname == "cinea.ec.europa.eu" and re.fullmatch(r"/life-calls-proposals-\d{4}_en", path)
         and title == "Coordination and Support Action Grants (CSA) for clean energy transition sub-programme")):
        return "catalog_or_navigation"
    if (location.hostname == "www.sviluppo.toscana.it" and path.endswith("_var")
            and re.search(r"\(varianti\)$",title,re.I)):
        return "administrative_update"
    if (location.hostname == "www.pariopportunita.gov.it" and
            re.search(r"^Avviso Violenza \d{4}: pubblicate le Linee Guida.*rendicontazione",title,re.I)):
        return "administrative_update"
    if (location.hostname == "www.regione.toscana.it" and title.startswith("I vincitori del concorso")):
        return "administrative_update"
    if ((location.hostname == "www.funzionepubblica.gov.it" and path == "/it/il-dipartimento/notizie-del-dipartimento"
         and title == "Banda ultra larga e comunicazioni elettroniche") or
        (location.hostname == "www.politichecoesione.governo.it" and path in {
            "/it/finanziamenti-avvisi-e-bandi/dottorati-comunali",
            "/it/finanziamenti-avvisi-e-bandi/fondo-concorsi-progettazione-e-idee-per-la-coesione-territoriale",
            "/it/finanziamenti-avvisi-e-bandi/fondo-di-sostegno-ai-comuni-marginali"}
         and title in {"Dottorati comunali","Fondo concorsi progettazione e idee per la coesione territoriale","Fondo di sostegno ai comuni marginali"})):
        return "catalog_or_navigation"
    # Never derive expiry from a decree year or a multi-year programme.
    # Only an explicitly archived route or matching annual archive heading
    # qualifies; a reopening or a still-current structured deadline wins.
    if REOPENING.search(context):
        return None
    reference = str(reference_date or date.today().isoformat())
    deadline = str(item.get("deadline_at") or "")
    current_window = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline) and deadline >= reference)
    if current_window:
        return None

    # Only source-scoped, unequivocally non-actionable headlines. This is a
    # discovery-budget filter, not a decision about a published grant. A
    # reopening/current explicit application window already won above.
    host = (location.hostname or "").casefold()
    if host in {"www.mim.gov.it", "mim.gov.it"} and re.match(
            r"^#?NoiSiamoLeScuole\b", title, re.I):
        return "administrative_update"
    if host in {"www.regione.toscana.it", "regione.toscana.it"}:
        if re.match(r"^Bando Nidi gratis 20\d{2}-20\d{2} per i servizi educativi rivolto alle famiglie$", title, re.I):
            return "outside_municipal_scope"
        if re.match(r"^Riconoscimento dei percorsi formativi degli organismi formativi per Esperta ed Esperto di valutazione", title, re.I):
            return "outside_municipal_scope"
    if host == "prefettura.interno.gov.it" and re.match(
            r"^(?:DATA ESTRAZIONE NOMINATIVI DEI REVISORI CONTABILI|"
            r"Estrazione (?:a Sorte )?Nomina Revisori Dei Conti|"
            r"Comunicazione estrazione nominativi revisore conti)", title, re.I):
        return "administrative_update"
    if host in {"www.mim.gov.it", "mim.gov.it"} and re.match(
            r"^(?:Asili nido, quasi \d+ milioni di euro per ulteriori \d+ interventi|"
            r"Comunicazione apertura piattaforma gestione procedurale e finanziaria\."
            r" Interventi di cui al D\.M\. 06 agosto 2021|"
            r"Interventi di adeguamento degli edifici scolastici alla normativa antisismica\."
            r" Piano 2018-2021 Comunicazione apertura piattaforma)", title, re.I):
        return "administrative_update"
    if host == "prefettura.interno.gov.it":
        if re.match(r"^(?:Il Prefetto (?:incontra|di .+ riceve|.+ saluta)|"
                    r"Il Vicecapo Missione .+ ricevuto dal Prefetto|"
                    r"Comitato Operativo Viabilità|COV su cantieri stradali|"
                    r"Cposp Agitazioni studentesche|Operazioni brillamento|"
                    r"Esercitazione per la gestione di un.emergenza|"
                    r"Giornata pubblica dedicata alla prevenzione|"
                    r"(?:VIII edizione della |Settimana Nazionale della )Settimana nazionale della Protezione Civile|"
                    r"Settimana Nazionale della Protezione Civile|"
                    r"Inaugurazione dei nuovi spazi|Incontro sulla sicurezza|"
                    r"Nomina Commissario Prefettizio|"
                    r"Tentato assalto a un.azienda orafa|"
                    r"Nuovo servizio straordinario|"
                    r"Banche e uffici postali, alleanza per la sicurezza|"
                    r"Estrazione dell.organo Revisione Economico Finanziaria|"
                    r"Finanza locale - Data estrazione organo di revisione|"
                    r"Sorteggio Revisore Dei Conti Comune di|"
                    r"Videosorveglianza: in Prefettura già .+ le domande di finanziamento)", title, re.I):
            return "administrative_update"
        if re.match(r"^(?:AVVISO ESPLORATIVO SERVIZIO DI COND\. OBBLIGATORIA|"
                    r"Manifestazione di interesse per il servizio di interpretariato|"
                    r"INDAGINE ESPLORATIVA DI MERCATO PER MANIFESTAZIONI D.INTERESSE)", title, re.I):
            return "procurement_notice"
    if host == "anci.lombardia.it" and re.search(
            r"^Bando 2027-2028 per l.assegnazione di contributi regionali ai Comuni lombardi|"
            r"^RECALL BANDO SISMICA REGIONE LOMBARDIA", title, re.I):
        return "outside_municipal_scope"
    edition = re.fullmatch(r"Avviso\s+(20\d{2})", title, re.I)
    outcome = re.search(r"chiusura\s+(?:dell[’']?\s*)?avviso|"
                        r"elenco\s+degli\s+eventi\s+ammessi\s+(?:al\s+|a\s+)?contributo", context, re.I)
    if not current_window and (
        (edition and outcome and location.hostname == "www.sport.governo.it"
         and int(edition[1]) < int(reference[:4]) and path.endswith("/avviso-" + edition[1]))
        or (location.hostname == "spettacolo.cultura.gov.it" and path in {
            "/tax-credit-musica-old", "/tax-credit-musica-old-old"})
    ):
        return "archive_page"
    annual_family = re.search(r"(?:-|/)(20\d{2})$", path)
    if (location.hostname == "www.famiglia.governo.it" and annual_family
            and path.rsplit("/", 1)[-1].startswith("finanziamento-")
            and int(annual_family[1]) < int(reference[:4])
            and re.search(r"elenco dei comuni beneficiari", context, re.I)):
        return "archive_page"
    if location.hostname == "prefettura.interno.gov.it":
        if "/amministrazione-trasparente/bandi-gara-e-contratti/" in path:
            return "procurement_notice"
        if re.search(r"\b(?:riunione|visita|firmati.*patti|sigla.*(?:patti|protocolli)|"
                     r"terminata.*istruttoria|graduatoria definitiva)\b", title, re.I):
            return "administrative_update"
        if re.search(r"controlli (?:serali )?interforze ad alto impatto", context, re.I):
            return "administrative_update"
    if (location.hostname == "www.interregeurope.eu" and "/news-events/events/" in path
            and re.search(r"\bstrong regions\b.*\bstrong europe\b", title, re.I)):
        return "informational_event"
    if (location.hostname == "interreg-marittimo.eu"
            and re.search(r"^Rendez-vous Express,.*help desk per la comunicazione dei progetti", title, re.I)):
        return "informational_event"
    if (location.hostname == "cultura.gov.it" and path == "/comunicati/avvisi"
            and re.search(r"^Recovery: Franceschini,.*la cultura guiderà la ripartenza", title, re.I)):
        return "administrative_update"
    if (location.hostname == "www.lavoro.gov.it" and re.search(
            r"^Nasce la .Rete Nazionale delle Città di Fondazione", title, re.I)
            and re.search(r"firma dell.Accordo", context, re.I)):
        return "administrative_update"
    from opportunity_review_actions import is_administrative_update
    if is_administrative_update(title, str(item.get("url") or "")):
        return "administrative_update"
    return None


def content_html(payload):
    """Remove site chrome, retaining article headers and actual attachments."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(payload or "", "html.parser")
    for element in list(soup.select("nav, [role=navigation], [role=contentinfo], "
                                    ".site-header, .site-footer, "
                                    ".elementor-location-header, .elementor-location-footer")):
        if element.parent is not None:
            element.decompose()
    for element in list(soup.find_all(["header", "footer"])):
        if element.find_parent(["main", "article"]) is None:
            element.decompose()
    return str(soup)


def unrelated_document(url):
    name = unquote(urlsplit(str(url)).path.rsplit("/", 1)[-1]).casefold()
    if re.search(r"(?:bando|avviso|allegat|domanda)", name):
        return False
    return bool(re.search(r"statuto.*anci|anci.*statuto|privacy[-_ ]?policy|"
                          r"cookie[-_ ]?policy|dichiarazione[-_ ].*accessibilit", name))


def clean_review_queues(payload, reference_date):
    """Retain exclusions with reasons; remove them before document budgets."""
    discarded = { (x.get("url"), x.get("title"), x.get("reasonCode")): x
                  for x in payload.get("discoveryNoise") or [] }
    for field in ("discoveryQueue", "reviewQueue"):
        kept = []
        for item in payload.get(field) or []:
            reason = classify_signal(item, reference_date)
            if reason:
                row = {"url": item.get("url"), "title": item.get("title"),
                       "source_id": item.get("source_id"), "reasonCode": reason,
                       "summary": item.get("summary", ""), "deadline_at": item.get("deadline_at", "")}
                discarded[(row["url"], row["title"], reason)] = row
            else:
                kept.append(item)
        if field in payload:
            payload[field] = kept
    payload["discoveryNoise"] = list(discarded.values())
    payload.setdefault("counts", {})["discoveryReview"] = len(payload.get("discoveryQueue") or [])
    if "reviewQueue" in payload:
        payload["counts"]["reviewInternal"] = len(payload["reviewQueue"])
    payload["counts"]["discoveryNoiseDiscarded"] = len(discarded)
    return payload
