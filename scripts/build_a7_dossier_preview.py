#!/usr/bin/env python3
"""Build a review-only static preview; no public routes or canonical copies."""
import argparse
import json
import re
import shutil
from pathlib import Path
from build_a7_static_pilot import ROOT, build, encode, render_answers


def preview(output, repository_commit, catalog=None, bundle=None, release=None):
    if not re.fullmatch(r'[a-f0-9]{40}', repository_commit):
        raise ValueError('repository_commit_required')
    if bundle is None:
        bundle, release, _ = build(catalog)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/'bundle.json').write_text(encode(bundle), encoding='utf-8')
    # Pinned by the generating build, never supplied by a question or URL.
    (output/'release.mjs').write_text('export default '+json.dumps(dict(release, repositoryCommit=repository_commit), ensure_ascii=False, sort_keys=True)+';\n', encoding='utf-8')
    (output/'answers.md').write_text(render_answers(bundle), encoding='utf-8')
    for name in ['index.html', 'preview.mjs', 'preview.css']:
        shutil.copyfile(ROOT/'experiments/a7-dossier-preview'/name, output/name)
    shutil.copyfile(ROOT/'experiments/a7-static-pilot/reader.mjs', output/'reader.mjs')
    return output


def main():
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--repository-commit',required=True,help='Reviewed GitHub commit for frozen source/dossier links')
    args=p.parse_args();preview(args.output_dir,args.repository_commit,args.catalog)
    print('Review-only preview generated at '+str(args.output_dir))


if __name__=='__main__':
    main()
