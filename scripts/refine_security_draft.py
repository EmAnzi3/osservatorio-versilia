#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "sicurezza-territorio-draft-2026-08.json"
APP03 = ROOT / "assets" / "app-parts" / "03.txt"
APP05 = ROOT / "assets" / "app-parts" / "05.txt"
APPLY = ROOT / "scripts" / "apply_security_draft.py"
TEST_COMPOSITES = ROOT / "scripts" / "test_composite_indicators.py"
TEST_ACCORDION = ROOT / "scripts" / "test_accordion_no_overlap.py"
TEST_PERCORSI = ROOT / "scripts" / "test_percorsi_draft.py"
TEST_REFINEMENTS = ROOT / "scripts" / "test_percorsi_refinements.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scalar_fines(data: dict, snapshot: dict) -> dict:
    current = data["metrics"]["roadFinesPerResident"]
    existing_rows = {row["town"]: row for row in current["rows"]}
    rows = []
    values = []
    for town, raw in snapshot["towns"].items():
        previous = existing_rows[town]
        value = raw["roadFinesPerResident"]["values"][-1]
        values.append(float(value))
        rows.append({
            "town": town,
            "code": previous["code"],
            "slug": previous["slug"],
            "value": value,
            "formatted": "",
            "series": raw["roadFinesPerResident"],
            "normalized": None,
            "benchmarkValue": value,
        })

    meta = dict(current["meta"])
    meta.pop("compositeType", None)
    meta.pop("selectorLabel", None)
    meta.update({
        "label": "Proventi rendicontati da sanzioni al Codice della strada per abitante",
        "shortLabel": "Proventi da sanzioni",
        "description": (
            "Proventi complessivi rendicontati per violazioni al Codice della strada, "
            "rapportati alla popolazione residente media. Il dato non misura il numero "
            "di verbali né, da solo, il livello di sicurezza o l’intensità dei controlli."
        ),
        "unit": "currency",
        "polarity": "neutral",
        "searchTerms": ["multe", "sanzioni", "codice della strada", "proventi"],
    })
    if meta.get("benchmark"):
        meta["benchmark"]["note"] = "Benchmark riferito ai proventi complessivi rendicontati per abitante."

    return {
        "meta": meta,
        "sourceUrl": current["sourceUrl"],
        "rows": rows,
        "aggregate": {
            "value": statistics.fmean(values),
            "label": "Media semplice dei 7 comuni",
            "note": (
                "Ogni Comune pesa allo stesso modo. Il valore descrive proventi rendicontati "
                "e non costituisce una graduatoria di sicurezza o di efficacia dei controlli."
            ),
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Dato ufficiale Istat / DAIT",
            "formula": "Proventi complessivi rendicontati per violazioni al Codice della strada / popolazione residente media.",
            "caveat": (
                "Il confronto risente di turismo, traffico di attraversamento, intensità e tipologia dei controlli, "
                "modalità di accertamento, riscossione e rendicontazione. La quota dei proventi attribuita ai limiti "
                "di velocità non viene pubblicata dall’Osservatorio perché il campo DAIT può risultare pari a zero "
                "anche in presenza di sanzioni per eccesso di velocità e rischia quindi di essere interpretato in modo improprio."
            ),
            "coverage": "7/7",
        },
    }


