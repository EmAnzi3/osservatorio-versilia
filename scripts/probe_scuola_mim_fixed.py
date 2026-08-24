#!/usr/bin/env python3
"""Compatibilità temporanea: corregge il path delle distribuzioni CSV MIM."""
from __future__ import annotations

import probe_scuola_mim as probe


def candidate_urls(code: str):
    base = "https://dati.istruzione.it/opendata/opendata/catalog/"
    for school_year, date in probe.DISTRIBUTIONS:
        yield f"{base}{code}{school_year}{date}.csv"


probe.candidate_urls = candidate_urls
probe.main()
