#!/usr/bin/env python3
"""Promuove il lotto Welfare + prima infanzia dal collaudo alla release canonica v1.18.0.

Lo script è idempotente: materializza i tre indicatori, allinea catalogo, registry,
metadati di release e UI, quindi lascia i file pronti per commit/push dal workflow.
"""
from __future__ import annotations

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_SNAPSHOT = ROOT / "data" / "source-snapshots" / "welfare-prima-infanzia-draft-2026-08.json"
NEW_SNAPSHOT = ROOT / "data" / "source-snapshots" / "welfare-prima-infanzia-2026-08.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace(path: str, old: str, new: str, *, required: bool = True, count: int = 0) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old not in text:
        if required and new not in text:
            raise RuntimeError(f"{path}: marker non trovato: {old!r}")
        return
    text = text.replace(old, new, count) if count else text.replace(old, new)
    p.write_text(text, encoding="utf-8")


# 1) Materializza il catalogo sui dati verificati 7/7.
runpy.run_path(str(ROOT / "scripts" / "materialize_welfare_prima_infanzia_draft.py"), run_name="__main__")
site_path = ROOT / "data" / "site-data.json"
site = load(site_path)
site["version"] = "v1.18.0"
site["updated"] = "25 agosto 2026"
save(site_path, site)

# 2) Promuove lo snapshot da draft a snapshot di release, mantenendo i valori sorgente integri.
snapshot_path = OLD_SNAPSHOT if OLD_SNAPSHOT.exists() else NEW_SNAPSHOT
snapshot = load(snapshot_path)
snapshot["snapshotVersion"] = "2026-08-25-v1"
snapshot["status"] = "release-verified-7of7"
save(NEW_SNAPSHOT, snapshot)
if OLD_SNAPSHOT.exists() and OLD_SNAPSHOT != NEW_SNAPSHOT:
    OLD_SNAPSHOT.unlink()

for path in (
    "scripts/materialize_welfare_prima_infanzia_draft.py",
    "scripts/test_welfare_prima_infanzia_draft.py",
    ".github/workflows/welfare-draft.yml",
):
    replace(path, "welfare-prima-infanzia-draft-2026-08.json", "welfare-prima-infanzia-2026-08.json", required=False)
replace("scripts/test_welfare_prima_infanzia_draft.py", 'assert SNAP["status"] == "draft-verified-7of7"', 'assert SNAP["status"] == "release-verified-7of7"', required=False)
replace("scripts/test_welfare_prima_infanzia_draft.py", 'assert SITE["version"] == "1.18.0-draft"', 'assert SITE["version"] == "v1.18.0"', required=False)

# 3) UI: una distribuzione senza conteggi assoluti non deve mostrare "NaN residenti".
#    I conteggi restano visibili per le distribuzioni che li possiedono davvero.
ui_path = ROOT / "assets" / "app-parts" / "03.txt"
ui = ui_path.read_text(encoding="utf-8")
old_ui = '<div class="composite-town-detail">${parts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${html(number1.format(part.value))}%</b><small>${html(number0.format(part.count))} ${html(countLabel)}</small></div>`).join(\'\')}</div>${agePyramidDisclosure}'
new_ui = '<div class="composite-town-detail">${parts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${html(number1.format(part.value))}%</b>${part.count === null || part.count === undefined ? \'\' : `<small>${html(number0.format(part.count))} ${html(countLabel)}</small>`}</div>`).join(\'\')}</div>${agePyramidDisclosure}'
if old_ui in ui:
    ui = ui.replace(old_ui, new_ui, 1)
elif new_ui not in ui:
    raise RuntimeError("assets/app-parts/03.txt: renderer distribuzioni non riconosciuto")
ui_path.write_text(ui, encoding="utf-8")

# 4) Registry fonti: 146 totali = 142 inline + 4 climatici esterni.
registry_path = ROOT / "data" / "source-registry.json"
registry = load(registry_path)
registry["expectedMetricCount"] = 146
registry["expectedInlineMetricCount"] = 142
registry["expectedExternalMetricCount"] = 4
registry.setdefault("sourceProfiles", {})["istat-social-services-annual"] = {
    "publisher": "Istat",
    "frequency": "annual",
    "frequencyLabel": "Annuale, secondo disponibilità della rilevazione",
    "expectedRelease": "Secondo il calendario Istat della spesa sociale dei Comuni",
    "acquisitionMethod": "Download delle tavole comunali A misura di Comune; valori e composizioni sono conservati nello snapshot versionato senza stime aggiuntive dell'Osservatorio.",
    "licenseName": "CC BY 4.0",
    "licenseUrl": "https://www.istat.it/note-legali/",
}
registry.setdefault("sourceProfiles", {})["regione-toscana-early-childhood"] = {
    "publisher": "Regione Toscana",
    "frequency": "school_year",
    "frequencyLabel": "Annuale, per anno educativo",
    "expectedRelease": "Dopo il consolidamento dell'anno educativo",
    "acquisitionMethod": "Download del CSV comunale ufficiale e calcolo del tasso come ricettività potenziale / residenti 3–36 mesi × 100.",
    "licenseName": "Licenza indicata nel catalogo Open Data Regione Toscana",
    "licenseUrl": "https://www.regione.toscana.it/open-data",
}
url_profiles = registry.setdefault("sourceUrlProfiles", {})
url_profiles["https://www.istat.it/storage/misura-comune/10a-Servizi-sociali-per-tipologia-di-utenza.xlsx"] = "istat-social-services-annual"
url_profiles["https://www.istat.it/storage/misura-comune/10b-Servizi-sociali-per-abitante.xlsx"] = "istat-social-services-annual"
url_profiles["https://dati.toscana.it/dataset/serviziprimainfanzia"] = "regione-toscana-early-childhood"
url_profiles["https://dati.toscana.it/dataset/98ee6064-b61a-45e2-a790-86c55b278574/resource/01588909-8f0b-4b80-8af7-1749bab80a5e/download/opendata-_-da-pubblicare-24-25.csv"] = "regione-toscana-early-childhood"
overrides = registry.setdefault("metricOverrides", {})
overrides["socialSpendingPerResident"] = {"profile": "istat-social-services-annual"}
overrides["socialSpendingByUserArea"] = {"profile": "istat-social-services-annual"}
overrides["earlyChildhoodPotentialCapacityRate"] = {"profile": "regione-toscana-early-childhood"}
save(registry_path, registry)

