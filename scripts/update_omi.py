#!/usr/bin/env python3
"""Quotazioni residenziali OMI: nuovo semestre per le zone dei sette Comuni.

Usato da `update_source_data.py omi-residential --semester AAAA-SN`. Percorre la
consultazione pubblica dell'Agenzia delle Entrate (provincia → Comune e
semestre → zona → destinazione residenziale) e legge, per ogni zona, l'intervallo
min/max di compravendita e locazione delle «Abitazioni civili» in stato
«NORMALE». Il valore di zona pubblicato è il punto medio dell'intervallo
(compravendita in €/m², locazione in €/m² al mese arrotondata al decimo).

Prima di scrivere il semestre nuovo rilegge dalla fonte il semestre pubblicato e
verifica che la stessa regola riproduca esattamente tutti i valori di zona del
catalogo: se non li riproduce si ferma.
"""
from __future__ import annotations

import html as htmllib
import http.cookiejar
import re
import time
import urllib.parse
import urllib.request
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

BASE = "https://www1.agenziaentrate.gov.it/servizi/Consultazione/"
SEARCH, RESULT = BASE + "ricerca.php", BASE + "risultato.php"
PROVINCE = "LU"
TOWNS = {"Camaiore": "046005", "Forte dei Marmi": "046013", "Massarosa": "046018", "Pietrasanta": "046024",
         "Seravezza": "046028", "Stazzema": "046030", "Viareggio": "046033"}
UA = {"User-Agent": "Mozilla/5.0 (compatible; OsservatorioVersilia-data-audit/1.0)"}
TYPE, STATE = "Abitazioni civili", "NORMALE"
SNAPSHOT_PREFIX = "omi-residential-"


class OmiError(RuntimeError):
    pass


def semester_code(semester: str) -> str:
    m = re.fullmatch(r"(\d{4})-S([12])", semester)
    if not m:
        raise OmiError(f"semestre {semester!r}: atteso AAAA-S1 o AAAA-S2")
    return m.group(1) + m.group(2)


def semester_label(semester: str) -> str:
    year, half = semester.split("-S")
    return f"{half}° semestre {year}"


def label_semester(label: str) -> str:
    m = re.fullmatch(r"([12])° semestre (\d{4})", label.strip())
    if not m:
        raise OmiError(f"semestre pubblicato {label!r} non riconosciuto")
    return f"{m.group(2)}-S{m.group(1)}"


class Session:
    def __init__(self) -> None:
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def post(self, url: str, fields: dict[str, str]) -> str:
        data = urllib.parse.urlencode(fields).encode()
        error: Exception | None = None
        for attempt in range(4):
            try:
                with self.opener.open(urllib.request.Request(url, data=data, headers=UA), timeout=120) as r:
                    return r.read().decode("utf-8", errors="replace")
            except Exception as exc:  # noqa: BLE001 - nuovo tentativo e poi errore esplicito
                error = exc
                time.sleep(3 * (attempt + 1))
        raise OmiError(f"consultazione OMI non raggiungibile ({url}): {error}")


def options(page: str, name: str) -> list[tuple[str, str]]:
    m = re.search(rf"<select\b[^>]*name=[\"']?{name}\b[^>]*>(.*?)</select>", page, flags=re.I | re.S)
    if not m:
        raise OmiError(f"campo {name} assente nella pagina")
    return [(attr("value", tag), re.sub(r"\s+", " ", htmllib.unescape(t)).strip())
            for tag, t in re.findall(r"(<option\b[^>]*>)([^<]*)", m.group(1), flags=re.I)]


def attr(name: str, tag: str) -> str:
    found = re.search(rf"\b{name}\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))", tag, re.I)
    return htmllib.unescape(next((g for g in found.groups() if g is not None), "")) if found else ""


def hidden(page: str, action: str) -> dict[str, str]:
    for m in re.finditer(r"<form\b([^>]*)>(.*?)</form>", page, flags=re.I | re.S):
        if action in attr("action", m.group(1)):
            return {attr("name", t): attr("value", t) for t in re.findall(r"<input\b[^>]*>", m.group(2), flags=re.I)
                    if attr("type", t).lower() == "hidden" and attr("name", t)}
    raise OmiError(f"modulo {action} assente")


def number(text: str) -> Decimal:
    return Decimal(text.replace(".", "").replace(",", "."))


def text_of(page: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<(script|style)\b.*?</\1>|<[^>]+>", " ", page, flags=re.I | re.S)))


def parse_result(page: str, semester: str) -> dict[str, Any]:
    text = text_of(page)
    year, half = semester.split("-S")
    if f"Anno {year} - Semestre {half}" not in text:
        raise OmiError(f"risultato OMI non relativo al semestre {semester}")
    prevalent = re.search(r"Tipologia prevalente:\s*(.+?)\s+Destinazione:", text)
    num = r"(\d[\d.]*(?:,\d+)?)"
    m = re.search(rf"{TYPE}\s*(\*?)\s*{STATE}\s+{num}\s+{num}\s+([LN])\s+{num}\s+{num}\s+([LN])", text)
    if not m:
        raise OmiError(f"riga «{TYPE} {STATE}» con compravendita e locazione assente")
    smin, smax, rmin, rmax = (number(m.group(i)) for i in (2, 3, 5, 6))
    if not (0 < smin <= smax and 0 < rmin <= rmax):
        raise OmiError("intervallo OMI non valido")
    return {"prevalentType": prevalent.group(1).strip() if prevalent else None, "rectified": bool(m.group(1)),
            "saleMin": float(smin), "saleMax": float(smax), "saleSurface": m.group(4),
            "rentMin": float(rmin), "rentMax": float(rmax), "rentSurface": m.group(7),
            "sale": float((smin + smax) / 2), "rent": float(((rmin + rmax) / 2).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))}


def town_codes(session: Session) -> dict[str, str]:
    page = session.post(SEARCH, {"level": "1", "lingua": "IT", "pr": PROVINCE})
    names = {t.upper(): v for v, t in options(page, "co")}
    if any(t.upper() not in names for t in TOWNS):
        raise OmiError("Comuni della Versilia non tutti presenti nella provincia di Lucca")
    return {t: names[t.upper()] for t in TOWNS}


def semesters(session: Session) -> list[str]:
    page = session.post(SEARCH, {"level": "1", "lingua": "IT", "pr": PROVINCE})
    return [f"{v[:4]}-S{v[4]}" for v, _ in options(page, "anno_semestre") if re.fullmatch(r"\d{4}[12]", v)]


def read_semester(session: Session, semester: str, codes: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    code = semester_code(semester)
    out: dict[str, list[dict[str, Any]]] = {}
    for town, co in codes.items():
        base = {"lingua": "IT", "pr": PROVINCE, "co": co, "anno_semestre": code}
        page = session.post(SEARCH, {**base, "level": "2"})
        zones = []
        for link, label in options(page, "linkzonastrada"):
            dest = session.post(SEARCH, {**base, "level": "4", "linkzonastrada": link})
            fields = hidden(dest, "risultato.php")
            result = session.post(RESULT, {**fields, "utilizzo": "Residenziale", "bt1": "Mostra valori"})
            try:
                values = parse_result(result, semester)
            except OmiError as error:
                raise OmiError(f"{town} {fields.get('codzona')}: {error}") from error
            zones.append({"code": fields.get("codzona") or label.split("/")[0], "linkzona": link,
                          "band": fields.get("fasciazona", ""), "sourceLabel": label, **values})
        if not zones or len({z["code"] for z in zones}) != len(zones):
            raise OmiError(f"{town}: zone OMI assenti o duplicate")
        out[town] = zones
    return out
