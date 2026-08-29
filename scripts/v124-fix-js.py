from pathlib import Path

p = Path('assets/app-parts/03.txt')
s = p.read_text(encoding='utf-8')
bad = '</b></div></aside>`));\n    container.innerHTML'
good = '</b></div></aside>`);\n    container.innerHTML'
if bad not in s:
    raise SystemExit('Expected v1.24 positionMarkup syntax marker not found')
p.write_text(s.replace(bad, good, 1), encoding='utf-8')
