#!/usr/bin/env python3
"""Verifica mensile del periodo alla fonte, indicatore per indicatore.

Ogni indicatore elencato in `ci/release-probe-coverage.json` con un `probe`
viene confrontato con la fonte ufficiale: ultimo periodo disponibile, valori del
periodo pubblicato e storico già pubblicato. Gli esiti possibili sono tre:

- `current`: stesso periodo, stessi valori, storico invariato;
- `release_detected`: la fonte pubblica un periodo più recente;
- `verification_required`: fonte non scaricabile, struttura cambiata, valori o
  storico diversi da quelli pubblicati. Ogni caso porta un motivo e, quando la
  fonte non si scarica, le istruzioni per chiudere il controllo a mano.

Il modulo non modifica mai i dati pubblicati.

Uso manuale (chiusura di un controllo con un file scaricato a mano):

    python scripts/release_period_probes.py --catalog dist/data/site-data.json \
        --metric mortalityAll --file ~/Download/1438-dati_indicatori.zip
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "ci" / "release-probe-coverage.json"
TOWN_CODES = ("046005", "046013", "046018", "046024", "046028", "046030", "046033")
VERSILIA_ARS = "202M"
ARS_EXPORT = "https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore={id}"
ARS_TIMEOUT = 300
ARS_ATTEMPTS = 3
# I valori pubblicati sono arrotondati a due decimali.
TOLERANCE = 0.0051
USER_AGENT = "OsservatorioVersilia-source-audit/1.0 (+https://osservatorioversilia.it)"

Fetcher = Callable[[str], bytes]
# Catalogo in verifica: alcune famiglie usano denominatori pubblicati (es. popolazione).
CATALOG: dict[str, Any] = {}


class ProbeError(RuntimeError):
    """Errore che impedisce di leggere la fonte: richiede un'azione."""

    def __init__(self, reason: str, detail: str):
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


def load_coverage(path: Path = COVERAGE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def norm_period(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).replace("–", "-").replace("—", "-")


def period_key(value: str) -> tuple[int, int, str]:
    parts = [int(p) for p in re.findall(r"\d{4}", value)]
    if not parts:
        return (0, 0, value)
    return (parts[-1], parts[0], value)


def parse_number(text: Any) -> float | None:
    value = str(text or "").strip()
    if not value:
        return None
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        value = value.replace(",", ".")
    return float(value)


def http_fetch(url: str, timeout: float = ARS_TIMEOUT, attempts: int = ARS_ATTEMPTS) -> bytes:
    errors = []
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "it-IT,it;q=0.9"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 410):
                raise ProbeError("not_found", f"{url}: HTTP {exc.code}") from exc
            errors.append(f"tentativo {attempt}: HTTP {exc.code}")
            if attempt < attempts:
                time.sleep(10 * attempt)
        except Exception as exc:  # rete, timeout
            errors.append(f"tentativo {attempt}: {type(exc).__name__}: {exc}")
            if attempt < attempts:
                time.sleep(10 * attempt)
    raise ProbeError("source_unreachable", f"{url}: {attempts} tentativi da {int(timeout)} secondi falliti; " + " | ".join(errors[-2:]))


def zip_members_sha(payload: bytes) -> str:
    digest = hashlib.sha256()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for item in sorted((i for i in archive.infolist() if not i.is_dir()), key=lambda v: (v.filename, v.CRC, v.file_size)):
            digest.update(item.filename.encode("utf-8"))
            digest.update(b"\0")
            digest.update(archive.read(item))
            digest.update(b"\0")
    return digest.hexdigest()


def ars_rows(payload: bytes, spec: dict[str, Any]) -> dict[tuple[str, str], float]:
    """Righe totali dell'export ARS: (codice geografia, periodo) -> misura."""
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            name = next((n for n in archive.namelist() if n.lower().endswith(".csv")), None)
            if name is None:
                raise ProbeError("structure_changed", "lo ZIP ARS non contiene un CSV")
            raw = archive.read(name)
    except zipfile.BadZipFile as exc:
        raise ProbeError("structure_changed", f"il file scaricato non è uno ZIP valido ({exc})") from exc
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required = {"id_indicatore", "anno", "codice_geografia", "sesso", "strato1", "strato2", "misura_grezza", "misura_standardizzata"}
    if not required.issubset(reader.fieldnames or []):
        raise ProbeError("structure_changed", f"colonne ARS cambiate: {reader.fieldnames}")
    field = "misura_grezza" if spec.get("measurement") == "raw" else "misura_standardizzata"
    strata = {s.casefold() for s in spec.get("strato1", ["", "totale"])}
    wanted = {c.lstrip("0") for c in TOWN_CODES} | {VERSILIA_ARS}
    result: dict[tuple[str, str], float] = {}
    for row in reader:
        if str(row["id_indicatore"]).strip() != str(spec["indicatorId"]):
            continue
        code = str(row["codice_geografia"]).strip().lstrip("0")
        if code not in wanted or str(row["sesso"]).strip().casefold() not in {"totale", "total"}:
            continue
        if str(row["strato1"]).strip().casefold() not in strata or str(row["strato2"]).strip().casefold() not in {"", "totale"}:
            continue
        value = parse_number(row[field])
        if value is None:
            continue
        key = (code if code == VERSILIA_ARS else code.zfill(6), norm_period(row["anno"]))
        if key in result:
            raise ProbeError("structure_changed", f"riga duplicata nell'export ARS per {key}")
        result[key] = value
    if not result:
        raise ProbeError("structure_changed", "nessuna riga totale per i sette Comuni nell'export ARS")
    return result


