#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/".github/workflows/pages.yml"
text=PATH.read_text(encoding="utf-8")
if "Materialize Lavoro e Istruzione per età e genere" in text:
    print("Pages workflow già aggiornato")
    raise SystemExit(0)

anchor='''      - name: Build pre-rendered site
        run: python scripts/build_static_brand.py
'''
insert='''      - name: Materialize Lavoro e Istruzione per età e genere
        run: |
          python scripts/materialize_lavoro_istruzione_eta_genere.py
          python scripts/patch_lavoro_istruzione_eta_genere_frontend.py
          python scripts/test_lavoro_istruzione_eta_genere.py
          python -m json.tool data/site-data.json > /dev/null
          python -m json.tool data/source-snapshots/istat-lavoro-istruzione-eta-genere-2024.json > /dev/null

      - name: Build pre-rendered site
        run: python scripts/build_static_brand.py
'''
if anchor not in text: raise RuntimeError("Anchor build non trovato")
text=text.replace(anchor,insert,1)

anchor2='''      - name: Validate PNRR Toscana town experience
        run: python scripts/test_pnrr_toscana_town_browser.py --base http://127.0.0.1:8123/
'''
insert2='''      - name: Validate Lavoro e Istruzione per età e genere
        run: python scripts/test_lavoro_istruzione_eta_genere_browser.py --base http://127.0.0.1:8123/

      - name: Validate PNRR Toscana town experience
        run: python scripts/test_pnrr_toscana_town_browser.py --base http://127.0.0.1:8123/
'''
if anchor2 not in text: raise RuntimeError("Anchor browser non trovato")
text=text.replace(anchor2,insert2,1)

anchor3='''            scripts/test_amministrazione_lotto_a_browser.py \\
            scripts/test_percorsi_mobile_list_contract.py
'''
insert3='''            scripts/test_amministrazione_lotto_a_browser.py \\
            scripts/materialize_lavoro_istruzione_eta_genere.py \\
            scripts/patch_lavoro_istruzione_eta_genere_frontend.py \\
            scripts/test_lavoro_istruzione_eta_genere.py \\
            scripts/test_lavoro_istruzione_eta_genere_browser.py \\
            scripts/test_percorsi_mobile_list_contract.py
'''
if anchor3 not in text: raise RuntimeError("Anchor py_compile non trovato")
text=text.replace(anchor3,insert3,1)
PATH.write_text(text,encoding="utf-8")
print("Pages workflow aggiornato con materializzazione, test dati e test browser età×genere.")
