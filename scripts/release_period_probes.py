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
        except Exception as exc:  # rete, timeout, HTTP
            errors.append(f"tentativo {attempt}: {type(exc).__name__}: {exc}")
            if attempt < attempts:
                time.sleep(10 * attempt)
    raise ProbeError("source_unreachable", f"{attempts} tentativi da {int(timeout)} secondi falliti; " + " | ".join(errors[-2:]))


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


def compare_ars(metric: dict[str, Any], spec: dict[str, Any], payload: bytes) -> dict[str, Any]:
    source = ars_rows(payload, spec)
    published, current, history = published_points(metric)
    town_periods = [{p for (c, p) in source if c == code} for code in TOWN_CODES]
    if any(not periods for periods in town_periods):
        missing = [c for c, periods in zip(TOWN_CODES, town_periods) if not periods]
        raise ProbeError("structure_changed", f"l'export ARS non contiene i Comuni {missing}")
    common = set.intersection(*town_periods)
    latest = max(common, key=period_key)
    result: dict[str, Any] = {
        "publishedPeriod": published,
        "observedLatestPeriod": latest,
        "contentSha256": zip_members_sha(payload),
        "contentHashMode": "zip-members",
        "coverage": f"{sum(1 for p in town_periods if latest in p)}/7",
    }
    differences = []
    if published in common:
        for code, value in sorted(current.items()):
            observed = source.get((code, published))
            if observed is None or abs(round(observed + 1e-12, 2) - value) > TOLERANCE:
                differences.append({"geography": code, "period": published, "published": value, "observed": observed})
    revisions = []
    for (code, period), value in sorted(history.items()):
        observed = source.get((code, period))
        if observed is not None and abs(round(observed + 1e-12, 2) - value) > TOLERANCE:
            revisions.append({"geography": code, "period": period, "published": value, "observed": round(observed + 1e-12, 2)})
    result["valuesMatchPublished"] = not differences
    result["historyRevisions"] = revisions[:20]
    result["historyRevisionCount"] = len(revisions)
    if published not in common and period_key(latest) < period_key(published):
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


def manual_action(metric_key: str, spec: dict[str, Any], error: ProbeError) -> dict[str, Any]:
    url = ARS_EXPORT.format(id=spec["indicatorId"])
    return {
        "metric": metric_key,
        "reason": error.reason,
        "detail": error.detail,
        "url": url,
        "steps": [
            f"Aprire {url} da un browser: il download può richiedere oltre due minuti.",
            f"Salvare lo ZIP così come arriva (es. `{spec['indicatorId']}-dati_indicatori.zip`), senza aprirlo né rinominarlo.",
            "Allegarlo alla conversazione con Claude oppure caricarlo nella PR del controllo mensile.",
            f"Chiudere il controllo con: `python scripts/release_period_probes.py --catalog dist/data/site-data.json --metric {metric_key} --file <percorso dello ZIP>`.",
        ],
    }


def probe_metric(metric_key: str, metric: dict[str, Any], spec: dict[str, Any], fetch: Fetcher = http_fetch,
                 local_file: Path | None = None) -> dict[str, Any]:
    if spec.get("probe") != "ars_export":
        raise ValueError(f"probe non supportato: {spec.get('probe')}")
    url = ARS_EXPORT.format(id=spec["indicatorId"])
    try:
        payload = local_file.read_bytes() if local_file else fetch(url)
        result = compare_ars(metric, spec, payload)
    except ProbeError as error:
        return {
            "metric": metric_key, "probe": spec["probe"], "url": url, "status": "verification_required",
            "publishedPeriod": norm_period(metric.get("meta", {}).get("year")),
            "reason": error.reason, "detail": error.detail, "manualAction": manual_action(metric_key, spec, error),
        }
    result.update(metric=metric_key, probe=spec["probe"], url=url, acquisition="manual_file" if local_file else "automatic")
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
    parser.add_argument("--file", type=Path, help="File della fonte scaricato a mano")
    args = parser.parse_args()
    data = json.loads(args.catalog.read_text(encoding="utf-8"))
    coverage = load_coverage()
    if args.metric:
        spec = coverage["metrics"].get(args.metric, {})
        if "probe" not in spec:
            raise SystemExit(f"{args.metric}: nessuna verifica di periodo definita (lotto {spec.get('pendingLot', '?')})")
        result = probe_metric(args.metric, data["metrics"][args.metric], spec, local_file=args.file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] != "verification_required" or result.get("reason") != "source_unreachable" else 2
    results = run_all(data, coverage)
    print("\n".join(report_lines(results, coverage)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