def published_points(metric: dict[str, Any]) -> tuple[str, dict[str, float], dict[tuple[str, str], float]]:
    period = norm_period(metric.get("meta", {}).get("year"))
    current: dict[str, float] = {}
    history: dict[tuple[str, str], float] = {}
    for row in metric.get("rows", []):
        code = str(row.get("code") or "")
        if row.get("value") is not None:
            current[code] = float(row["value"])
        series = row.get("series") if isinstance(row.get("series"), dict) else {}
        for year, value in zip(series.get("years") or [], series.get("values") or []):
            if value is not None:
                history[(code, norm_period(year))] = float(value)
    aggregate = metric.get("aggregate") if isinstance(metric.get("aggregate"), dict) else {}
    if aggregate.get("value") is not None:
        current[VERSILIA_ARS] = float(aggregate["value"])
    return period, current, history


def close(published: float, observed: float) -> bool:
    """Valori pubblicati arrotondati (es. ARS a due decimali) o non arrotondati (bilanci)."""
    if abs(published - observed) <= 1e-6 * max(1.0, abs(observed)):
        return True
    return abs(round(observed + 1e-12, 2) - published) <= TOLERANCE


def evaluate(metric: dict[str, Any], source: dict[tuple[str, str], float], latest: str,
             extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Confronto generico tra fonte e indicatore pubblicato.

    `source` contiene i valori alla fonte per (codice geografia, periodo); `latest` è l'ultimo
    periodo che la fonte pubblica per tutti e sette i Comuni.
    """
    published, current, history = published_points(metric)
    available = {p for (_, p) in source}
    result: dict[str, Any] = {"publishedPeriod": published, "observedLatestPeriod": latest, **(extra or {})}
    differences = []
    if published in available:
        for code, value in sorted(current.items()):
            observed = source.get((code, published))
            if observed is None:
                if code == VERSILIA_ARS:
                    continue  # aggregato non sempre pubblicato dalla fonte
                differences.append({"geography": code, "period": published, "published": value, "observed": None})
            elif not close(value, observed):
                differences.append({"geography": code, "period": published, "published": value, "observed": observed})
    revisions = []
    for (code, period), value in sorted(history.items()):
        observed = source.get((code, period))
        if observed is not None and period != published and not close(value, observed):
            revisions.append({"geography": code, "period": period, "published": value, "observed": round(observed + 1e-12, 2)})
    result["valuesMatchPublished"] = not differences
    result["historyRevisions"] = revisions[:20]
    result["historyRevisionCount"] = len(revisions)
    if published not in available and period_key(latest) < period_key(published):
        result.update(status="verification_required", reason="published_period_missing_at_source")
    elif period_key(latest) > period_key(published):
        result.update(status="release_detected", reason="new_period")
    elif differences:
        result.update(status="verification_required", reason="same_period_values_differ", differences=differences[:20])
    elif revisions:
        result.update(status="verification_required", reason="history_revised")
    else:
        result.update(status="current", reason="match")
    return result


# ---------------------------------------------------------------- ARS

def ars_probe(metric_key: str, metric: dict[str, Any], spec: dict[str, Any], fetch: Fetcher) -> dict[str, Any]:
    url = ARS_EXPORT.format(id=spec["indicatorId"])
    payload = fetch(url)
    source = ars_rows(payload, spec)
    town_periods = [{p for (c, p) in source if c == code} for code in TOWN_CODES]
    if any(not periods for periods in town_periods):
        missing = [c for c, periods in zip(TOWN_CODES, town_periods) if not periods]
        raise ProbeError("structure_changed", f"l'export ARS non contiene i Comuni {missing}")
    latest = max(set.intersection(*town_periods), key=period_key)
    extra = {"url": url, "contentSha256": zip_members_sha(payload), "contentHashMode": "zip-members", "coverage": "7/7"}
    return evaluate(metric, source, latest, extra)


def ars_manual(metric_key: str, spec: dict[str, Any]) -> dict[str, Any]:
    url = ARS_EXPORT.format(id=spec["indicatorId"])
    return {"urls": [url], "steps": [
        f"Aprire {url} da un browser: il download può richiedere oltre due minuti.",
        f"Salvare lo ZIP così come arriva (es. `{spec['indicatorId']}-dati_indicatori.zip`), senza aprirlo né rinominarlo.",
    ]}


# ---------------------------------------------------------------- OpenBDAP, rendiconti dei Comuni

OPENBDAP_RENDICONTO = "https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/{year}/{year}_Rendiconto%20-%20{kind}_TOSCANA.zip"
OPENBDAP_KINDS = {"schemi": "Schemi%20di%20bilancio", "indicatori": "Piano%20degli%20indicatori"}


def openbdap_url(year: int, kind: str) -> str:
    return OPENBDAP_RENDICONTO.format(year=year, kind=OPENBDAP_KINDS[kind])


def is_zip(payload: bytes) -> bool:
    return payload[:2] == b"PK"


def openbdap_values(year: int, family: str, archives: dict[str, bytes]) -> dict[str, dict[str, float]]:
    """Valori per Comune (nome) e indicatore, calcolati con le stesse funzioni dei materializzatori."""
    import build_bilanci_snapshot as v160
    import materialize_bilanci_v139 as v139

    snapshot = json.loads((ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json").read_text(encoding="utf-8"))
    populations = {town: {int(y): v["population_at_1_january"] for y, v in item["years"].items()}
                   for town, item in snapshot["raw"].items()}
    if any(year not in by_year for by_year in populations.values()):
        raise ProbeError("population_missing", f"popolazione al 1° gennaio {year} assente dallo snapshot bilanci")
    if family == "v160":
        raw, _ = v160.build_year(year, populations, {f"{year}-schemi": (archives["schemi"], ""), f"{year}-indicatori": (archives["indicatori"], "")})
        return {town: v160.compute_values(values) for town, values in raw.items()}
    if family == "debt_d1":
        # Profilo del debito, misura principale (PDI 10.4): voce D1 Debiti da finanziamento / popolazione.
        with zipfile.ZipFile(io.BytesIO(archives["schemi"])) as archive:
            name = next((n for n in archive.namelist() if n.endswith("Stato Patrimoniale Passivo_TOSCANA.csv")), None)
            if name is None:
                raise ProbeError("structure_changed", "Stato patrimoniale passivo assente dall'archivio")
            text = archive.read(name).decode("utf-8-sig")
        codes = {item["code"]: town for town, item in json.loads(
            (ROOT / "data" / "source-snapshots" / "salute-finanziaria-v129.json").read_text(encoding="utf-8"))["towns"].items()}
        debt = {town: 0.0 for town in codes.values()}
        for row in csv.DictReader(io.StringIO(text), delimiter=";"):
            code = "046" + (row.get("Codice Comune") or "").strip().zfill(3)
            if (row.get("Codice Provincia") or "").strip() != "046" or code not in codes:
                continue
            if row.get("Codice Tipologia Soggetto") != "ELCOMU" or row.get("Codice II Livello") != "04" or row.get("Codice III Livello") != "01":
                continue
            if (row.get("Codice V Livello") or "00") != "00":
                raise ProbeError("structure_changed", "voce D1 articolata oltre il IV livello: rivedere la somma")
            debt[codes[code]] += parse_number(row.get("Consistenza Anno Corrente")) or 0.0
        return {town: {"financialDebtProfile": amount / populations[town][year]} for town, amount in debt.items()}
    if family == "mission03":
        import materialize_bilanci_v139 as rows_reader
        with zipfile.ZipFile(io.BytesIO(archives["schemi"])) as archive:
            missions = rows_reader.rows_by_town(rows_reader.read_member(archive, rows_reader.MISSION_MEMBER))
        population = CATALOG.get("metrics", {}).get("population", {})
        by_town = {}
        for row in population.get("rows", []):
            series = row.get("series") or {}
            values = dict(zip([int(y) for y in series.get("years", [])], series.get("values", [])))
            values.setdefault(int(population["meta"]["year"]), row.get("value"))
            by_town[row["town"]] = values.get(year)
        result = {}
        for town, rows in missions.items():
            hits = [r for r in rows if (r.get("Codice Missione") or "").strip().zfill(2) == "03"]
            amount = rows_reader.number(hits[0].get("Impegni")) if len(hits) == 1 else None
            result[town] = {"securityMissionExpenditurePerResident": amount / float(by_town[town]) if amount is not None and by_town.get(town) else None}
        return result
    if family == "v139":
        values, _ = v139.extract_year(year, archives["schemi"])
        return {town: {key: (amount / populations[town][year] if amount is not None else None) for key, amount in by_key.items()}
                for town, by_key in values.items()}
    raise ValueError(f"famiglia OpenBDAP sconosciuta: {family}")


def openbdap_probe(metric_key: str, metric: dict[str, Any], spec: dict[str, Any], fetch: Fetcher) -> dict[str, Any]:
    year = int(norm_period(metric.get("meta", {}).get("year")))
    kinds = ["schemi", "indicatori"] if spec["family"] == "v160" else ["schemi"]
    archives = {}
    for kind in kinds:
        payload = fetch(openbdap_url(year, kind))
        if not is_zip(payload):
            raise ProbeError("published_period_missing_at_source", f"l'archivio {kind} {year} non è più uno ZIP")
        archives[kind] = payload
    try:
        following = fetch(openbdap_url(year + 1, "schemi"))
    except ProbeError as error:
        if error.reason != "not_found":
            raise
        following = b""  # il rendiconto successivo non è ancora pubblicato
    try:
        values = openbdap_values(year, spec["family"], archives)
    except ProbeError:
        raise
    except Exception as exc:
        raise ProbeError("structure_changed", f"rendiconto {year} non leggibile: {type(exc).__name__}: {exc}") from exc
    codes = {str(row.get("town")): str(row.get("code")) for row in metric.get("rows", [])}
    source = {(codes[town], str(year)): by_key[metric_key] for town, by_key in values.items()
              if town in codes and by_key.get(metric_key) is not None}
    latest = str(year + 1) if is_zip(following) else str(year)
    extra = {"url": openbdap_url(year, "schemi"), "nextReleaseUrl": openbdap_url(year + 1, "schemi"),
             "contentSha256": hashlib.sha256(archives["schemi"]).hexdigest(), "coverage": f"{len(source)}/7"}
    if len(source) < 7 and latest == str(year):
        raise ProbeError("structure_changed", f"il rendiconto {year} copre {len(source)} Comuni su 7")
    return evaluate(metric, source, latest, extra)


def openbdap_manual(metric_key: str, spec: dict[str, Any], year: int) -> dict[str, Any]:
    kinds = ["schemi", "indicatori"] if spec["family"] == "v160" else ["schemi"]
    urls = [openbdap_url(year, kind) for kind in kinds] + [openbdap_url(year + 1, "schemi")]
    return {"urls": urls, "steps": [
        "Scaricare da un browser gli archivi del rendiconto indicati sotto (ognuno pesa 3–20 MB); "
        f"se l'archivio {year + 1} apre una pagina invece di scaricare uno ZIP, il nuovo rendiconto non è ancora uscito: non serve salvarlo.",
        *[f"- {url}" for url in urls],
        "Non rinominare i file: lo script li riconosce dal nome.",
    ]}


# ---------------------------------------------------------------- SIOPE, movimenti cumulati di dicembre

SIOPE_API = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3"
SIOPE_DUMP = SIOPE_API + "/datastore/dump/{id}.csv"
SIOPE_TITLE = "{year} - Toscana - SIOPE Movimenti cumulati mensili di {movement}"
SIOPE_TOWNS = {"046005": "Camaiore", "046013": "Forte dei Marmi", "046018": "Massarosa", "046024": "Pietrasanta",
               "046028": "Seravezza", "046030": "Stazzema", "046033": "Viareggio"}
SIOPE_FIELDS = ("Codice istat provincia", "Codice istat comune", "Codice Tipologia Ente BDAP", "Anno/Mese calendario",
                "Codice Titolo CG", "Importo cumulato")


def siope_package_url(year: int, movement: str, fetch: Fetcher) -> str:
    """URL del CSV del pacchetto ufficiale, cercato per titolo esatto sul catalogo BDAP."""
    title = SIOPE_TITLE.format(year=year, movement=movement)
    query = urllib.parse.quote(f'"{title}"')
    payload = json.loads(fetch(f"{SIOPE_API}/action/package_search?q={query}&rows=5").decode("utf-8"))
    matches = [p for p in payload.get("result", {}).get("results", []) if p.get("title") == title]
    if not matches:
        raise ProbeError("not_found", f"pacchetto «{title}» assente dal catalogo BDAP")
    return SIOPE_DUMP.format(id=matches[0]["id"])


def siope_totals(raw: bytes, year: int, movement: str) -> dict[str, dict[str, float]]:
    text = raw.decode("cp1252")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    if not set(SIOPE_FIELDS).issubset(reader.fieldnames or []):
        raise ProbeError("structure_changed", f"colonne SIOPE cambiate: {reader.fieldnames}")
    totals = {code: {"total": 0.0, "current": 0.0, "capital": 0.0, "verification": 0.0, "population": 0.0, "rows": 0}
              for code in SIOPE_TOWNS}
    for row in reader:
        if row["Codice istat provincia"].strip() != "046" or row["Codice Tipologia Ente BDAP"].strip() != "CO":
            continue
        code = "046" + row["Codice istat comune"].strip().zfill(3)
        if code not in totals or row["Anno/Mese calendario"].strip() != f"{year}/12":
            continue
        amount = parse_number(row["Importo cumulato"]) or 0.0
        item = totals[code]
        item["total"] += amount
        item["rows"] += 1
        item["population"] = parse_number(row.get("Popolazione ISTAT")) or item["population"]
        if "verifica e controllo" in (row.get("Descrizione CG") or "").casefold():
            item["verification"] += amount
        title = row["Codice Titolo CG"].strip().upper()
        if movement == "Spesa" and title.startswith("U1"):
            item["current"] += amount
        if movement == "Spesa" and title.startswith("U2"):
            item["capital"] += amount
    return totals


SIOPE_NUMERATOR = {
    "siopePayments": lambda e, s: s["total"],
    "currentPayments": lambda e, s: s["current"],
    "capitalPayments": lambda e, s: s["capital"],
    "cashReceiptsPerResident": lambda e, s: e["total"],
    "cashBalancePerResident": lambda e, s: e["total"] - s["total"],
    # Incassi tributari riscossi a seguito di verifica e controllo, sulla popolazione Istat del dataset SIOPE.
    "fiscalRecoveryActivity": lambda e, s: e["verification"],
}
SIOPE_OWN_POPULATION = {"fiscalRecoveryActivity"}


def siope_probe(metric_key: str, metric: dict[str, Any], spec: dict[str, Any], fetch: Fetcher) -> dict[str, Any]:
    year = int(norm_period(metric.get("meta", {}).get("year")))
    snapshot = json.loads((ROOT / "data" / "source-snapshots" / "siope-history-v1.6.0.json").read_text(encoding="utf-8"))
    receipts = siope_totals(fetch(siope_package_url(year, "Entrata", fetch)), year, "Entrata")
    payments = siope_totals(fetch(siope_package_url(year, "Spesa", fetch)), year, "Spesa")
    source = {}
    for code, town in SIOPE_TOWNS.items():
        population = (snapshot["raw"].get(town, {}).get(str(year)) or {}).get("population_resident")
        if not population:
            raise ProbeError("population_missing", f"popolazione residente {town} {year} assente dallo snapshot SIOPE")
        if metric_key in SIOPE_OWN_POPULATION:
            population = receipts[code]["population"]
        if receipts[code]["rows"] and payments[code]["rows"] and population:
            source[(code, str(year))] = SIOPE_NUMERATOR[metric_key](receipts[code], payments[code]) / float(population)
    if len(source) < 7:
        raise ProbeError("structure_changed", f"SIOPE dicembre {year}: {len(source)} Comuni su 7")
    latest = str(year)
    try:
        following = siope_totals(fetch(siope_package_url(year + 1, "Spesa", fetch)), year + 1, "Spesa")
        if all(item["rows"] for item in following.values()):
            latest = str(year + 1)
    except ProbeError as error:
        if error.reason != "not_found":
            raise
    return evaluate(metric, source, latest, {"url": SIOPE_API, "coverage": "7/7", "december": f"{year}/12"})


def siope_manual(metric_key: str, spec: dict[str, Any], year: int) -> dict[str, Any]:
    titles = [SIOPE_TITLE.format(year=year, movement=m) for m in ("Entrata", "Spesa")] + [SIOPE_TITLE.format(year=year + 1, movement="Spesa")]
    return {"urls": ["https://bdap-opendata.rgs.mef.gov.it/"], "steps": [
        "Aprire il catalogo BDAP Open Data (https://bdap-opendata.rgs.mef.gov.it/) e cercare, uno alla volta, i dataset:",
        *[f"- «{title}»" for title in titles],
        "Da ciascuno scaricare la risorsa CSV (50–100 MB) senza aprirla; l'ultimo serve solo a capire se c'è già il dicembre dell'anno nuovo.",
        "Avvisare Claude: con i file allegati il controllo si chiude ricalcolando i valori dei sette Comuni.",
    ]}


# ---------------------------------------------------------------- RGS, Conto annuale del personale

RGS_EXPORT = "https://bdap-opendata.rgs.mef.gov.it/export/csv/{year}---Dipendenti-Pubblici---{name}.csv"
RGS_FILES = {
    "occupation": "Occupazione-e-Turnover---Dati-analitici-per-Ente",
    "age": "Anzianita---Dati-analitici-per-Ente",
    "hires": "Assunzioni---Dati-Analitici-per-Causale-Assunzione",
    "cessations": "Cessazioni---Dati-analitici-per-Causale-Cessazione",
}
RGS_STAFF_COLUMNS = ("NumeroDipendentiDonneTempoPieno", "NumeroDipendentiUominiTempoPieno",
                     "NumeroDipendentiDonnePartTimeInf.50%", "NumeroDipendentiUominiPartTimeInf.50%",
                     "NumeroDipendentiDonnePartTimeSup.50%", "NumeroDipendentiUominiPartTimeSup.50%")
RGS_FILES_BY_MEASURE = {"employeesPer1000": ("occupation",), "age55": ("occupation", "age"),
                        "turnover": ("occupation", "hires", "cessations")}


def rgs_url(year: int, kind: str) -> str:
    return RGS_EXPORT.format(year=year, name=RGS_FILES[kind])


def rgs_rows(raw: bytes, institutions: set[str]):
    if raw[:200].lstrip().lower().startswith((b"<!doctype", b"<html")):
        raise ProbeError("not_found", "il file del Conto annuale non è pubblicato")
    reader = csv.reader(io.StringIO(raw.decode("cp1252")), delimiter=";")
    header = [re.sub(r"\s+", "", h).casefold() for h in next(reader)]
    index = {h: i for i, h in enumerate(header)}
    if "codiceistituzione" not in index:
        raise ProbeError("structure_changed", "colonna Codice Istituzione assente nel Conto annuale")
    for row in reader:
        if len(row) >= len(header) - 1 and row[index["codiceistituzione"]] in institutions:
            yield {h: row[i] if i < len(row) else "" for h, i in index.items()}


def rgs_probe(metric_key: str, metric: dict[str, Any], spec: dict[str, Any], fetch: Fetcher) -> dict[str, Any]:
    year = int(norm_period(metric.get("meta", {}).get("year")))
    towns = json.loads((ROOT / "data" / "source-snapshots" / f"rgs-amministrazione-{year}.json").read_text(encoding="utf-8"))["towns"]
    institution = {item["institutionCode"]: town for town, item in towns.items()}
    counts = {town: {"staff": 0.0, "age55": 0.0, "hires": 0.0, "cessations": 0.0} for town in towns}
    for kind in RGS_FILES_BY_MEASURE[spec["measure"]]:
        for row in rgs_rows(fetch(rgs_url(year, kind)), set(institution)):
            item = counts[institution[row["codiceistituzione"]]]
            if kind == "occupation":
                item["staff"] += sum(parse_number(row.get(c.casefold())) or 0.0 for c in RGS_STAFF_COLUMNS)
            elif kind == "age":
                start = re.match(r"E(\d{3})", row.get("codicefasciaeta", ""))
                if start and int(start.group(1)) >= 55:
                    item["age55"] += (parse_number(row.get("numerodipendentidonne")) or 0.0) + (parse_number(row.get("numerodipendentiuomini")) or 0.0)
            elif "passaggi" not in row.get("descrizionecausale", "").casefold():
                item[kind] += (parse_number(row.get("donne")) or 0.0) + (parse_number(row.get("uomini")) or 0.0)
    rows = {str(r.get("town")): r for r in metric.get("rows", [])}
    source = {}
    for town, item in counts.items():
        row = rows.get(town)
        if row is None or not item["staff"]:
            continue
        if spec["measure"] == "employeesPer1000":
            value = item["staff"] / float(row["residentPopulation"]) * 1000
        elif spec["measure"] == "age55":
            value = item["age55"] / item["staff"] * 100
        else:
            value = (item["hires"] - item["cessations"]) / item["staff"] * 100
        source[(str(row["code"]), str(year))] = value
    if len(source) < 7:
        raise ProbeError("structure_changed", f"Conto annuale {year}: {len(source)} Comuni su 7")
    latest = str(year)
    try:
        next(iter(rgs_rows(fetch(rgs_url(year + 1, "occupation")), set(institution))), None)
        latest = str(year + 1)
    except ProbeError as error:
        if error.reason != "not_found":
            raise
    return evaluate(metric, source, latest, {"url": rgs_url(year, "occupation"), "nextReleaseUrl": rgs_url(year + 1, "occupation"), "coverage": "7/7"})


def rgs_manual(metric_key: str, spec: dict[str, Any], year: int) -> dict[str, Any]:
    urls = [rgs_url(year, kind) for kind in RGS_FILES_BY_MEASURE[spec["measure"]]] + [rgs_url(year + 1, "occupation")]
    return {"urls": urls, "steps": [
        "Scaricare da un browser i CSV del Conto annuale indicati sotto, senza aprirli né rinominarli:",
        *[f"- {url}" for url in urls],
        f"Se l'ultimo ({year + 1}) mostra «Not Found», il nuovo Conto annuale non è ancora uscito: non serve salvarlo.",
    ]}


# ---------------------------------------------------------------- Istat, demo.istat.it (POSAS, P2, RCS)

DEMO_URL = {
    "posas": "https://demo.istat.it/data/posas/POSAS_{year}_it_046_Lucca.zip",
    "p2": "https://demo.istat.it/data/p2/P2_{year}_it_046_Lucca.zip",
    "rcs": "https://demo.istat.it/data/rcs/Dati_RCS_cittadinanza_{year}.zip",
}
DEMO_DATASET = {"population": "posas", "dependency": "posas", "old_age": "posas", "age_20_34": "posas",
                "density": "posas", "natural": "p2", "mobility_internal": "p2", "mobility_foreign": "p2",
                "mobility_total": "p2", "foreign_share": "rcs"}


def _demo_table(payload: bytes, titled: bool) -> tuple[list[str], list[dict[str, str]]]:
    if not is_zip(payload):
        raise ProbeError("structure_changed", "il file demo.istat non è uno ZIP")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [n for n in archive.namelist() if n.lower().endswith((".csv", ".txt"))]
        if not members:
            raise ProbeError("structure_changed", "ZIP demo.istat senza CSV")
        raw = archive.read(max(members, key=lambda n: archive.getinfo(n).file_size)).decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(raw), delimiter=";"))
    header_index = 1 if titled else 0
    header = [cell.strip() for cell in rows[header_index]]
    records = [dict(zip(header, row + [""] * (len(header) - len(row)))) for row in rows[header_index + 1:] if row]
    return header, records


def _demo_int(value: Any) -> float:
    text = str(value or "").strip().replace(".", "").replace(",", ".")
    return float(text) if text else 0.0


def demo_values(measure: str, payload: bytes, metric: dict[str, Any]) -> dict[str, float]:
    codes = {str(r.get("code")) for r in metric.get("rows", [])}
    rows = {str(r.get("code")): r for r in metric.get("rows", [])}
    dataset = DEMO_DATASET[measure]
    out: dict[str, float] = {}
    if dataset == "posas":
        import acquire_a3_benchmark_demography_candidates as demo
        header, records = _demo_table(payload, titled=True)
        try:
            age_h = demo.pick(header, ("eta",))
            total_h = demo.pick(header, ("totale",), ("maschi", "femmine"))
        except Exception as exc:
            raise ProbeError("structure_changed", f"colonne POSAS cambiate: {header}") from exc
        bands: dict[str, dict[str, float]] = {c: {"total": 0, "young": 0, "work": 0, "old": 0, "b2034": 0, "row999": 0} for c in codes}
        for rec in records:
            code = demo.code_of(rec)
            if code not in bands:
                continue
            age = demo.age_number(rec.get(age_h))
            if age is None:
                continue
            value = _demo_int(rec.get(total_h))
            b = bands[code]
            if age == 999:  # riga di totale del Comune
                b["row999"] += value
                continue
            b["total"] += value
            b["young" if age <= 14 else "work" if age <= 64 else "old"] += value
            if 20 <= age <= 34:
                b["b2034"] += value
        for code, b in bands.items():
            if not b["total"]:
                continue
            if b["row999"] and abs(b["row999"] - b["total"]) > 0.1:
                raise ProbeError("structure_changed", f"POSAS {code}: somma delle età {b['total']} diversa dal totale {b['row999']}")
            out[code] = {
                "population": b["total"],
                "dependency": (b["young"] + b["old"]) / b["work"] * 100,
                "old_age": round(b["old"] / b["young"] * 100, 1),
                "age_20_34": b["b2034"] / b["total"] * 100,
                "density": b["total"] / float(rows[code].get("surfaceKm2") or "nan"),
            }[measure]
    elif dataset == "p2":
        import acquire_a3_benchmark_demography_candidates as demo
        header, records = _demo_table(payload, titled=True)
        h = demo.p2_mobility_headers(header) if measure.startswith("mobility") else demo.p2_natural_headers(header)
        for rec in records:
            code = rec.get("Codice comune", "").strip()
            if code not in codes:
                continue
            mean = (_demo_int(rec[h["jan1"]]) + _demo_int(rec[h["dec31"]])) / 2
            if measure == "natural":
                numerator = _demo_int(rec[h["natural"]])
            else:
                internal = _demo_int(rec[h["internalIn"]]) - _demo_int(rec[h["internalOut"]])
                foreign = _demo_int(rec[h["foreignIn"]]) - _demo_int(rec[h["foreignOut"]])
                numerator = {"mobility_internal": internal, "mobility_foreign": foreign, "mobility_total": internal + foreign}[measure]
            out[code] = numerator / mean * 1000
    else:
        _, records = _demo_table(payload, titled=False)
        totals: dict[str, dict[str, float]] = {}
        for rec in records:
            # Solo codici comunali a 6 cifre: il file contiene anche aggregati territoriali.
            code = re.sub(r"\D", "", str(rec.get("Codice Istat") or "").strip())
            if code not in codes:
                continue
            value = _demo_int(rec.get("Totale"))
            town = totals.setdefault(code, {"foreign": 0.0, "population": 0.0})
            town["population"] += value
            citizenship = str(rec.get("Codice stato di cittadinanza") or "").strip()
            label = str(rec.get("Stato di cittadinanza") or "").strip().casefold()
            if citizenship != "100" and label != "italia":
                town["foreign"] += value
        for code, town in totals.items():
            if town["population"]:
                out[code] = town["foreign"] / town["population"] * 100
    return out


def demo_probe(metric_key: str, metric: dict[str, Any], spec: dict[str, Any], fetch: Fetcher) -> dict[str, Any]:
    year = int(re.findall(r"\d{4}", norm_period(metric.get("meta", {}).get("year")))[-1])
    dataset = DEMO_DATASET[spec["measure"]]
    url = DEMO_URL[dataset].format(year=year)
    values = demo_values(spec["measure"], fetch(url), metric)
    if len(values) < 7:
        raise ProbeError("structure_changed", f"demo.istat {dataset} {year}: {len(values)} Comuni su 7")
    source = {(code, str(year)): value for code, value in values.items()}
    latest = str(year)
    try:
        if is_zip(fetch(DEMO_URL[dataset].format(year=year + 1))):
            latest = str(year + 1)
    except ProbeError as error:
        if error.reason != "not_found":
            raise
    return evaluate(metric, source, latest, {"url": url, "nextReleaseUrl": DEMO_URL[dataset].format(year=year + 1), "coverage": "7/7"})


def demo_manual(metric_key: str, spec: dict[str, Any], year: int) -> dict[str, Any]:
    dataset = DEMO_DATASET[spec["measure"]]
    urls = [DEMO_URL[dataset].format(year=year), DEMO_URL[dataset].format(year=year + 1)]
    return {"urls": urls, "steps": [
        f"Scaricare da un browser {urls[0]} (pochi MB) senza aprirlo.",
        f"Provare anche {urls[1]}: se risponde «Not Found» l'anno successivo non è ancora pubblicato.",
    ]}


PROBES = {
    "ars_export": (ars_probe, lambda key, spec, metric: ars_manual(key, spec)),
    "demo_istat": (demo_probe, lambda key, spec, metric: demo_manual(key, spec, int((re.findall(r"\d{4}", norm_period(metric.get("meta", {}).get("year"))) or ["0"])[-1]))),
    "rgs_conto_annuale": (rgs_probe, lambda key, spec, metric: rgs_manual(key, spec, int(norm_period(metric.get("meta", {}).get("year")) or 0))),
    "siope_cumulative": (siope_probe, lambda key, spec, metric: siope_manual(key, spec, int(norm_period(metric.get("meta", {}).get("year")) or 0))),
    "openbdap_rendiconto": (openbdap_probe, lambda key, spec, metric: openbdap_manual(key, spec, int(norm_period(metric.get("meta", {}).get("year")) or 0))),
}


def manual_action(metric_key: str, spec: dict[str, Any], metric: dict[str, Any], error: ProbeError) -> dict[str, Any]:
    guide = PROBES[spec["probe"]][1](metric_key, spec, metric)
    files = " ".join("--file <file>" for _ in guide["urls"])
    return {
        "metric": metric_key,
        "reason": error.reason,
        "detail": error.detail,
        "url": guide["urls"][0],
        "urls": guide["urls"],
        "steps": [
            *guide["steps"],
            "Allegare i file alla conversazione con Claude oppure caricarli nella PR del controllo mensile.",
            f"Chiudere il controllo con: `python scripts/release_period_probes.py --catalog dist/data/site-data.json --metric {metric_key} {files}`.",
        ],
    }


def local_fetcher(files: list[Path]) -> Fetcher:
    """Serve i file scaricati a mano: riconosciuti dal nome del file nell'URL o, per ARS, dall'identificativo."""
    by_name = {path.name: path for path in files}

    def fetch(url: str) -> bytes:
        name = urllib.parse.unquote(url.rsplit("/", 1)[-1])
        if name in by_name:
            return by_name[name].read_bytes()
        match = re.search(r"indicatore=(\d+)", url)
        if match:
            for path in files:
                if re.search(rf"(^|\D){match.group(1)}(\D|$)", path.name):
                    return path.read_bytes()
        if "/Datasets_FET/Rendiconto/" in url:
            # Il rendiconto dell'anno successivo si allega solo se esiste: se manca, non è uscito.
            return b""
        raise ProbeError("source_unreachable", f"file non fornito per {url}")

    return fetch


def probe_metric(metric_key: str, metric: dict[str, Any], spec: dict[str, Any], fetch: Fetcher = http_fetch,
                 local_file: Path | list[Path] | None = None) -> dict[str, Any]:
    if spec.get("probe") not in PROBES:
        raise ValueError(f"probe non supportato: {spec.get('probe')}")
    if local_file is not None:
        fetch = local_fetcher(local_file if isinstance(local_file, list) else [local_file])
    try:
        result = PROBES[spec["probe"]][0](metric_key, metric, spec, fetch)
    except ProbeError as error:
        return {
            "metric": metric_key, "probe": spec["probe"], "status": "verification_required",
            "publishedPeriod": norm_period(metric.get("meta", {}).get("year")),
            "reason": error.reason, "detail": error.detail,
            "manualAction": manual_action(metric_key, spec, metric, error),
        }
    result.update(metric=metric_key, probe=spec["probe"], acquisition="manual_file" if local_file else "automatic")
    return result


def run_all(data: dict[str, Any], coverage: dict[str, Any], fetch: Fetcher = http_fetch) -> dict[str, dict[str, Any]]:
    """Esegue i probe di tutti gli indicatori coperti; un download per export condiviso."""
    cache: dict[str, Any] = {}

    def cached(url: str) -> bytes:
        if url not in cache:
            try:
                cache[url] = fetch(url)
            except ProbeError as error:
                cache[url] = error
        if isinstance(cache[url], ProbeError):
            raise cache[url]
        return cache[url]

    CATALOG.clear()
    CATALOG.update(data)
    results = {}
    for key, spec in coverage.get("metrics", {}).items():
        if "probe" not in spec:
            continue
        metric = data.get("metrics", {}).get(key)
        if not isinstance(metric, dict):
            results[key] = {"metric": key, "status": "verification_required", "reason": "metric_missing_from_catalog",
                            "detail": "indicatore assente dal catalogo controllato"}
            continue
        results[key] = probe_metric(key, metric, spec, cached)
    return results


REASONS = {
    "match": "periodo e valori coincidono con la fonte",
    "new_period": "la fonte pubblica un periodo più recente",
    "source_unreachable": "fonte non scaricabile",
    "structure_changed": "struttura del file cambiata",
    "same_period_values_differ": "stesso periodo ma valori diversi da quelli pubblicati",
    "history_revised": "la fonte ha rivisto valori già pubblicati",
    "published_period_missing_at_source": "il periodo pubblicato non compare più alla fonte",
    "metric_missing_from_catalog": "indicatore assente dal catalogo",
}


def report_lines(results: dict[str, dict[str, Any]], coverage: dict[str, Any]) -> list[str]:
    covered = sum(1 for v in coverage.get("metrics", {}).values() if "probe" in v)
    total = len(coverage.get("metrics", {}))
    lines = ["", "### Verifica dei periodi alla fonte", "",
             f"Indicatori con verifica del periodo: **{covered}/{total}**. Gli altri entrano nei lotti successivi del controllo completo.", "",
             "| Indicatore | Pubblicato | Alla fonte | Esito | Motivo |", "|---|---|---|---|---|"]
    for key, item in sorted(results.items()):
        lines.append(f"| `{key}` | {item.get('publishedPeriod') or 'n.d.'} | {item.get('observedLatestPeriod') or 'n.d.'} | "
                     f"`{item.get('status')}` | {REASONS.get(str(item.get('reason')), item.get('reason') or '')} |")
    actions = [item["manualAction"] for item in results.values() if item.get("manualAction")]
    lines += ["", "### Azioni manuali", ""]
    if not actions:
        lines.append("Nessuna: tutte le fonti verificate sono state scaricate automaticamente.")
    for index, action in enumerate(actions, 1):
        lines.append(f"{index}. **`{action['metric']}`** — {REASONS.get(action['reason'], action['reason'])}: {action['detail']}")
        lines.extend(f"   - {step}" for step in action["steps"])
    differing = {k: v for k, v in results.items() if v.get("differences")}
    if differing:
        lines += ["", "### Valori diversi nello stesso periodo", ""]
        for key, item in sorted(differing.items()):
            sample = ", ".join(f"{d['geography']} {d['period']}: {d['published']} → {d['observed']}" for d in item["differences"][:7])
            lines.append(f"- `{key}`: {sample}.")
    revised = {k: v for k, v in results.items() if v.get("historyRevisionCount")}
    if revised:
        lines += ["", "### Revisioni dello storico", ""]
        for key, item in sorted(revised.items()):
            sample = ", ".join(f"{r['geography']} {r['period']}: {r['published']} → {r['observed']}" for r in item["historyRevisions"][:5])
            lines.append(f"- `{key}`: {item['historyRevisionCount']} valori rivisti ({sample}).")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--catalog", type=Path, required=True, help="Catalogo effettivo (dist/data/site-data.json)")
    parser.add_argument("--metric", help="Un solo indicatore")
    parser.add_argument("--file", type=Path, action="append", help="File della fonte scaricato a mano (ripetibile)")
    parser.add_argument("--json-out", type=Path, help="Esiti completi in JSON")
    parser.add_argument("--report-md", type=Path, help="Resoconto in Markdown")
    args = parser.parse_args()
    data = json.loads(args.catalog.read_text(encoding="utf-8"))
    CATALOG.update(data)
    coverage = load_coverage()
    if args.metric:
        spec = coverage["metrics"].get(args.metric, {})
        if "probe" not in spec:
            raise SystemExit(f"{args.metric}: nessuna verifica di periodo definita (lotto {spec.get('pendingLot', '?')})")
        result = probe_metric(args.metric, data["metrics"][args.metric], spec, local_file=args.file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] != "verification_required" or result.get("reason") != "source_unreachable" else 2
    results = run_all(data, coverage)
    lines = report_lines(results, coverage)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.report_md:
        args.report_md.parent.mkdir(parents=True, exist_ok=True)
        args.report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