def update_data() -> None:
    data = load(DATA)
    snapshot = load(SNAPSHOT)
    data["metrics"]["roadFinesPerResident"] = scalar_fines(data, snapshot)
    theme = data["themes"]["sicurezza"]
    theme["question"] = "Quanto è sicuro il territorio e quali risorse vengono dedicate alla sicurezza?"
    theme["description"] = (
        "Sicurezza stradale e risorse comunali dedicate alla sicurezza e al controllo della circolazione, "
        "mantenendo la criminalità come contesto sovracomunale."
    )
    security_draft = data.setdefault("securityDraft", {})
    security_draft.pop("localPolice", None)
    security_draft["localPoliceResearch"] = {
        "status": "not-published",
        "reason": (
            "Verificate Regione Toscana, RGS-SICO/Conto annuale e le sezioni Personale/PIAO/Amministrazione trasparente "
            "dei sette Comuni. Le fonti reperibili non consentono ancora una fotografia 2025 omogenea almeno 6/7 del personale "
            "di Polizia Locale; i dati parziali non vengono mescolati né stimati."
        ),
        "publicationRule": "Pubblicare solo con definizione temporale e perimetro del personale omogenei, copertura 7/7 o 6/7 con n.d. esplicito.",
    }
    save(DATA, data)

    snapshot.setdefault("publicationPolicy", {})["speedFineShare"] = {
        "published": False,
        "reason": (
            "Campo DAIT contabilmente specifico: valori pari a zero non equivalgono necessariamente ad assenza di sanzioni "
            "per eccesso di velocità. Escluso dalla pubblicazione per evitare un’interpretazione causale non supportata."
        ),
    }
    snapshot["publicationPolicy"]["localPolice2025"] = {
        "published": False,
        "reason": (
            "Le tavole regionali sono aggregate e la ricognizione di PIAO, Conto annuale e Amministrazione trasparente comunali "
            "non produce ancora una base 2025 omogenea almeno 6/7."
        ),
    }
    save(SNAPSHOT, snapshot)


def update_app() -> None:
    app03 = APP03.read_text(encoding="utf-8")
    app03 = app03.replace("localPoliceDraftMarkup(data) + crimeMarkup(data)", "crimeMarkup(data)")
    APP03.write_text(app03, encoding="utf-8")

    app05 = APP05.read_text(encoding="utf-8")
    app05, count = re.subn(
        r"\n  function localPoliceDraftMarkup\(data\) \{.*?\n  \}\n\n(?=  function crimeMarkup\(data\) \{)",
        "\n",
        app05,
        count=1,
        flags=re.S,
    )
    if count not in (0, 1):
        raise RuntimeError("Rimozione localPoliceDraftMarkup ambigua")
    APP05.write_text(app05, encoding="utf-8")


