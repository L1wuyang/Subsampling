"""Build deterministic code/data assets; optionally publish a verified GitHub Release.

The data bytes come from the immutable source commit in review_data.json. Build
uses only Python's standard library. Publish additionally requires Git, GitHub
CLI and GH_TOKEN, and never replaces an existing tag or release asset.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'L1wuyang/Subsampling'
DATE = (1980, 1, 1, 0, 0, 0)
MAX_SOURCE_BYTES = 1024 * 1024 * 1024


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def relative_name(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError(f'Invalid release path: {name!r}')
    if PurePosixPath(name).is_absolute() or any(p in ('', '.', '..') for p in name.split('/')):
        raise ValueError(f'Unsafe release path: {name!r}')
    return name


def regular_file(root, name):
    name = relative_name(name)
    root = Path(root).resolve()
    path = root
    for part in name.split('/'):
        path = path / part
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError(f'Linked release input: {name}')
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError(f'Missing or unsafe release input: {name}')
    return path


def checked_bytes(data, record, name):
    if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError(f'Input integrity mismatch: {name}')
    return data


def checked_file(root, name, record):
    return checked_bytes(regular_file(root, name).read_bytes(), record, name)


def descriptor(root):
    version = regular_file(root, 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'v[0-9]{4}\.[0-9]{1,2}\.[0-9]{1,2}\.[0-9]+', version):
        raise ValueError('VERSION must be vYYYY.MM.DD.N')
    value = json.loads(regular_file(root, 'provenance/review_data.json').read_bytes())
    if value.get('schema') != 1 or value.get('version') != version:
        raise ValueError('VERSION and review-data descriptor disagree')
    if not re.fullmatch('[0-9a-f]{40}', value.get('source_commit', '')):
        raise ValueError('Review-data source must be a complete immutable commit SHA')
    expected_name = f'Subsampling-review-data-{version}.zip'
    expected_url = f'https://github.com/{REPOSITORY}/releases/download/{version}/{expected_name}'
    archive = value['archive']
    if archive['name'] != expected_name or archive['url'] != expected_url:
        raise ValueError('Unexpected review-data asset name or URL')
    if not re.fullmatch('[0-9a-f]{64}', archive['sha256']):
        raise ValueError('Invalid archive checksum')
    if not isinstance(archive['bytes'], int) or not 0 < archive['bytes'] < MAX_SOURCE_BYTES:
        raise ValueError('Unexpected archive length')
    if not isinstance(value['files'], dict) or not value['files']:
        raise ValueError('The review-data member inventory must be nonempty')
    for name, record in value['files'].items():
        relative_name(name)
        if not isinstance(record['bytes'], int) or not 0 <= record['bytes'] < MAX_SOURCE_BYTES:
            raise ValueError(f'Invalid member length: {name}')
        if not re.fullmatch('[0-9a-f]{64}', record['sha256']):
            raise ValueError(f'Invalid member checksum: {name}')
    return version, value


def write_zip(path, records, read, prefix=''):
    """Identical bytes across platforms: sorted, stored, fixed UTC-like DOS date."""
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_STORED) as archive:
        archive.comment = b''
        for name in sorted(records):
            info = zipfile.ZipInfo(prefix + relative_name(name), date_time=DATE)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.extra = b''
            info.comment = b''
            archive.writestr(info, checked_bytes(read(name), records[name], name))


@contextmanager
def data_reader(value, source_dir=None, timeout=90):
    if source_dir is not None:
        yield lambda name: regular_file(source_dir, name).read_bytes()
        return
    url = f'https://codeload.github.com/{REPOSITORY}/zip/{value["source_commit"]}'
    with tempfile.TemporaryDirectory(prefix='subsampling-source-') as folder:
        path = Path(folder) / 'source.zip'
        request = urllib.request.Request(url, headers={'User-Agent': 'Subsampling-release-builder'})
        with urllib.request.urlopen(request, timeout=timeout) as response, path.open('xb') as output:
            size = 0
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_SOURCE_BYTES:
                    raise ValueError('Source archive exceeds the download limit')
                output.write(chunk)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError('Duplicate names in source archive')
            prefix = 'Subsampling-' + value['source_commit'] + '/'
            def read(name):
                info = archive.getinfo(prefix + relative_name(name))
                mode = stat.S_IFMT(info.external_attr >> 16)
                if info.is_dir() or mode not in (0, stat.S_IFREG):
                    raise ValueError(f'Nonregular source member: {name}')
                if info.file_size != value['files'][name]['bytes']:
                    raise ValueError(f'Source member length mismatch: {name}')
                return archive.read(info)
            yield read


def build(output, source_dir=None, timeout=90, root=ROOT):
    root = Path(root).resolve()
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Choose a new release output directory')
    if output.resolve().is_relative_to(root) or root.is_relative_to(output.resolve()):
        raise ValueError('Build release assets outside the source checkout and its parents')
    version, value = descriptor(root)
    manifest_path = regular_file(root, 'MANIFEST.json')
    core = json.loads(manifest_path.read_bytes())['files']
    if set(core) & set(value['files']):
        raise ValueError('Core and review-data inventories overlap')
    for name, record in core.items():
        checked_file(root, name, record)
    core = dict(core)
    core['MANIFEST.json'] = {'bytes': manifest_path.stat().st_size, 'sha256': digest(manifest_path)}
    notes = regular_file(root, 'docs/RELEASE_NOTES.md').read_text(encoding='utf-8')
    if version not in notes:
        raise ValueError('Release notes do not identify VERSION')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.subsampling-build-', dir=output.parent) as temporary:
        temporary = Path(temporary)
        data_path = temporary / value['archive']['name']
        with data_reader(value, source_dir, timeout) as read:
            write_zip(data_path, value['files'], read)
        if data_path.stat().st_size != value['archive']['bytes'] or digest(data_path) != value['archive']['sha256']:
            raise ValueError('Rebuilt data archive differs from the frozen descriptor')
        core_path = temporary / f'Subsampling-core-{version}.zip'
        write_zip(core_path, core, lambda name: regular_file(root, name).read_bytes(), f'Subsampling-{version}/')
        assets = {p.name: {'sha256': digest(p), 'bytes': p.stat().st_size} for p in (core_path, data_path)}
        checksums = ''.join(f'{record["sha256"]}  {name}\n' for name, record in sorted(assets.items()))
        (temporary/'SHA256SUMS.txt').write_bytes(checksums.encode('ascii'))
        assets['SHA256SUMS.txt'] = {'bytes': len(checksums), 'sha256': hashlib.sha256(checksums.encode('ascii')).hexdigest()}
        (temporary/'release_notes.md').write_bytes(notes.encode('utf-8'))
        report = {'version': version, 'source_commit': value['source_commit'], 'core_files': len(core),
                  'data_files': len(value['files']), 'assets': assets, 'data_archive_matches_descriptor': True,
                  'numerical_trajectories_executed': 0}
        (temporary/'build_validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        temporary.rename(output)
    return report


def gh_json(arguments, payload=None, missing_ok=False):
    command = ['gh', 'api', *arguments]
    raw = None if payload is None else json.dumps(payload).encode('utf-8')
    if payload is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=raw, capture_output=True, check=False)
    if result.returncode:
        detail = result.stderr.decode('utf-8', errors='replace')
        if missing_ok and '(HTTP 404)' in detail:
            return None
        raise RuntimeError('GitHub API operation failed: ' + detail.strip())
    return json.loads(result.stdout) if result.stdout.strip() else None


def tag_commit(version):
    ref = gh_json([f'repos/{REPOSITORY}/git/ref/tags/{version}'], missing_ok=True)
    if ref is None:
        return None
    obj = ref['object']
    for _ in range(8):
        if obj['type'] == 'commit':
            return obj['sha']
        if obj['type'] != 'tag':
            raise ValueError('Release tag does not identify a commit')
        obj = gh_json([f'repos/{REPOSITORY}/git/tags/{obj["sha"]}'])['object']
    raise ValueError('Release tag indirection is excessive')


def assert_assets(release, expected):
    assets = release.get('assets', [])
    names = [a['name'] for a in assets]
    if len(names) != len(set(names)) or not set(names).issubset(expected):
        raise ValueError('Existing release has unexpected or duplicate assets; refusing to alter it')
    for item in assets:
        name = item['name']
        record = expected[name]
        if item['size'] != record['bytes'] or item.get('state') != 'uploaded':
            raise ValueError(f'Existing asset has the wrong size/state: {name}')
        if item.get('digest') is not None:
            if item['digest'] != 'sha256:' + record['sha256']:
                raise ValueError(f'Existing asset has a different checksum: {name}')
        else:
            # Older GitHub assets may omit digest. Download without replacing any local file.
            with tempfile.TemporaryDirectory(prefix='subsampling-asset-check-') as folder:
                subprocess.run(['gh','release','download',release['tag_name'],'--repo',REPOSITORY,
                                '--pattern',name,'--dir',folder],check=True,capture_output=True)
                if digest(Path(folder)/name) != record['sha256']:
                    raise ValueError(f'Existing asset bytes differ: {name}')
    return set(names)


def publish(output, root=ROOT):
    root = Path(root).resolve()
    output = Path(output).resolve()
    version, value = descriptor(root)
    report = json.loads(regular_file(output, 'build_validation.json').read_bytes())
    if report['version'] != version or not report['data_archive_matches_descriptor']:
        raise ValueError('Build record/version mismatch')
    expected_names = {f'Subsampling-core-{version}.zip', value['archive']['name'], 'SHA256SUMS.txt'}
    if set(report['assets']) != expected_names:
        raise ValueError('Unexpected built asset inventory')
    for name, record in report['assets'].items():
        checked_file(output, name, record)
    data_record = report['assets'][value['archive']['name']]
    if data_record != {k:value['archive'][k] for k in ('sha256','bytes')}:
        raise ValueError('Data asset no longer matches descriptor')
    notes = regular_file(root, 'docs/RELEASE_NOTES.md').read_text(encoding='utf-8')
    if regular_file(output, 'release_notes.md').read_text(encoding='utf-8') != notes:
        raise ValueError('Release notes changed after build')
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()
    if os.environ.get('GITHUB_REPOSITORY') != REPOSITORY or os.environ.get('GITHUB_REF') != 'refs/heads/main':
        raise ValueError('Publication is restricted to this repository main-branch workflow')
    if os.environ.get('GITHUB_SHA') != head or not re.fullmatch('[0-9a-f]{40}',head):
        raise ValueError('Checkout is not the workflow target commit')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=root).strip():
        raise ValueError('Tracked checkout files changed after checkout')
    release = gh_json([f'repos/{REPOSITORY}/releases/tags/{version}'], missing_ok=True)
    target = tag_commit(version)
    if target is not None and target != head:
        raise ValueError('Existing version tag points to another commit; use a new VERSION')
    title = f'Subsampling {version}: core code and review data'
    body = notes.rstrip() + f'\n\nFixed source commit: `{head}`.\n'
    if release is not None:
        if target is None or release['name'] != title or release['body'].replace('\r\n','\n') != body:
            raise ValueError('Existing release does not match this build; refusing to change it')
        present = assert_assets(release, report['assets'])
        if not release['draft']:
            if present != expected_names:
                raise ValueError('Published release is incomplete; refusing to mutate it')
            return {'published':True,'version':version,'commit':head,'url':release['html_url'],'already_complete':True}
    if target is None:
        tag = gh_json([f'repos/{REPOSITORY}/git/tags','--method','POST'],
                      {'tag':version,'message':title+'\n\n'+body,'object':head,'type':'commit'})
        gh_json([f'repos/{REPOSITORY}/git/refs','--method','POST'],
                {'ref':'refs/tags/'+version,'sha':tag['sha']})
    if tag_commit(version) != head:
        raise ValueError('Published tag target mismatch')
    if release is None:
        release = gh_json([f'repos/{REPOSITORY}/releases','--method','POST'],
            {'tag_name':version,'target_commitish':head,'name':title,'body':body,'draft':True,'prerelease':False})
    present = assert_assets(release, report['assets'])
    for name in sorted(expected_names-present):
        # No --clobber: another writer or an unexpected same-name asset must fail safely.
        subprocess.run(['gh','release','upload',version,str(output/name),'--repo',REPOSITORY],check=True)
    release = gh_json([f'repos/{REPOSITORY}/releases/{release["id"]}'])
    if assert_assets(release, report['assets']) != expected_names or tag_commit(version) != head:
        raise ValueError('Final release verification failed; draft left unpublished')
    if (release['tag_name'] != version or release['name'] != title
            or release['body'].replace('\r\n','\n') != body):
        raise ValueError('Release metadata changed during upload; refusing to publish')
    if not release['draft']:
        return {'published':True,'version':version,'commit':head,'url':release['html_url'],'already_complete':True}
    release = gh_json([f'repos/{REPOSITORY}/releases/{release["id"]}','--method','PATCH'],
                      {'draft':False,'make_latest':'true'})
    if release['draft']:
        raise ValueError('Release is unexpectedly still a draft')
    return {'published':True,'version':version,'commit':head,'url':release['html_url'],'already_complete':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-dir',type=Path,help='Use local original data instead of downloading the fixed source commit')
    parser.add_argument('--timeout',type=float,default=90.)
    parser.add_argument('--publish',action='store_true',help='Publish an already built output in the authorized main-branch GitHub workflow')
    args = parser.parse_args()
    result = publish(args.output) if args.publish else build(args.output,args.source_dir,args.timeout)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
