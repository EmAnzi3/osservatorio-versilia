#!/usr/bin/env python3
from __future__ import annotations

import inspect

import build_siope_history as builder

for name in ("main", "current_values"):
    print(f"=== {name} ===")
    print(inspect.getsource(getattr(builder, name)))
