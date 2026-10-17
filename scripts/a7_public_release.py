"""Content-addressed public A7 assets, separate from the canonical data catalog."""
import hashlib
import json
import re

FILES = ('answers.md', 'bundle.json', 'preview.mjs', 'public.css', 'public.mjs', 'reader.mjs', 'release.mjs', 'education.mjs', 'education.json', 'education.pdf')


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
    def raw(path):
        value = read(path)
        return value.encode() if isinstance(value, str) else value
    page = raw('chiedi/index.html').decode('utf-8')
    relative = release_path(page)
    if f'src="{relative}public.mjs"' not in page or f'href="{relative}public.css"' not in page:
        raise ValueError('unbound_a7_entrypoint')
    prefix = 'chiedi/' + relative
    text = raw(prefix + 'manifest.json').decode('utf-8')
    if hashlib.sha256(text.encode()).hexdigest() != relative.split('/')[1]:
        raise ValueError('a7_manifest_hash_mismatch')
    manifest = json.loads(text)
    if manifest.get('schemaVersion') != 1 or set(manifest.get('files', {})) != set(FILES):
        raise ValueError('invalid_a7_manifest')
    blobs = {name: raw(prefix + name) for name in FILES}
    values = {name: data if name.endswith('.pdf') else data.decode('utf-8') for name, data in blobs.items()}
    for name, value in values.items():
        if not value or hashlib.sha256(blobs[name]).hexdigest() != manifest['files'][name]:
            raise ValueError('a7_asset_hash_mismatch:' + name)
    release = json.loads(values['release.mjs'].removeprefix('export default ').strip().removesuffix(';'))
    if not re.fullmatch(r'[a-f0-9]{40}', release.get('repositoryCommit', '')):
        raise ValueError('invalid_a7_source_commit')
    if hashlib.sha256(values['bundle.json'].encode()).hexdigest() != release['bundleSha256']:
        raise ValueError('a7_bundle_release_mismatch')
    if hashlib.sha256(values['reader.mjs'].encode()).hexdigest() != release['readerSha256']:
        raise ValueError('a7_reader_release_mismatch')
    education = json.loads(values['education.json'])
    if (hashlib.sha256(blobs['education.json']).hexdigest() != release['educationSha256'] or
        hashlib.sha256(blobs['education.pdf']).hexdigest() != release['educationPdfSha256'] or
        education['bundleSha256'] != release['bundleSha256'] or
        education['repositoryCommit'] != release['repositoryCommit'] or
        not blobs['education.pdf'].startswith(b'%PDF-')):
        raise ValueError('a7_education_release_mismatch')
    return relative, values, release
