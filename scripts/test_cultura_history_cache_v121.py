#!/usr/bin/env python3
"""Regression gate: gli storici Cultura non devono restare bloccati in cache."""
from pathlib import Path
import re

from finalize_catalog_release import VERSION as CATALOG_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PART = (ROOT / "assets" / "app-parts" / "03.txt").read_text(encoding="utf-8")
BUILD_BRAND = (ROOT / "scripts" / "build_static_brand.py").read_text(encoding="utf-8")
BUILD_SAFE = (ROOT / "scripts" / "build_static_safe.py").read_text(encoding="utf-8")
UX_HISTORY = (ROOT / "assets" / "ux-history.js").read_text(encoding="utf-8")


def constant(text: str, pattern: str, label: str) -> str:
    match = re.search(pattern, text)
    assert match, f"Costante {label} non trovata"
    return match.group(1)


# La preview e la produzione non caricano assets/app.js: build_static.py crea
# assets/app-bundle.js e build_static_brand.py ne decide la query di cache-busting.
# Il gate verifica quindi che tutte le revisioni correnti restino sincronizzate,
# senza fissarsi sulla release che introdusse per prima gli storici Cultura.
app_version = constant(APP, r"const VERSION='([^']+)';", "VERSION app")
ux_version = constant(BUILD_SAFE, r'UX_ASSET_VERSION = "([^"]+)"', "UX_ASSET_VERSION")
history_version = constant(BUILD_SAFE, r'HISTORY_ASSET_VERSION = "([^"]+)"', "HISTORY_ASSET_VERSION")
bundle_version = constant(BUILD_BRAND, r'APP_BUNDLE_ASSET_VERSION = "([^"]+)"', "APP_BUNDLE_ASSET_VERSION")
pwa_revision = constant(BUILD_BRAND, r'PWA_JS_REVISION = "([^"]+)"', "PWA_JS_REVISION")
hotfix_version = constant(UX_HISTORY, r"const HOTFIX_VERSION = '([^']+)';", "HOTFIX_VERSION")
sw_version = constant(SW, r"const VERSION = '([^']+)';", "service worker VERSION")

assert app_version == ux_version == history_version == bundle_version == hotfix_version, (
    "Revisioni asset non sincronizzate",
    app_version,
    ux_version,
    history_version,
    bundle_version,
    hotfix_version,
)
release_suffix = CATALOG_VERSION.removeprefix("v").replace(".", "")
assert pwa_revision == f"catalog-v{release_suffix}", "Revisione PWA non allineata alla release canonica"
assert app_version in sw_version, "Service worker non allineato alla revisione asset corrente"

assert 'rf\'src="\\1?v={APP_BUNDLE_ASSET_VERSION}"\'' in BUILD_BRAND, "La build non applica il cache-buster al bundle di produzione"
assert 'script in {"ux-history-core.js", "ux-history.js"}' in BUILD_SAFE, "ux-history.js non usa il cache-buster storico dedicato"
assert UX_HISTORY.count("LIBRARY_HISTORY_KEYS.has(selected.key)") >= 2, "L'enhancer 7/7 deve lasciare intatti gli storici Cultura sia nel confronto sia nelle schede comunali"
assert "app-parts" in SW and "\\d{2}\\.txt" in SW, "I moduli .txt non sono gestiti esplicitamente dal service worker"
assert "networkFirst(request)" in SW, "Policy network-first assente"
assert "function libraryHistoryTableMarkup(metric)" in PART, "Renderer storico Cultura assente"
assert "Media comuni con dato" in PART, "Colonna media storica assente"
assert "libraryHistoryTableMarkup(metric)" in PART, "Storico non collegato al rendering del confronto"

print(
    "Cache policy Cultura verificata: bundle, service worker ed enhancer storici "
    "seguono la revisione canonica corrente; il renderer parziale del lotto non viene sovrascritto dal contratto 7/7."
)

assert "toolkit.viewShellMarkup(currentMarkup, historyMarkup, true, note)" in UX_HISTORY, "Lo switch Attuale/Storico Cultura deve essere ricostruito nel confronto"
assert "toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note)" in UX_HISTORY, "Lo switch Attuale/Storico Cultura deve essere ricostruito nelle schede comunali"