def update_apply_script() -> None:
    text = APPLY.read_text(encoding="utf-8")
    new_build_fines = '''def build_fines(snapshot: dict) -> dict:\n    rows, values = [], []\n    for town, raw in snapshot["towns"].items():\n        value = raw["roadFinesPerResident"]["values"][-1]\n        values.append(float(value))\n        rows.append({\n            "town": town, "code": raw["code"],\n            "slug": town.lower().replace(" ", "-").replace("à", "a"),\n            "value": value, "formatted": "", "series": raw["roadFinesPerResident"],\n            "normalized": None, "benchmarkValue": value,\n        })\n    benchmark = snapshot["benchmarks"]["roadFinesPerResident"]\n    return {\n        "meta": {\n            "key": "roadFinesPerResident", "theme": "sicurezza",\n            "label": "Proventi rendicontati da sanzioni al Codice della strada per abitante",\n            "shortLabel": "Proventi da sanzioni",\n            "description": "Proventi complessivi rendicontati per violazioni al Codice della strada, rapportati alla popolazione residente media. Il dato non misura il numero di verbali né, da solo, il livello di sicurezza o l’intensità dei controlli.",\n            "unit": "currency", "year": "2024",\n            "source": "Istat / Ministero dell’Interno — A misura di Comune",\n            "polarity": "neutral",\n            "searchTerms": ["multe", "sanzioni", "codice della strada", "proventi"],\n            "benchmark": {\n                "year": 2024, "tuscany": benchmark["tuscany"], "italy": benchmark["italy"],\n                "source": "Istat / Ministero dell’Interno", "url": snapshot["sources"]["istat15c"]["url"],\n                "note": "Benchmark riferito ai proventi complessivi rendicontati per abitante.",\n            },\n        },\n        "sourceUrl": snapshot["sources"]["istat15c"]["url"], "rows": rows,\n        "aggregate": {\n            "value": mean(values), "label": "Media semplice dei 7 comuni",\n            "note": "Ogni Comune pesa allo stesso modo. Il valore descrive proventi rendicontati e non costituisce una graduatoria di sicurezza o di efficacia dei controlli.",\n        },\n        "normalizedAggregate": None,\n        "method": {\n            "type": "Dato ufficiale Istat / DAIT",\n            "formula": "Proventi complessivi rendicontati per violazioni al Codice della strada / popolazione residente media.",\n            "caveat": "Il confronto risente di turismo, traffico di attraversamento, intensità e tipologia dei controlli, modalità di accertamento, riscossione e rendicontazione. La quota dei proventi attribuita ai limiti di velocità non viene pubblicata perché il campo DAIT può risultare pari a zero anche in presenza di sanzioni per eccesso di velocità.",\n            "coverage": "7/7",\n        },\n    }\n\n\n'''
    text, count = re.subn(
        r"def build_fines\(snapshot: dict\) -> dict:.*?(?=def build_mission\(data: dict\) -> dict:)",
        new_build_fines,
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("build_fines non sostituita")

    text = text.replace(
        '        "question": "Quanto è sicuro il territorio e quali risorse vengono dedicate al presidio?",\n        "description": "Sicurezza stradale, risorse comunali e controllo della circolazione, mantenendo criminalità e Polizia Locale alla scala realmente disponibile.",',
        '        "question": "Quanto è sicuro il territorio e quali risorse vengono dedicate alla sicurezza?",\n        "description": "Sicurezza stradale e risorse comunali dedicate alla sicurezza e al controllo della circolazione, mantenendo la criminalità come contesto sovracomunale.",',
    )

    text, count = re.subn(
        r'    local = snapshot\["sources"\]\["localPolice2025"\]\n    data\["securityDraft"\] = \{.*?\n    \}\n(?=    save\(DATA_PATH, data\))',
        '    data["securityDraft"] = {\n        "status": "draft", "mission03Status": mission_status,\n        "localPoliceResearch": {\n            "status": "not-published",\n            "reason": "Regione Toscana, RGS-SICO/Conto annuale e Amministrazione trasparente dei sette Comuni non consentono ancora una fotografia 2025 omogenea almeno 6/7; nessun valore viene stimato o mescolato tra annualità/perimetri diversi.",\n        },\n    }\n',
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("securityDraft non aggiornato")

    marker = "    return app\n\n\ndef patch_app05(app: str) -> str:"
    if marker in text and 'app = app.replace("localPoliceDraftMarkup(data) + crimeMarkup(data)", "crimeMarkup(data)")' not in text:
        text = text.replace(
            marker,
            '    app = app.replace("localPoliceDraftMarkup(data) + crimeMarkup(data)", "crimeMarkup(data)")\n    return app\n\n\ndef patch_app05(app: str) -> str:',
            1,
        )

    text, count = re.subn(
        r'def patch_app05\(app: str\) -> str:.*?(?=def update_data_and_registry\(data: dict, snapshot: dict\) -> None:)',
        'def patch_app05(app: str) -> str:\n    return re.sub(r"\\n  function localPoliceDraftMarkup\\(data\\) \\{.*?\\n  \\}\\n\\n(?=  function crimeMarkup\\(data\\) \\{)", "\\n", app, count=1, flags=re.S)\n\n\n',
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("patch_app05 non aggiornata")
    APPLY.write_text(text, encoding="utf-8")


def update_tests() -> None:
    text = TEST_COMPOSITES.read_text(encoding="utf-8")
    text = text.replace(', "roadSafety", "roadFinesPerResident"}', ', "roadSafety"}')
    text = text.replace(
        '    assert road_fines["meta"]["compositeType"] == "securityMeasures"\n    assert [part["unit"] for part in road_fines["rows"][0]["parts"]] == ["currency", "percent"]\n    assert all(len(row["parts"]) == 2 for row in road_fines["rows"])',
        '    assert road_fines["meta"]["unit"] == "currency"\n    assert "compositeType" not in road_fines["meta"]\n    assert all("parts" not in row and "componentSeries" not in row for row in road_fines["rows"])\n    assert road_fines["method"]["coverage"] == "7/7"\n    assert registry_map[road_fines["sourceUrl"]]',
    )
    text = text.replace(
        'for metric_key, option_count in (("roadSafety", 4), ("roadFinesPerResident", 2)):',
        'for metric_key, option_count in (("roadSafety", 4),):',
    )
    TEST_COMPOSITES.write_text(text, encoding="utf-8")

    text = TEST_ACCORDION.read_text(encoding="utf-8")
    text = re.sub(
        r'        local_police = page\.locator\("#polizia-locale"\)\n        require\(local_police\.count\(\) == 1 and local_police\.is_visible\(\),\n                "Il contesto Polizia Locale deve vivere nel tema Sicurezza e territorio"\)\n        require\(not overlaps\(crime\.bounding_box\(\), local_police\.bounding_box\(\)\),\n                "I blocchi Criminalità e Polizia Locale non devono sovrapporsi"\)\n',
        '        require(page.locator("#polizia-locale").count() == 0,\n                "Il dato regionale Polizia Locale non deve essere esposto come contesto comunale")\n',
        text,
    )
    TEST_ACCORDION.write_text(text, encoding="utf-8")

    text = TEST_PERCORSI.read_text(encoding="utf-8")
    text = text.replace(
        '    require("themeKey === \'sicurezza\' ? localPoliceDraftMarkup(data) + crimeMarkup(data)" in bundle,\n            "Contesti Polizia Locale e criminalità non presenti nel tema Sicurezza")',
        '    require("themeKey === \'sicurezza\' ? crimeMarkup(data)" in bundle,\n            "Contesto criminalità non presente nel tema Sicurezza")\n    require("localPoliceDraftMarkup" not in bundle,\n            "Il contesto regionale Polizia Locale non deve essere pubblicato")',
    )
    text = text.replace(
        '        require(page.locator("#polizia-locale").count() == 1,\n                "Contesto Polizia Locale non presente nel nuovo tema Sicurezza")',
        '        require(page.locator("#polizia-locale").count() == 0,\n                "Contesto regionale Polizia Locale ancora pubblicato")',
    )
    TEST_PERCORSI.write_text(text, encoding="utf-8")

    text = TEST_REFINEMENTS.read_text(encoding="utf-8")
    old_order = '''          return [\n            nodes.indexOf(document.querySelector('#compare-benchmark')),\n            nodes.indexOf(document.querySelector('#polizia-locale')),\n            nodes.indexOf(document.querySelector('#criminalita')),\n            nodes.indexOf(document.querySelector('#compare-tools'))\n          ];'''
    new_order = '''          return [\n            nodes.indexOf(document.querySelector('#compare-benchmark')),\n            nodes.indexOf(document.querySelector('#criminalita')),\n            nodes.indexOf(document.querySelector('#compare-tools'))\n          ];'''
    text = text.replace(old_order, new_order)
    text = text.replace(
        '        require(order[0] >= 0 and order[0] < order[1] < order[2] < order[3],\n                f"Ordine benchmark/Polizia Locale/criminalità/metodo errato: {order}")',
        '        require(order[0] >= 0 and order[0] < order[1] < order[2],\n                f"Ordine benchmark/criminalità/metodo errato: {order}")',
    )
    text = text.replace(
        "        local_police = page.locator('#polizia-locale')\n        require(crime.count() == 1 and crime.is_visible(),\n                \"Criminalità e delitti denunciati non visibile su mobile\")\n        require(local_police.count() == 1 and local_police.is_visible(),\n                \"Contesto Polizia Locale non visibile su mobile\")\n        require_box_inside_viewport(page, '#criminalita', \"box Criminalità e delitti denunciati\")\n        require_box_inside_viewport(page, '#polizia-locale', \"box Polizia Locale\")",
        "        require(crime.count() == 1 and crime.is_visible(),\n                \"Criminalità e delitti denunciati non visibile su mobile\")\n        require(page.locator('#polizia-locale').count() == 0,\n                \"Contesto regionale Polizia Locale ancora pubblicato su mobile\")\n        require_box_inside_viewport(page, '#criminalita', \"box Criminalità e delitti denunciati\")",
    )
    TEST_REFINEMENTS.write_text(text, encoding="utf-8")


def main() -> None:
    update_data()
    update_app()
    update_apply_script()
    update_tests()
    print("Correzione Sicurezza applicata: sanzioni scalari, quota velocità non pubblicata, contesto PL regionale rimosso.")


if __name__ == "__main__":
    main()
