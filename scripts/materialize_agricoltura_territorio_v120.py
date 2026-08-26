#!/usr/bin/env python3
"""Materializza il lotto Agricoltura e territorio v1.20.0 da snapshot Istat verificato."""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "istat-agricoltura-territorio-2020.json"
APP_PART_00 = ROOT / "assets" / "app-parts" / "00.txt"
APP_PART_03 = ROOT / "assets" / "app-parts" / "03.txt"
APP_JS = ROOT / "assets" / "app.js"
FINALIZER = ROOT / "scripts" / "finalize_catalog_release.py"
README = ROOT / "README.md"
HISTORY_DOC = ROOT / "docs" / "copertura-serie-storiche.md"
COHERENCE_DOC = ROOT / "docs" / "coerenza-interfaccia.md"
PAGES = ROOT / ".github" / "workflows" / "pages.yml"

VERSION = "v1.20.0"
UPDATED = "26 agosto 2026"
KEYS = (
    "agriculturalFarms",
    "agriculturalUsedArea",
    "averageAgriculturalFarmSize",
    "cropProfile",
    "irrigatedAgriculturalArea",
)
SOURCE_PAGE = "https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/"
SITUAS_URL = "https://situas.istat.it/"
SNAPSHOT_REF = "data/source-snapshots/istat-agricoltura-territorio-2020.json"
CROP_PARTS = (
    ("ARLAND", "Seminativi"),
    ("OLIVOOILTR", "Olivo da olio"),
    ("OLIVTTR", "Olive da tavola"),
    ("VINEY", "Vite"),
    ("PGRAPM", "Prati permanenti e pascoli"),
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Pattern non trovato in {path}: {old[:90]}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def validate_snapshot(snapshot: dict, site: dict) -> None:
    expected = {town["code"]: town["name"] for town in site["towns"]}
    raw = snapshot.get("towns", {})
    if set(raw) != set(expected):
        raise RuntimeError("Snapshot agricoltura: perimetro comunale diverso dai 7 Comuni canonici")
    for code, name in expected.items():
        if raw[code].get("name") != name:
            raise RuntimeError(f"Snapshot agricoltura: nome incoerente per {code}")
        for field in ("farms", "sauCenterHa", "farmsWithSau", "sauLocalizedHa", "municipalAreaKm2", "irrigatedAreaHa"):
            if raw[code].get(field) is None:
                raise RuntimeError(f"Snapshot agricoltura: {name} senza {field}")
    for crop, _ in CROP_PARTS:
        present = sum(raw[code]["cropsHa"].get(crop) is not None for code in expected)
        minimum = 4 if crop == "OLIVTTR" else 6
        if present < minimum:
            raise RuntimeError(f"Snapshot agricoltura: copertura {crop} {present}/7 sotto il minimo {minimum}/7")
    # Assenze ammesse e note prima della pubblicazione.
    if raw["046013"]["cropsHa"].get("VINEY") is not None:
        raise RuntimeError("Il gate si aspetta VINEY n.d. a Forte dei Marmi")


def meta(key: str, label: str, short: str, description: str, unit: str, keywords: list[str]) -> dict:
    return {
        "key": key,
        "theme": "ambiente",
        "label": label,
        "shortLabel": short,
        "description": description,
        "unit": unit,
        "year": "2020",
        "source": "Istat — 7° Censimento generale dell'agricoltura 2020",
        "update": "Censimento 2020 · coltivazioni riferite all'annata agraria 2019/2020",
        "freshness": "Ultima base censuaria comunale omogenea disponibile",
        "polarity": "neutral",
        "context": "Agricoltura e territorio",
        "keywords": keywords,
        "sortable": True,
        "periodType": "census",
        "detailGroup": "agricoltura",
        "sourceMeta": {
            "publisher": "Istat",
            "snapshot": SNAPSHOT_REF,
            "note": "Dati comunali ufficiali; nessuna stima dei valori mancanti.",
        },
    }


def build_metrics(site: dict, snapshot: dict) -> OrderedDict:
    raw = snapshot["towns"]
    towns = site["towns"]
    slug_by_code = {row["code"]: row["slug"] for row in site["metrics"]["population"]["rows"]}

    def item(town: dict) -> dict:
        return raw[town["code"]]

    farms_total = sum(item(t)["farms"] for t in towns)
    sau_center_total = sum(item(t)["sauCenterHa"] for t in towns)
    farms_sau_total = sum(item(t)["farmsWithSau"] for t in towns)
    sau_local_total = sum(item(t)["sauLocalizedHa"] for t in towns)
    area_total = sum(item(t)["municipalAreaKm2"] for t in towns)
    irrig_total = sum(item(t)["irrigatedAreaHa"] for t in towns)

    farms_meta = meta(
        KEYS[0], "Aziende agricole", "Aziende agricole",
        "Numero di aziende con centro aziendale nel Comune al Censimento agricolo 2020.",
        "number", ["agricoltura", "aziende agricole", "imprese agricole", "censimento agricoltura"],
    )
    farms = {
        "meta": farms_meta,
        "sourceUrl": SOURCE_PAGE,
        "rows": [{"town": t["name"], "code": t["code"], "slug": slug_by_code[t["code"]], "value": item(t)["farms"], "year": 2020} for t in towns],
        "aggregate": {"value": farms_total, "label": "Versilia · totale", "note": "Somma delle aziende con centro aziendale nei sette Comuni."},
        "method": {
            "type": "Dato censuario Istat",
            "formula": "Indicatore HO del dataflow DF_DCAT_CENSAGRIC2020_SURF_ALL, selezionato per i sette codici comunali.",
            "caveat": "Il Comune è attribuito in base al centro aziendale; i terreni dell'azienda possono trovarsi anche in altri Comuni.",
            "coverage": "7/7",
            "snapshot": SNAPSHOT_REF,
        },
    }

    sau_meta = meta(
        KEYS[1], "Superficie agricola utilizzata (SAU)", "SAU del territorio",
        "Superficie agricola utilizzata localizzata fisicamente nel territorio comunale. La lettura rapportata indica la quota della superficie comunale occupata da SAU.",
        "hectares", ["sau", "superficie agricola", "agricoltura", "territorio", "ettari"],
    )
    sau_meta["normalized"] = {
        "label": "Quota della superficie comunale occupata da SAU",
        "description": "SAU localizzata nel Comune divisa per la superficie comunale Istat-SITUAS al 31 dicembre 2020.",
        "unit": "percent",
    }
    sau_rows = []
    for t in towns:
        r = item(t)
        share = r["sauLocalizedHa"] / (r["municipalAreaKm2"] * 100) * 100
        sau_rows.append({
            "town": t["name"], "code": t["code"], "slug": slug_by_code[t["code"]], "value": r["sauLocalizedHa"], "year": 2020,
            "normalized": {"label": "Quota della superficie comunale occupata da SAU", "value": share, "unit": "percent", "year": 2020},
        })
    sau = {
        "meta": sau_meta,
        "sourceUrl": SOURCE_PAGE,
        "sourceUrls": {"agriculture": SOURCE_PAGE, "municipalArea": SITUAS_URL},
        "rows": sau_rows,
        "aggregate": {"value": sau_local_total, "label": "Versilia · SAU localizzata", "note": "Somma degli ettari di SAU localizzati nei sette Comuni."},
        "normalizedAggregate": {
            "value": sau_local_total / (area_total * 100) * 100,
            "label": "Versilia · quota di territorio in SAU",
            "note": "Rapporto tra SAU localizzata complessiva e superficie complessiva dei sette Comuni, entrambe sul perimetro territoriale 2020.",
        },
        "method": {
            "type": "Dato Istat + rapporto territoriale Osservatorio Versilia",
            "formula": "SAU territoriale: ARU/ALL del dataflow DF_DCAT_CENSAGRIC2020_UA_CROPS_2. Quota % = SAU localizzata (ha) / [superficie comunale SITUAS 31/12/2020 (km²) × 100] × 100.",
            "caveat": "Per evitare di attribuire al Comune terreni di aziende con centro altrove, la SAU usa la localizzazione dei terreni, non il centro aziendale. Il denominatore SITUAS è allineato al 2020.",
            "coverage": "7/7",
            "snapshot": SNAPSHOT_REF,
        },
    }

    avg_meta = meta(
        KEYS[2], "Dimensione media delle aziende agricole", "Dimensione media aziendale",
        "SAU delle aziende con centro nel Comune divisa per il numero di aziende con SAU.",
        "hectaresPerFarm", ["dimensione azienda", "ettari per azienda", "sau", "aziende con sau"],
    )
    avg = {
        "meta": avg_meta,
        "sourceUrl": SOURCE_PAGE,
        "rows": [{
            "town": t["name"], "code": t["code"], "slug": slug_by_code[t["code"]], "value": item(t)["sauCenterHa"] / item(t)["farmsWithSau"], "year": 2020,
        } for t in towns],
        "aggregate": {
            "value": sau_center_total / farms_sau_total,
            "label": "Versilia · dimensione media",
            "note": "Rapporto tra la somma della SAU delle aziende e la somma delle aziende con SAU; non media semplice delle medie comunali.",
        },
        "method": {
            "type": "Indicatore derivato da dati censuari Istat",
            "formula": "ARU / FUAA: SAU delle aziende con centro nel Comune divisa per aziende con SAU.",
            "caveat": "Il denominatore è il numero di aziende con SAU, non il totale delle aziende agricole.",
            "coverage": "7/7",
            "snapshot": SNAPSHOT_REF,
        },
    }

    crop_meta = meta(
        KEYS[3], "Profilo delle colture", "Profilo colture",
        "Superficie delle principali colture localizzata nel territorio comunale. Seleziona la coltura per confrontare gli ettari.",
        "hectares", ["colture", "seminativi", "olivo", "olive", "vite", "pascoli", "agricoltura"],
    )
    crop_meta["compositeType"] = "agricultureProfile"
    crop_meta["selectorLabel"] = "Coltura"
    crop_rows = []
    for t in towns:
        parts = []
        for crop, label in CROP_PARTS:
            parts.append({"key": crop, "label": label, "selectorLabel": label, "value": item(t)["cropsHa"].get(crop), "unit": "hectares"})
        crop_rows.append({"town": t["name"], "code": t["code"], "slug": slug_by_code[t["code"]], "value": item(t)["sauLocalizedHa"], "year": 2020, "parts": parts})
    aggregate_parts = []
    for crop, label in CROP_PARTS:
        values = [raw[code]["cropsHa"].get(crop) for code in raw]
        present = [v for v in values if v is not None]
        aggregate_parts.append({
            "key": crop, "label": label, "selectorLabel": label,
            "value": sum(present) if present else None,
            "availableValue": sum(present), "coverage": f"{len(present)}/7", "unit": "hectares",
        })
    crop = {
        "meta": crop_meta,
        "sourceUrl": SOURCE_PAGE,
        "rows": crop_rows,
        "aggregate": {
            "value": sau_local_total,
            "label": "Versilia · profilo colture",
            "parts": aggregate_parts,
            "note": "Il totale di ciascuna coltura è la somma dei Comuni con dato disponibile; la copertura è dichiarata e i Comuni senza riga restano n.d.",
        },
        "method": {
            "type": "Dato censuario Istat per localizzazione dei terreni",
            "formula": "ARU per TYPE_OF_CROP nel dataflow DF_DCAT_CENSAGRIC2020_UA_CROPS_2: ARLAND, OLIVOOILTR, OLIVTTR, VINEY, PGRAPM.",
            "caveat": "Una riga assente non è interpretata come zero. Vite: 6/7 (Forte dei Marmi n.d.). Olive da tavola: eccezione approvata 4/7; Forte dei Marmi, Stazzema e Viareggio restano n.d.",
            "coverage": "7/7 seminativi, olivo da olio e prati/pascoli; 6/7 vite; 4/7 olive da tavola (eccezione approvata)",
            "snapshot": SNAPSHOT_REF,
        },
    }

    irr_meta = meta(
        KEYS[4], "Superficie irrigata", "SAU irrigata",
        "Superficie irrigata almeno una volta nell'annata agraria 2019/2020 dalle aziende con centro nel Comune. La lettura rapportata indica la quota sulla SAU delle stesse aziende.",
        "hectares", ["irrigazione", "superficie irrigata", "sau irrigata", "acqua", "agricoltura"],
    )
    irr_meta["normalized"] = {
        "label": "Quota di SAU irrigata",
        "description": "Superficie irrigata divisa per la SAU delle aziende con centro nel Comune.",
        "unit": "percent",
    }
    irr = {
        "meta": irr_meta,
        "sourceUrl": SOURCE_PAGE,
        "rows": [{
            "town": t["name"], "code": t["code"], "slug": slug_by_code[t["code"]], "value": item(t)["irrigatedAreaHa"], "year": 2020,
            "normalized": {"label": "Quota di SAU irrigata", "value": item(t)["irrigatedAreaHa"] / item(t)["sauCenterHa"] * 100, "unit": "percent", "year": 2020},
        } for t in towns],
        "aggregate": {"value": irrig_total, "label": "Versilia · superficie irrigata", "note": "Somma degli ettari irrigati delle aziende con centro nei sette Comuni."},
        "normalizedAggregate": {
            "value": irrig_total / sau_center_total * 100,
            "label": "Versilia · quota di SAU irrigata",
            "note": "Rapporto tra superficie irrigata complessiva e SAU complessiva delle aziende con centro nei sette Comuni.",
        },
        "method": {
            "type": "Dato censuario Istat + rapporto derivato",
            "formula": "IA del dataflow DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS; quota % = IA / ARU del dataflow per centro aziendale.",
            "caveat": "Misura le superfici delle aziende attribuite per centro aziendale, non necessariamente gli ettari fisicamente localizzati nello stesso Comune.",
            "coverage": "7/7",
            "snapshot": SNAPSHOT_REF,
        },
    }

    return OrderedDict((k, v) for k, v in zip(KEYS, (farms, sau, avg, crop, irr)))


def apply_site(site: dict, snapshot: dict) -> None:
    validate_snapshot(snapshot, site)
    if "organicAgriculturalAreaShare" not in site["metrics"]:
        raise RuntimeError("Indicatore biologico canonico non trovato: evitare duplicazioni o sostituzioni")
    new_metrics = build_metrics(site, snapshot)
    rebuilt = OrderedDict()
    inserted = False
    for key, metric in site["metrics"].items():
        if key in KEYS:
            continue
        if key == "organicAgriculturalAreaShare" and not inserted:
            rebuilt.update(new_metrics)
            inserted = True
        rebuilt[key] = metric
    if not inserted:
        raise RuntimeError("Punto di inserimento agricoltura non trovato")
    site["metrics"] = rebuilt

    theme = site["themes"]["ambiente"]
    theme["description"] = "Clima, suolo, rifiuti, agricoltura e uso del territorio, coltivazioni biologiche ed esposizione concreta ai rischi idrogeologici."
    section = next((s for s in theme["sections"] if s.get("key") == "agricoltura"), None)
    if not section:
        raise RuntimeError("Sezione Ambiente/Agricoltura non trovata")
    section["label"] = "Agricoltura e territorio"
    section["description"] = "Aziende, SAU, dimensione aziendale, colture, irrigazione e diffusione del biologico, distinguendo centro aziendale e localizzazione dei terreni."
    section["metrics"] = [*KEYS, "organicAgriculturalAreaShare"]
    theme["metrics"] = [key for s in theme["sections"] for key in s["metrics"]]
    site["version"] = VERSION
    site["updated"] = UPDATED


def apply_registry(registry: dict) -> None:
    profile = "istat-agriculture-census-2020"
    registry["sourceProfiles"][profile] = {
        "publisher": "Istat",
        "frequency": "census_or_irregular",
        "frequencyLabel": "Censuaria o irregolare",
        "expectedRelease": "Quando Istat pubblica una nuova base comunale omogenea del Censimento/struttura agricola",
        "acquisitionMethod": "Interrogazione IstatData SDMX del 7° Censimento Agricoltura 2020; distinzione tra dati per centro aziendale e localizzazione dei terreni; superficie comunale SITUAS 31/12/2020 per la quota territoriale; nessuna stima dei valori mancanti.",
        "licenseName": "CC BY 4.0",
        "licenseUrl": "https://www.istat.it/note-legali/",
    }
    for url in (SOURCE_PAGE, SITUAS_URL):
        registry.setdefault("sourceProfileByUrl", {})[url] = profile
        registry.setdefault("sourceUrlProfiles", {})[url] = profile
    for key in KEYS:
        registry.setdefault("metricOverrides", {})[key] = {"profile": profile}
    registry["expectedMetricCount"] = 154
    registry["expectedInlineMetricCount"] = 150
    registry["expectedExternalMetricCount"] = 4


def patch_frontend() -> None:
    replace_once(APP_JS, "const VERSION='20260826-v119';", "const VERSION='20260826-v120';")
    replace_once(
        APP_PART_00,
        "    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],",
        "    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],\n    agriculturalFarms: ['aziende agricole', 'imprese agricole', 'censimento agricoltura'],\n    agriculturalUsedArea: ['sau', 'superficie agricola utilizzata', 'ettari agricoli'],\n    averageAgriculturalFarmSize: ['dimensione aziende agricole', 'ettari per azienda', 'azienda con sau'],\n    cropProfile: ['colture', 'seminativi', 'olivo', 'olive', 'vite', 'pascoli'],\n    irrigatedAgriculturalArea: ['irrigazione', 'superficie irrigata', 'sau irrigata'],",
    )
    replace_once(
        APP_PART_00,
        "      case 'hectares': return `${number2.format(v)} ha`;",
        "      case 'hectares': return `${number2.format(v)} ha`;\n      case 'hectaresPerFarm': return `${number2.format(v)} ha/azienda`;",
    )
    text = APP_PART_03.read_text(encoding="utf-8")
    text = text.replace("metric.meta.compositeType === 'securityMeasures'", "['securityMeasures','agricultureProfile'].includes(metric.meta.compositeType)")
    text = text.replace(
        "const selectableComposite = ['stock','mobility','omi','securityMeasures','demographicBreakdown'].includes(compositeType);",
        "const selectableComposite = ['stock','mobility','omi','securityMeasures','agricultureProfile','demographicBreakdown'].includes(compositeType);",
    )
    text = text.replace(
        ".sort((a,b)=>{const av=Number(a.displayValue),bv=Number(b.displayValue);return (Number.isFinite(bv)?bv:-Infinity)-(Number.isFinite(av)?av:-Infinity);});",
        ".sort((a,b)=>{const av=a.displayValue===null||a.displayValue===undefined?NaN:Number(a.displayValue),bv=b.displayValue===null||b.displayValue===undefined?NaN:Number(b.displayValue);return (Number.isFinite(bv)?bv:-Infinity)-(Number.isFinite(av)?av:-Infinity);});",
    )
    text = text.replace(
        "return { code:r.code, value:Number(r.parts?.[index]?.value) }; }",
        "const raw=r.parts?.[index]?.value; return { code:r.code, value:raw===null||raw===undefined?NaN:Number(raw) }; }",
    )
    APP_PART_03.write_text(text, encoding="utf-8")


def patch_release_files() -> None:
    # Finalizzatore canonico.
    text = FINALIZER.read_text(encoding="utf-8")
    text = text.replace("v1.19.0", "v1.20.0")
    text = text.replace("EXPECTED_METRICS = 149", "EXPECTED_METRICS = 154")
    text = text.replace("EXPECTED_INLINE = 145", "EXPECTED_INLINE = 150")
    FINALIZER.write_text(text, encoding="utf-8")

    text = README.read_text(encoding="utf-8")
    text = text.replace("Versione dati corrente: **v1.19.0** — 26 agosto 2026.", "Versione dati corrente: **v1.20.0** — 26 agosto 2026.")
    text = text.replace("149 indicatori nel catalogo canonico: 145 con valori incorporati e 4 climatici", "154 indicatori nel catalogo canonico: 150 con valori incorporati e 4 climatici")
    text = text.replace("`indicatori/`: 145 pagine canoniche", "`indicatori/`: 150 pagine canoniche")
    text = text.replace("catalogo canonico dei 149 indicatori, con dati incorporati per 145", "catalogo canonico dei 154 indicatori, con dati incorporati per 150")
    text = text.replace("metadati dei 149 indicatori", "metadati dei 154 indicatori")
    text = text.replace("valida tutti i 149 indicatori canonici, la ripartizione fra 145 valori incorporati", "valida tutti i 154 indicatori canonici, la ripartizione fra 150 valori incorporati")
    text = text.replace("ciascuno dei 145 indicatori incorporati", "ciascuno dei 150 indicatori incorporati")
    old_cov = "La copertura standard è **7/7 Comuni**. Un indicatore può essere pubblicato con copertura **6/7** soltanto quando un unico Comune presenta un dato ufficiale mancante o non validabile; il valore resta `n.d.` e non viene stimato o ricostruito."
    new_cov = old_cov + " Coperture inferiori richiedono un'eccezione esplicita, documentata nello snapshot e nei test: nella v1.20.0 l'unico caso è la sottodimensione “Olive da tavola” del Profilo colture, pubblicata 4/7 con gli altri tre Comuni indicati come `n.d.`."
    if new_cov not in text:
        text = text.replace(old_cov, new_cov)
    README.write_text(text, encoding="utf-8")

    history = HISTORY_DOC.read_text(encoding="utf-8")
    marker = "## Lotto Agricoltura e territorio v1.20.0"
    if marker not in history:
        history += "\n\n## Lotto Agricoltura e territorio v1.20.0\n\nIl 7° Censimento generale dell'Agricoltura Istat 2020 è usato come ultima base comunale censuaria omogenea. Aziende, dimensione media e irrigazione sono attribuite per centro aziendale; SAU territoriale e profilo colture usano invece il Comune di localizzazione dei terreni. La quota di SAU sulla superficie comunale usa come denominatore SITUAS al 31 dicembre 2020.\n\nLa copertura è 7/7 per aziende, SAU, dimensione media, irrigazione, seminativi, olivo da olio e prati/pascoli; 6/7 per la vite (Forte dei Marmi `n.d.`). La sola eccezione approvata è “Olive da tavola”, pubblicata 4/7: Forte dei Marmi, Stazzema e Viareggio restano `n.d.`. Nessuna assenza viene trasformata in zero.\n"
    HISTORY_DOC.write_text(history, encoding="utf-8")

    coherence = COHERENCE_DOC.read_text(encoding="utf-8")
    note = "\n### Selettori Agricoltura e territorio\n\nIl profilo colture riusa i controlli compositi canonici della pagina di confronto e delle schede comunali. SAU e superficie irrigata riusano il selettore assoluto/rapportato esistente. Non sono introdotte pagine, shell, colori o componenti paralleli. I valori `null` devono essere resi come `n.d.` e non possono essere classificati o ordinati come zeri reali.\n"
    if "### Selettori Agricoltura e territorio" not in coherence:
        coherence = coherence.replace("\n## Profili ed eccezioni esplicite", note + "\n## Profili ed eccezioni esplicite")
    COHERENCE_DOC.write_text(coherence, encoding="utf-8")

    pages = PAGES.read_text(encoding="utf-8")
    if "test_agricoltura_territorio_v120.py" not in pages:
        pages = pages.replace("          python scripts/test_mobilita_tpl_v119.py\n", "          python scripts/test_mobilita_tpl_v119.py\n          python scripts/test_agricoltura_territorio_v120.py\n")
        pages = pages.replace("          python -m json.tool data/source-snapshots/mobilita-tpl-2026-08-26.json > /dev/null\n", "          python -m json.tool data/source-snapshots/mobilita-tpl-2026-08-26.json > /dev/null\n          python -m json.tool data/source-snapshots/istat-agricoltura-territorio-2020.json > /dev/null\n")
        pages = pages.replace("            scripts/materialize_mobilita_tpl_v119.py \\\n            scripts/test_mobilita_tpl_v119.py \\", "            scripts/materialize_mobilita_tpl_v119.py \\\n            scripts/test_mobilita_tpl_v119.py \\\n            scripts/materialize_agricoltura_territorio_v120.py \\\n            scripts/test_agricoltura_territorio_v120.py \\")
    if "test_agricoltura_review_interactions_v120.py" not in pages:
        pages = pages.replace(
            "      - name: Validate PNRR Toscana town experience\n",
            "      - name: Validate Agricoltura e territorio interactions\n        run: python scripts/test_agricoltura_review_interactions_v120.py\n\n      - name: Validate PNRR Toscana town experience\n",
        )
        pages = pages.replace(
            "            scripts/test_agricoltura_territorio_v120.py \\\n",
            "            scripts/test_agricoltura_territorio_v120.py \\\n            scripts/test_agricoltura_review_interactions_v120.py \\\n",
        )
    PAGES.write_text(pages, encoding="utf-8")


def main() -> None:
    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    snapshot = load(SNAPSHOT_PATH)
    apply_site(site, snapshot)
    apply_registry(registry)
    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    patch_frontend()
    patch_release_files()
    print("Agricoltura e territorio v1.20.0 materializzata: 5 indicatori canonici; soglia 6/7 rispettata, con la sola eccezione approvata Olive da tavola 4/7.")


if __name__ == "__main__":
    main()
