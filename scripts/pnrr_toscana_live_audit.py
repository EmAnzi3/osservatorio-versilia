#!/usr/bin/env python3
"""Entry point live con dominio TLS canonico del portale Open Data Toscana."""
from __future__ import annotations

import pnrr_toscana_audit as audit

# `www.dati.toscana.it` presenta un certificato non valido per il sottodominio www.
# Il servizio ufficiale CKAN è disponibile sul dominio canonico senza www.
audit.CKAN_API = "https://dati.toscana.it/api/3/action/datastore_search"
audit.DATASET_URL = "https://dati.toscana.it/dataset/regione-toscana-pnrr"

if __name__ == "__main__":
    raise SystemExit(audit.main())
