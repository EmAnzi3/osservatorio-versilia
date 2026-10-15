"""Content-addressed public A7 assets, separate from the canonical data catalog."""
import hashlib
import json
import re

FILES = ('answers.md', 'bundle.json', 'preview.mjs', 'public.css', 'public.mjs', 'reader.mjs', 'release.mjs')


def manifest_text(files):
    if set(files) != set(FILES):
        raise ValueError('invalid_a7_asset_set')
    manifest = {'schemaVersion': 1, 'files': {name: hashlib.sha256(files[name]).hexdigest() for name in FILES}}
    return json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def release_path(page):
    match = re.search(r'data-a7-release="(releases/([a-f0-9]{64})/)"', page)
    if not match:
        raise ValueError('missing_versioned_a7_release')
    return match.group(1)


def validate_release(read):
    page = read('chiedi/index.html')
    relative = release_path(page)
    if f'src="{relative}public.mjs"' not in page or f'href="{relative}public.css"' not in page:
        raise ValueError('unbound_a7_entrypoint')
    prefix = 'chiedi/' + relative
    text = read(prefix + 'manifest.json')
    if hashlib.sha256(text.encode()).hexdigest() != relative.split('/')[1]:
        raise ValueError('a7_manifest_hash_mismatch')
    manifest = json.loads(text)
    if manifest.get('schemaVersion') != 1 or set(manifest.get('files', {})) != set(FILES):
        raise ValueError('invalid_a7_manifest')
    values = {name: read(prefix + name) for name in FILES}
    for name, value in values.items():
        if not value or hashlib.sha256(value.encode()).hexdigest() != manifest['files'][name]:
            raise ValueError('a7_asset_hash_mismatch:' + name)
    release = json.loads(values['release.mjs'].removeprefix('export default ').strip().removesuffix(';'))
    if not re.fullmatch(r'[a-f0-9]{40}', release.get('repositoryCommit', '')):
        raise ValueError('invalid_a7_source_commit')
    if hashlib.sha256(values['bundle.json'].encode()).hexdigest() != release['bundleSha256']:
        raise ValueError('a7_bundle_release_mismatch')
    if hashlib.sha256(values['reader.mjs'].encode()).hexdigest() != release['readerSha256']:
        raise ValueError('a7_reader_release_mismatch')
    return relative, values, release
