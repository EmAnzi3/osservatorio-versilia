#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import tempfile
import zipfile
from pathlib import Path

import requests

URL = "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip"
OUT = Path("source-exploration/istat-sections")
OUT.mkdir(parents=True, exist_ok=True)


def download() -> Path:
    target = Path(tempfile.gettempdir()) / "istat-sections-2023.zip"
    with requests.get(URL, stream=True, timeout=(30, 900), headers={"User-Agent": "OsservatorioVersilia/1.0"}) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with target.open("wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if done % (25 * 1024 * 1024) < len(chunk):
                    print(f"download {done:,}/{total:,}", flush=True)
    print(f"download complete {target.stat().st_size:,}", flush=True)
    return target


def text_head(z: zipfile.ZipFile, name: str, limit: int = 100_000) -> str:
    with z.open(name) as f:
        raw = f.read(limit)
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def main() -> None:
    archive = download()
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        listing = [{"name": i.filename, "size": i.file_size, "compressed": i.compress_size} for i in infos]
        (OUT / "files.json").write_text(json.dumps(listing, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"files {len(infos)}", flush=True)
        for row in listing:
            print(row, flush=True)

        candidates = []
        for info in infos:
            low = info.filename.lower()
            if info.is_dir():
                continue
            is_text = low.endswith((".csv", ".txt", ".tsv", ".xml", ".json"))
            relevant_name = any(k in low for k in ("tracci", "dizion", "variab", "leggimi", "readme", "metadata", "descr"))
            tuscany = bool(re.search(r"(^|[/_.-])(09|toscana)([/_.-]|$)", low))
            if is_text and (relevant_name or tuscany or info.file_size < 2_000_000):
                candidates.append(info)

        summaries = []
        for idx, info in enumerate(candidates):
            try:
                head = text_head(z, info.filename)
            except Exception as exc:
                head = f"ERROR {exc!r}"
            safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", Path(info.filename).name)[:120]
            out_name = f"{idx:03d}_{safe}.head.txt"
            (OUT / out_name).write_text(head, encoding="utf-8")
            summaries.append({"name": info.filename, "size": info.file_size, "head_file": out_name})
            print("HEAD", info.filename, info.file_size, out_name, flush=True)
        (OUT / "heads.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
