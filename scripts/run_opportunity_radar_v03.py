#!/usr/bin/env python3
"""Entry point v0.3 con compatibilità per il fetch resiliente discovery.

Il fetch resiliente è definito nel modulo v0.2 e viene esposto sul namespace
v0.2.2 atteso dal collector v0.3 prima di eseguire il main.
"""
from __future__ import annotations

import opportunity_radar_v03 as radar

radar.v025.v022.fetch_resilient = radar.v025.v022.v02.fetch_resilient

if __name__ == "__main__":
    raise SystemExit(radar.main())
