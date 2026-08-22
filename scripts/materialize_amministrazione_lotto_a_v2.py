#!/usr/bin/env python3
"""Completa il Lotto A Amministrazione.

La v1 materializza dotazione, turnover ed età; questa estensione aggiunge:
- formazione del personale RGS 2024;
- servizi comunali online al massimo livello di disponibilità (Regione Toscana/Istat, ind18).
"""
from __future__ import annotations

import json
from pathlib import Path

import materialize_amministrazione_lotto_a as base

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
MONITOR_PATH = ROOT / "data" / "source-monitor-state.json"
TRAINING_SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "rgs-formazione-2024.json"
ONLINE_SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "regione-toscana-servizi-online-2018-2022.json"
APP_PART_PATH = ROOT / "assets" / "app-parts" / "03.txt"

TRAINING_KEY = "municipalStaffTraining"
ONLINE_KEY = "municipalOnlineServicesAdvanced"
RGS_TRAINING_URL = "https://contoannuale.rgs.mef.gov.it/web/sicosito/assenze-e-turnover/formazione-acc"
REGIONE_SOURCE_PAGE = "https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali"
PROFILE = base.PROFILE
REGIONE_PROFILE = "regione-toscana-indicatori-comunali"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pct(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def training_parts(raw: dict) -> list[dict]:
    return [
        {"label": "Media totale RGS", "selectorLabel": "Media totale RGS", "value": float(raw["meanTotalRgs"]), "unit": "decimal"},
        {"label": "Giornate complessive", "selectorLabel": "Giornate complessive", "value": int(raw["totalDays"]), "unit": "number"},
        {"label": "Media uomini RGS", "selectorLabel": "Media uomini", "value": float(raw["meanMen"]), "unit": "decimal"},
        {"label": "Media donne RGS", "selectorLabel": "Media donne", "value": float(raw["meanWomen"]), "unit": "decimal"},
    ]


def training_metric(site: dict, snapshot: dict) -> dict:
    order = [row["town"] for row in site["metrics"]["population"]["rows"]]
    rows = []
    for town in order:
        raw = snapshot["towns"][town]
        if int(raw["menDays"]) + int(raw["womenDays"]) != int(raw["totalDays"]):
            raise RuntimeError(f"{town}: giornate formazione per genere non riconciliate")
        expected_mean = (float(raw["meanMen"]) + float(raw["meanWomen"])) / 2
        if abs(float(raw["meanTotalRgs"]) - expected_mean) > 1e-9:
            raise RuntimeError(f"{town}: Media Totale RGS non riconciliata")
        parts = training_parts(raw)
        rows.append({
            **base.identity(site, town),
            "value": parts[0]["value"],
            "formatted": f"{parts[0]['value']:.2f}".replace(".", ","),
            "series": None,
            "normalized": None,
            "benchmarkValue": parts[0]["value"],
            "parts": parts,
        })

    aggregate_raw = snapshot["versilia"]
    if int(aggregate_raw["menDays"]) + int(aggregate_raw["womenDays"]) != int(aggregate_raw["totalDays"]):
        raise RuntimeError("Versilia: giornate formazione per genere non riconciliate")
    aggregate_parts = training_parts(aggregate_raw)

    return {
        "meta": {
            "key": TRAINING_KEY,
            "theme": "bilanci",
            "label": "Formazione del personale comunale",
            "shortLabel": "Formazione del personale",
            "description": (
                "Giornate di formazione rilevate dal Conto Annuale RGS. La lettura predefinita è la “Media Totale” "
                "pubblicata dalla fonte; il selettore mostra anche le giornate complessive e le medie per genere."
            ),
            "unit": "decimal",
            "year": "2024",
            "source": "RGS — Conto Annuale",
            "polarity": "neutral",
            "compositeType": "securityMeasures",
            "selectorLabel": "Lettura formazione",
            "searchTerms": [
                "formazione personale", "giorni formazione", "dipendenti comunali formazione",
                "media formazione", "aggiornamento personale", "conto annuale formazione",
            ],
        },
        "sourceUrl": RGS_TRAINING_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate_parts[0]["value"],
            "label": "Versilia · Media totale RGS",
            "note": (
                "Valori restituiti direttamente dall’API RGS selezionando insieme i sette Comuni della Versilia; "
                "non è la media semplice dei sette valori comunali."
            ),
            "parts": aggregate_parts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Valori ufficiali RGS — Conto Annuale",
            "formula": (
                "Nessuna formula applicata ai valori pubblicati. Nel payload 2024 la Media Totale RGS coincide, "
                "per tutti i sette Comuni e per la selezione congiunta, con (Media Uomini + Media Donne) / 2."
            ),
            "caveat": (
                "La Media Totale RGS non viene presentata come giornate complessive divise per il numero di dipendenti. "
                "Le giornate complessive sono disponibili come lettura separata. Un valore più alto non misura da solo "
                "la qualità, la pertinenza o l’efficacia della formazione."
            ),
            "coverage": "7/7",
            "history": (
                "RGS espone annualità dal 2008 al 2024 e documenta l’andamento storico delle giornate di formazione; "
                "questa prima materializzazione comunale usa il 2024 verificato 7/7."
            ),
        },
    }


