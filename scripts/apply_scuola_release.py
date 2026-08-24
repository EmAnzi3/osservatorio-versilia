#!/usr/bin/env python3
"""Allinea metadati di release e quality gate dopo il lotto Scuola MIM."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str, required: bool = True) -> None:
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    if old not in text:
        if required and new not in text:
            raise RuntimeError(f'{path}: marker non trovato: {old!r}')
        return
    p.write_text(text.replace(old, new), encoding='utf-8')


replace('scripts/finalize_catalog_release.py', 'v1.16.0', 'v1.17.0')
replace('scripts/finalize_catalog_release.py', 'EXPECTED_METRICS = 138', 'EXPECTED_METRICS = 143')
replace('scripts/finalize_catalog_release.py', 'EXPECTED_INLINE = 134', 'EXPECTED_INLINE = 139')

replace('README.md', 'Versione dati corrente: **v1.16.0** — 24 agosto 2026.', 'Versione dati corrente: **v1.17.0** — 24 agosto 2026.')
replace('README.md', '138 indicatori nel catalogo canonico: 134 con valori incorporati e 4 climatici con storici separati;', '143 indicatori nel catalogo canonico: 139 con valori incorporati e 4 climatici con storici separati;')
replace('README.md', '`indicatori/`: 134 pagine canoniche generate in build, una per indicatore con dati incorporati;', '`indicatori/`: 139 pagine canoniche generate in build, una per indicatore con dati incorporati;')
replace('README.md', '`data/site-data.json`: catalogo canonico dei 138 indicatori, con dati incorporati per 134 e riferimenti ai file storici separati per i 4 climatici;', '`data/site-data.json`: catalogo canonico dei 143 indicatori, con dati incorporati per 139 e riferimenti ai file storici separati per i 4 climatici;')
replace('README.md', 'Il catalogo e i metadati dei 138 indicatori sono centralizzati', 'Il catalogo e i metadati dei 143 indicatori sono centralizzati')
replace('README.md', 'valida tutti i 138 indicatori canonici, la ripartizione fra 134 valori incorporati e 4 storici climatici separati', 'valida tutti i 143 indicatori canonici, la ripartizione fra 139 valori incorporati e 4 storici climatici separati')
replace('README.md', 'La build genera una pagina autonoma per ciascuno dei 134 indicatori incorporati', 'La build genera una pagina autonoma per ciascuno dei 139 indicatori incorporati')

p = ROOT / 'assets/app-parts/05.txt'
text = p.read_text(encoding='utf-8')
new_entry = "      ['2026.08.24-v1.17.0','24 agosto 2026','143 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto il lotto Scuola MIM: sicurezza documentale, accessibilità, mensa e palestra, epoca di costruzione e raggiungibilità dei 109 edifici scolastici censiti nei sette Comuni.'],\n"
marker = "    const versions = [\n"
if '2026.08.24-v1.17.0' not in text:
    if marker not in text:
        raise RuntimeError('assets/app-parts/05.txt: cronologia release non trovata')
    text = text.replace(marker, marker + new_entry, 1)
    p.write_text(text, encoding='utf-8')

replace('scripts/build_static_safe.py', 'UX_ASSET_VERSION = "20260824-v116"', 'UX_ASSET_VERSION = "20260824-v117"')
replace('scripts/build_static_brand.py', 'APP_BUNDLE_ASSET_VERSION = "20260824-v116"', 'APP_BUNDLE_ASSET_VERSION = "20260824-v117"')
replace('service-worker.js', 'ov-pwa-20260824-v116', 'ov-pwa-20260824-v117')

replace('scripts/test_catalog_release_v116.py', 'release v1.16.0', 'release v1.17.0')
replace('scripts/test_catalog_release_v116.py', '"2026.08.24-v1.16.0" in app and "138 indicatori complessivi" in app', '"2026.08.24-v1.17.0" in app and "143 indicatori complessivi" in app')
replace('scripts/test_catalog_release_v116.py', '"**v1.16.0** — 24 agosto 2026" in readme', '"**v1.17.0** — 24 agosto 2026" in readme')
replace('scripts/test_catalog_release_v116.py', '"138 indicatori" in readme and "134 con valori incorporati" in readme', '"143 indicatori" in readme and "139 con valori incorporati" in readme')
replace('scripts/test_catalog_release_v116.py', 'UX_ASSET_VERSION = "20260824-v116"', 'UX_ASSET_VERSION = "20260824-v117"')
replace('scripts/test_catalog_release_v116.py', 'APP_BUNDLE_ASSET_VERSION = "20260824-v116"', 'APP_BUNDLE_ASSET_VERSION = "20260824-v117"')
replace('scripts/test_catalog_release_v116.py', 'ov-pwa-20260824-v116', 'ov-pwa-20260824-v117')

p = ROOT / '.github/workflows/pages.yml'
text = p.read_text(encoding='utf-8')
if 'python scripts/test_scuola_mim.py' not in text:
    text = text.replace('          python scripts/test_amministrazione_lotto_a.py\n', '          python scripts/test_amministrazione_lotto_a.py\n          python scripts/test_scuola_mim.py\n', 1)
if 'mim-edilizia-scolastica-versilia-2024-25.json' not in text:
    text = text.replace('          python -m json.tool data/source-snapshots/rgs-formazione-2024.json > /dev/null\n', '          python -m json.tool data/source-snapshots/rgs-formazione-2024.json > /dev/null\n          python -m json.tool data/source-snapshots/mim-edilizia-scolastica-versilia-2024-25.json > /dev/null\n', 1)
if 'scripts/materialize_scuola_mim.py' not in text:
    text = text.replace('            scripts/materialize_amministrazione_lotto_a_v2.py \\\n', '            scripts/materialize_amministrazione_lotto_a_v2.py \\\n            scripts/materialize_scuola_mim.py \\\n            scripts/test_scuola_mim.py \\\n', 1)
p.write_text(text, encoding='utf-8')

print('Release v1.17.0 allineata: 143 indicatori (139 inline + 4 climatici).')
