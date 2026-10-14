#!/usr/bin/env python3
"""Build a review-only static preview; no public routes or canonical copies."""
import argparse
import base64
import gzip
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from build_a7_static_pilot import ROOT, build, encode, render_answers


def validate_repository_commit(bundle, commit, root=ROOT):
    """Resolve actual Git content offline; a well-formed SHA is not evidence."""
    if not re.fullmatch(r'[a-f0-9]{40}', commit):
        raise ValueError('repository_commit_required')
    def git(*args):
        try:
            return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            raise ValueError('repository_commit_or_path_unavailable') from error
    git('cat-file','-e',commit+'^{commit}')
    files={}
    def read(path):
        if not isinstance(path,str) or not re.fullmatch(r'(?:ci|docs|data)/[A-Za-z0-9_./-]+',path) or '..' in path.split('/'):
            raise ValueError('invalid_repository_evidence_path')
        if path not in files:
            if git('cat-file','-t',commit+':'+path).strip()!=b'blob':
                raise ValueError('repository_evidence_not_file')
            files[path]=git('show',commit+':'+path)
        return files[path]
    def check(path, expected=None):
        data=read(path)
        if expected is not None and hashlib.sha256(data).hexdigest()!=expected:
            raise ValueError('repository_evidence_hash_mismatch:'+path)
        return data
    check('ci/territorial-dossier-program.json',bundle['programSha256'])
    for question in bundle['questions']:
        path=question['dossierPath']
        if check(path)!=(root/path).read_bytes():
            raise ValueError('repository_dossier_mismatch:'+path)
    def walk(value):
        if isinstance(value,list):
            for child in value:walk(child)
        elif isinstance(value,dict):
            path=value.get('path')
            if isinstance(path,str) and path.startswith(('data/','docs/')):
                if value.get('encoding')=='concatenate_ascii_base64_gzip_json':
                    if git('cat-file','-t',commit+':'+path).strip()!=b'tree':
                        raise ValueError('repository_snapshot_directory_missing')
                    parts=value.get('parts',[])
                    if not parts or value.get('sha256Basis')!='decoded_json_bytes':
                        raise ValueError('unsupported_reconstructed_snapshot')
                    encoded=b''.join(check(part['path'],part['sha256']) for part in parts)
                    data=gzip.decompress(base64.b64decode(b''.join(encoded.split()),validate=True))
                    if hashlib.sha256(data).hexdigest()!=value['sha256']:
                        raise ValueError('repository_reconstructed_hash_mismatch:'+path)
                else:check(path,value.get('sha256'))
            for child in value.values():walk(child)
    walk(bundle['cases'])
    return {'commit':commit,'files':len(files),'status':'PASS'}


def preview(output, repository_commit, catalog=None, bundle=None, release=None):
    if not re.fullmatch(r'[a-f0-9]{40}', repository_commit):
        raise ValueError('repository_commit_required')
    if bundle is None:
        bundle, release, _ = build(catalog)
    validate_repository_commit(bundle,repository_commit)
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