def online_metric(site: dict, snapshot: dict) -> dict:
    order = [row["town"] for row in site["metrics"]["population"]["rows"]]
    rows = []
    current_values = []
    for town in order:
        raw = snapshot["towns"][town]
        value_2018 = float(raw["2018"])
        value_2022 = float(raw["2022"])
        current_values.append(value_2022)
        rows.append({
            **base.identity(site, town),
            "value": value_2022,
            "formatted": pct(value_2022),
            "series": {"years": [2018, 2022], "values": [value_2018, value_2022]},
            "normalized": None,
            "benchmarkValue": value_2022,
        })

    return {
        "meta": {
            "key": ONLINE_KEY,
            "theme": "bilanci",
            "label": "Servizi comunali online al massimo livello di disponibilità",
            "shortLabel": "Servizi online · livello massimo",
            "description": (
                "Percentuale dei servizi offerti online dal Comune ai livelli più avanzati della classificazione Istat. "
                "Il metadato regionale include i livelli 3 e 4: invio telematico della modulistica e, al livello 4, "
                "completamento dell'intero procedimento online incluso l'eventuale pagamento."
            ),
            "unit": "percent",
            "year": "2022",
            "source": "Regione Toscana / Istat — ICT nelle PA locali",
            "polarity": "neutral",
            "searchTerms": [
                "servizi online", "servizi digitali comune", "digitalizzazione comune", "servizi telematici",
                "ict pubblica amministrazione", "procedimenti online", "servizi comunali digitali",
            ],
        },
        "sourceUrl": REGIONE_SOURCE_PAGE,
        "rows": rows,
        "aggregate": {
            "value": sum(current_values) / len(current_values),
            "label": "Versilia · media comunale servizi online avanzati",
            "note": (
                "Media aritmetica dei sette valori comunali 2022. Non è una media ponderata per numero di servizi, "
                "perché la fonte pubblica non espone i denominatori comunali dell'indicatore."
            ),
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Indicatore ufficiale Regione Toscana / Istat, codice ind18",
            "formula": (
                "Percentuale di servizi offerti online al massimo livello di disponibilità dai Comuni; "
                "il metadato regionale specifica livelli 3 e 4 della rilevazione Istat ICT nelle PA locali."
            ),
            "caveat": (
                "Il dato corrente è il definitivo al 31/12/2022. Il file regionale Indicatori 2024 lo ripropone "
                "invariato e non viene trattato come dato 2024. Il confronto 2018–2022 è informativo ma non perfettamente "
                "omogeneo: il paniere Istat è passato da 24 servizi osservati nel 2018 a 27 nel 2022. "
                "Una quota maggiore descrive una più ampia disponibilità online avanzata, ma non misura da sola qualità, "
                "usabilità o tempi dei servizi."
            ),
            "coverage": "7/7",
            "history": "Due rilevazioni effettive: 2018 e 2022. Nessun carry-forward artificiale negli anni intermedi.",
        },
    }


def update_theme(site: dict) -> None:
    theme = site["themes"]["bilanci"]
    theme["description"] = "Bilanci comunali, capacità di spesa, struttura del personale e digitalizzazione dei servizi."
    for key in (TRAINING_KEY, ONLINE_KEY):
        theme["metrics"] = [item for item in theme.get("metrics", []) if item != key]
        theme["metrics"].append(key)
    section = next(section for section in theme["sections"] if section["key"] == "personale-amministrazione")
    for key in (TRAINING_KEY, ONLINE_KEY):
        section["metrics"] = [item for item in section.get("metrics", []) if item != key]
        section["metrics"].append(key)
    section["description"] = (
        "Dotazione di personale, ricambio dell'organico, sostenibilità generazionale, formazione e disponibilità online dei servizi."
    )


def update_registry(registry: dict, site: dict) -> None:
    registry.setdefault("metricOverrides", {})[TRAINING_KEY] = {"profile": PROFILE}
    registry.setdefault("sourceProfileByUrl", {})[RGS_TRAINING_URL] = PROFILE
    registry.setdefault("sourceProfiles", {})[REGIONE_PROFILE] = {
        "publisher": "Regione Toscana — Ufficio regionale di Statistica / Istat",
        "frequency": "annual",
        "frequencyLabel": "Aggiornamento annuale della batteria regionale",
        "expectedRelease": (
            "La batteria regionale è aggiornata annualmente; ind18 cambia quando è disponibile una nuova rilevazione Istat ICT nelle PA locali."
        ),
        "acquisitionMethod": (
            "CSV ufficiali Regione Toscana a livello comunale; valori ind18 verificati 7/7 e conservati in snapshot versionato."
        ),
        "licenseName": "Open data / condizioni Regione Toscana",
        "licenseUrl": "https://www.regione.toscana.it/open-data",
    }
    registry.setdefault("metricOverrides", {})[ONLINE_KEY] = {"profile": REGIONE_PROFILE}
    registry.setdefault("sourceProfileByUrl", {})[REGIONE_SOURCE_PAGE] = REGIONE_PROFILE
    external = sum(
        1 for metric in site["metrics"].values()
        if metric.get("dataStorage", {}).get("type") == "external-climate"
    )
    registry["expectedMetricCount"] = len(site["metrics"])
    registry["expectedExternalMetricCount"] = external
    registry["expectedInlineMetricCount"] = len(site["metrics"]) - external


