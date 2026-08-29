#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/pnrr_toscana_audit.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "import re\nimport unicodedata\nimport urllib.request\n",
    "import re\nimport shutil\nimport subprocess\nimport tempfile\nimport unicodedata\nimport urllib.request\n",
    1,
)
old = '''def iter_csv_records(url: str = MAIN_CSV_URL) -> Iterable[dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/csv,*/*"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        text = io.TextIOWrapper(response, encoding="utf-8-sig", errors="replace", newline="")
        reader = csv.DictReader(text)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_FIELDS - fields)
        if missing:
            raise RuntimeError(f"Tracciato PNRR Toscana incompleto: {', '.join(missing)}")
        for field in CONCLUSION_FIELDS:
            if field not in fields:
                raise RuntimeError(f"Campo conclusione assente: {field}")
        yield from reader
'''
new = '''def _yield_csv_rows(stream: Any) -> Iterable[dict[str, str]]:
    reader = csv.DictReader(stream)
    fields = set(reader.fieldnames or [])
    missing = sorted(REQUIRED_FIELDS - fields)
    if missing:
        raise RuntimeError(f"Tracciato PNRR Toscana incompleto: {', '.join(missing)}")
    for field in CONCLUSION_FIELDS:
        if field not in fields:
            raise RuntimeError(f"Campo conclusione assente: {field}")
    yield from reader


def iter_csv_records(url: str = MAIN_CSV_URL) -> Iterable[dict[str, str]]:
    """Scarica il feed con retry robusti, poi effettua il parsing in streaming.

    Il CSV regionale supera 90 MB e occasionalmente interrompe una lettura urllib
    lunga. In CI si preferisce curl con retry su errori transitori; urllib resta
    il fallback portabile. Nessun file scaricato viene conservato nel repository.
    """
    curl = shutil.which("curl")
    if curl:
        with tempfile.NamedTemporaryFile(suffix=".csv") as temporary:
            completed = subprocess.run(
                [
                    curl,
                    "--fail",
                    "--location",
                    "--retry",
                    "4",
                    "--retry-delay",
                    "5",
                    "--retry-all-errors",
                    "--connect-timeout",
                    "20",
                    "--max-time",
                    "360",
                    "--user-agent",
                    USER_AGENT,
                    "--header",
                    "Accept: text/csv,*/*",
                    "--output",
                    temporary.name,
                    url,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=390,
            )
            if completed.returncode == 0:
                with open(temporary.name, encoding="utf-8-sig", errors="replace", newline="") as stream:
                    yield from _yield_csv_rows(stream)
                return

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/csv,*/*",
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        stream = io.TextIOWrapper(response, encoding="utf-8-sig", errors="replace", newline="")
        yield from _yield_csv_rows(stream)
'''
if old not in text:
    raise SystemExit("marker iter_csv_records non trovato")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