# 5) Contratto di release canonica.
replace("scripts/finalize_catalog_release.py", "v1.17.0", "v1.18.0")
replace("scripts/finalize_catalog_release.py", 'UPDATED = "24 agosto 2026"', 'UPDATED = "25 agosto 2026"')
replace("scripts/finalize_catalog_release.py", "EXPECTED_METRICS = 143", "EXPECTED_METRICS = 146")
replace("scripts/finalize_catalog_release.py", "EXPECTED_INLINE = 139", "EXPECTED_INLINE = 142")

# 6) README e cronologia pubblica.
replace("README.md", "Versione dati corrente: **v1.17.0** — 24 agosto 2026.", "Versione dati corrente: **v1.18.0** — 25 agosto 2026.")
replace("README.md", "143 indicatori nel catalogo canonico: 139 con valori incorporati e 4 climatici con storici separati;", "146 indicatori nel catalogo canonico: 142 con valori incorporati e 4 climatici con storici separati;")
replace("README.md", "`indicatori/`: 139 pagine canoniche generate in build, una per indicatore con dati incorporati;", "`indicatori/`: 142 pagine canoniche generate in build, una per indicatore con dati incorporati;")
replace("README.md", "`data/site-data.json`: catalogo canonico dei 143 indicatori, con dati incorporati per 139 e riferimenti ai file storici separati per i 4 climatici;", "`data/site-data.json`: catalogo canonico dei 146 indicatori, con dati incorporati per 142 e riferimenti ai file storici separati per i 4 climatici;")
replace("README.md", "Il catalogo e i metadati dei 143 indicatori sono centralizzati", "Il catalogo e i metadati dei 146 indicatori sono centralizzati")
replace("README.md", "valida tutti i 143 indicatori canonici, la ripartizione fra 139 valori incorporati e 4 storici climatici separati", "valida tutti i 146 indicatori canonici, la ripartizione fra 142 valori incorporati e 4 storici climatici separati")
replace("README.md", "La build genera una pagina autonoma per ciascuno dei 139 indicatori incorporati", "La build genera una pagina autonoma per ciascuno dei 142 indicatori incorporati")

history_path = ROOT / "assets" / "app-parts" / "05.txt"
history = history_path.read_text(encoding="utf-8")
entry = "      ['2026.08.25-v1.18.0','25 agosto 2026','146 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunti Welfare e servizi sociali (spesa per abitante e composizione per area di utenza) e Prima infanzia (ricettività potenziale 3–36 mesi).'],\n"
marker = "    const versions = [\n"
if "2026.08.25-v1.18.0" not in history:
    if marker not in history:
        raise RuntimeError("assets/app-parts/05.txt: cronologia release non trovata")
    history = history.replace(marker, marker + entry, 1)
    history_path.write_text(history, encoding="utf-8")

# 7) Cache asset della release.
replace("scripts/build_static_safe.py", 'UX_ASSET_VERSION = "20260824-v117"', 'UX_ASSET_VERSION = "20260825-v118"')
replace("scripts/build_static_brand.py", 'APP_BUNDLE_ASSET_VERSION = "20260824-v117"', 'APP_BUNDLE_ASSET_VERSION = "20260825-v118"')
replace("service-worker.js", "ov-pwa-20260824-v117", "ov-pwa-20260825-v118")

# 8) Aggiorna il gate catalogo esistente e aggiunge le garanzie specifiche Welfare.
test_path = ROOT / "scripts" / "test_catalog_release_v116.py"
test = test_path.read_text(encoding="utf-8")
test = test.replace("release v1.17.0", "release v1.18.0")
test = test.replace('"2026.08.24-v1.17.0" in app and "143 indicatori complessivi" in app', '"2026.08.25-v1.18.0" in app and "146 indicatori complessivi" in app')
test = test.replace('"**v1.17.0** — 24 agosto 2026" in readme', '"**v1.18.0** — 25 agosto 2026" in readme')
test = test.replace('"143 indicatori" in readme and "139 con valori incorporati" in readme', '"146 indicatori" in readme and "142 con valori incorporati" in readme')
test = test.replace('UX_ASSET_VERSION = "20260824-v117"', 'UX_ASSET_VERSION = "20260825-v118"')
test = test.replace('APP_BUNDLE_ASSET_VERSION = "20260824-v117"', 'APP_BUNDLE_ASSET_VERSION = "20260825-v118"')
test = test.replace("ov-pwa-20260824-v117", "ov-pwa-20260825-v118")
needle = "    chart_app = (ROOT / \"assets\" / \"app-parts\" / \"03.txt\").read_text(encoding=\"utf-8\")\n"
extra = "    assert 'part.count === null || part.count === undefined' in chart_app, 'Le distribuzioni senza conteggi non devono mostrare NaN'\n"
if extra not in test:
    test = test.replace(needle, needle + extra, 1)
test_path.write_text(test, encoding="utf-8")

print("Release Welfare v1.18.0 pronta: 146 indicatori (142 inline + 4 climatici), UI senza NaN residenti.")