def ensure_monitor_state(sources: dict, url: str, profile: str, key: str) -> None:
    state = sources.setdefault(url, {
        "url": url,
        "ok": True,
        "status": 200,
        "finalUrl": url,
        "contentType": "text/html",
        "contentLength": None,
        "etag": "",
        "lastModified": "",
        "contentSha256": "",
        "hashTruncated": False,
        "error": "",
        "metrics": [],
        "roles": ["primary"],
        "profileIds": [profile],
        "frequencies": ["annual"],
    })
    state["metrics"] = sorted(set(state.get("metrics", [])) | {key})
    state["profileIds"] = sorted(set(state.get("profileIds", [])) | {profile})
    state["frequencies"] = sorted(set(state.get("frequencies", [])) | {"annual"})


def update_monitor(monitor: dict) -> None:
    sources = monitor.setdefault("sources", {})
    ensure_monitor_state(sources, RGS_TRAINING_URL, PROFILE, TRAINING_KEY)
    ensure_monitor_state(sources, REGIONE_SOURCE_PAGE, REGIONE_PROFILE, ONLINE_KEY)


def patch_frontend() -> None:
    """Aggiunge i conteggi età senza rompere le semantiche Redditi già applicate."""
    text = APP_PART_PATH.read_text(encoding="utf-8")
    marker = "const showStaffCounts = metric.meta.key === 'municipalStaffAgeStructure';"
    if marker in text:
        return

    original = '''    if (metric.meta.compositeType === 'securityMeasures') {
      return `<div class="composite-town-mobility">${parts.map((part,index)=>`<article class="${index===0?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.year)}</small></article>`).join('')}</div>`;
    }'''
    after_income = '''    if (metric.meta.compositeType === 'securityMeasures') {
      const incomeSources = metric.meta.key === 'incomeSourceProfile';
      return `<div class="composite-town-mobility">${parts.map((part,index)=>`<article class="${index===0?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,part.unit || metric.meta.unit))}</strong><small>${incomeSources ? (part.count === null || part.count === undefined ? 'n.d. · dichiaranti con questa fonte' : `${html(number0.format(part.count))} dichiaranti con questa fonte`) : html(metric.meta.year)}</small></article>`).join('')}</div>`;
    }'''
    patched = '''    if (metric.meta.compositeType === 'securityMeasures') {
      const incomeSources = metric.meta.key === 'incomeSourceProfile';
      const totalCount = parts.reduce((sum, part) => sum + (Number(part.count) || 0), 0);
      const showStaffCounts = metric.meta.key === 'municipalStaffAgeStructure';
      return `<div class="composite-town-mobility">${parts.map((part,index)=>`<article class="${index===0?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,part.unit || metric.meta.unit))}</strong><small>${incomeSources ? (part.count === null || part.count === undefined ? 'n.d. · dichiaranti con questa fonte' : `${html(number0.format(part.count))} dichiaranti con questa fonte`) : (showStaffCounts && part.count !== undefined ? `${html(number0.format(part.count))} dipendenti su ${html(number0.format(totalCount))} · ${html(metric.meta.year)}` : html(metric.meta.year))}</small></article>`).join('')}</div>`;
    }'''

    for old in (after_income, original):
        if old in text:
            APP_PART_PATH.write_text(text.replace(old, patched, 1), encoding="utf-8")
            return
    raise RuntimeError("Blocco frontend securityMeasures non trovato: patch Amministrazione non applicabile")


def main() -> None:
    base.patch_frontend = lambda: None
    base.main()
    patch_frontend()

    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    monitor = load(MONITOR_PATH)
    training_snapshot = load(TRAINING_SNAPSHOT_PATH)
    online_snapshot = load(ONLINE_SNAPSHOT_PATH)

    site["metrics"].pop(TRAINING_KEY, None)
    site["metrics"][TRAINING_KEY] = training_metric(site, training_snapshot)
    site["metrics"].pop(ONLINE_KEY, None)
    site["metrics"][ONLINE_KEY] = online_metric(site, online_snapshot)
    update_theme(site)
    update_registry(registry, site)
    update_monitor(monitor)

    if len(site["metrics"]) != 138:
        raise RuntimeError(f"Conteggio inatteso dopo Amministrazione: {len(site['metrics'])}")

    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    save(MONITOR_PATH, monitor)
    print("Amministrazione Lotto A v2: 138 indicatori totali; formazione RGS 2024 e servizi online Regione Toscana/Istat 2022 materializzati 7/7.")


if __name__ == "__main__":
    main()
