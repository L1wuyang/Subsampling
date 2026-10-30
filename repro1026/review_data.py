"""Download, install or verify the separate, hash-pinned review-data package.

Only Python's standard library is needed. Installation validates the entire ZIP
before publishing any file, and never replaces an existing file with new bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = 'provenance/review_data.json'
CHUNK = 1024 * 1024
INSTALL_HELP = ('Run python run.py review-data download, or '
                'python run.py review-data install --file PATH_TO_ZIP.')


def _linklike(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) &
                 getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)))


def _root(root):
    root = Path(root).expanduser().absolute()
    for path in (*reversed(root.parents), root):
        if _linklike(path):
            raise ValueError(f'Symlink or reparse-point root ancestry: {path}')
    if not root.is_dir():
        raise ValueError(f'Repository root is not a directory: {root}')
    return root.resolve()


def _name(name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError(f'Unsafe review-data path: {name!r}')
    parts = name.split('/')
    reserved = re.compile(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', re.I)
    if any(part in ('', '.', '..') or part.endswith((' ', '.')) or
           any(ord(c) < 32 or c in '<>:"|?*' for c in part) or
           reserved.match(part) for part in parts):
        raise ValueError(f'Unsafe review-data path: {name!r}')
    if not (name.startswith('simulations/') or name.startswith('evidence/experiment5/')):
        raise ValueError(f'Unexpected review-data directory: {name}')
    return parts


def _target(root, name):
    current = root
    parts = _name(name)
    for index, part in enumerate(parts):
        current = current / part
        if _linklike(current):
            raise ValueError(f'Symlink or reparse-point data path: {current}')
        if current.exists() and index < len(parts) - 1 and not current.is_dir():
            raise ValueError(f'Data parent is not a directory: {current}')
    if not current.resolve().is_relative_to(root):
        raise ValueError(f'Data path escapes the repository: {name}')
    return current


def _digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _record(record):
    if (not isinstance(record, dict) or type(record.get('bytes')) is not int or
            record['bytes'] < 0 or not isinstance(record.get('sha256'), str) or
            re.fullmatch(r'[0-9a-f]{64}', record['sha256']) is None):
        raise ValueError('Invalid review-data byte count or SHA-256')


def load_descriptor(root=ROOT, descriptor=None):
    root = _root(root)
    if descriptor is None:
        path = root / DESCRIPTOR
        if _linklike(path) or _linklike(path.parent):
            raise ValueError('Review-data descriptor must not be a link')
        descriptor = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(descriptor, dict) or descriptor.get('schema') != 1:
        raise ValueError('Unsupported review-data descriptor schema')
    version = descriptor.get('version')
    if not isinstance(version, str) or re.fullmatch(r'v[0-9]+(?:\.[0-9]+){1,3}', version) is None:
        raise ValueError('Invalid review-data version')
    if re.fullmatch(r'[0-9a-f]{40}', str(descriptor.get('source_commit', ''))) is None:
        raise ValueError('Invalid review-data source commit')
    archive = descriptor.get('archive')
    _record(archive)
    filename = f'Subsampling-review-data-{version}.zip'
    url = f'https://github.com/L1wuyang/Subsampling/releases/download/{version}/{filename}'
    if archive.get('name') != filename or archive.get('url') != url or archive['bytes'] == 0:
        raise ValueError('Review-data archive must use its exact versioned Release URL')
    files = descriptor.get('files')
    if not isinstance(files, dict) or not files:
        raise ValueError('Review-data descriptor must contain files')
    normalized = set()
    for name, record in files.items():
        _name(name)
        _record(record)
        key = name.casefold()
        if key in normalized:
            raise ValueError('Review-data paths collide on case-insensitive filesystems')
        normalized.add(key)
    for name in normalized:
        if any('/'.join(name.split('/')[:i]) in normalized for i in range(1, len(name.split('/')))):
            raise ValueError('Review-data files contain a file/directory path collision')
    return descriptor


def _matches(path, record):
    return path.is_file() and path.stat().st_size == record['bytes'] and _digest(path) == record['sha256']


def verify(root=ROOT, descriptor=None):
    root = _root(root)
    descriptor = load_descriptor(root, descriptor)
    missing, mismatched, checked = [], [], 0
    for name, record in descriptor['files'].items():
        path = _target(root, name)
        if not path.exists():
            missing.append(name)
        elif not _matches(path, record):
            mismatched.append(name)
        else:
            checked += 1
    result = dict(passed=not missing and not mismatched, action='verify',
                  version=descriptor['version'], files=len(descriptor['files']),
                  verified_files=checked, missing_count=len(missing), mismatch_count=len(mismatched),
                  missing_files=missing[:10], mismatched_files=mismatched[:10],
                  numerical_trajectories_executed=0)
    if missing:
        result['message'] = 'Review data is not fully installed. ' + INSTALL_HELP
    if mismatched:
        result['message'] = 'Installed review data differs from its pinned hashes; no files were changed.'
    return result


def _copy_checked(source, target, record):
    digest, count = hashlib.sha256(), 0
    with target.open('xb') as output:
        while data := source.read(CHUNK):
            count += len(data)
            if count > record['bytes']:
                raise ValueError('Review-data member exceeds its declared byte count')
            digest.update(data)
            output.write(data)
    if count != record['bytes'] or digest.hexdigest() != record['sha256']:
        raise ValueError(f'Review-data member checksum mismatch: {target.name}')


def install(archive_path, root=ROOT, descriptor=None):
    root = _root(root)
    descriptor = load_descriptor(root, descriptor)
    files, archive_record = descriptor['files'], descriptor['archive']
    archive_path = Path(archive_path).expanduser()
    created = []
    with tempfile.TemporaryDirectory(prefix='subsampling-review-data-') as temporary:
        staging = Path(temporary)
        with archive_path.open('rb') as stream:
            if os.fstat(stream.fileno()).st_size != archive_record['bytes'] or hashlib.file_digest(stream, 'sha256').hexdigest() != archive_record['sha256']:
                raise ValueError('Review-data ZIP size/SHA-256 mismatch; nothing was installed')
            stream.seek(0)
            with zipfile.ZipFile(stream) as archive:
                members = archive.infolist()
                names = [member.filename for member in members]
                if len(names) != len(set(names)) or set(names) != set(files):
                    raise ValueError('Review-data ZIP has missing, unexpected or duplicate members')
                for member in members:
                    _name(member.filename)
                    mode = member.external_attr >> 16
                    kind = stat.S_IFMT(mode)
                    if (member.is_dir() or kind not in (0, stat.S_IFREG) or
                            member.flag_bits & 1 or member.external_attr & 0x10 or
                            member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED) or
                            member.file_size != files[member.filename]['bytes']):
                        raise ValueError(f'Invalid review-data ZIP member: {member.filename}')
                    staged = staging / member.filename
                    staged.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source:
                        _copy_checked(source, staged, files[member.filename])
        pending, existing = [], 0
        # Validate every destination before publishing the first new file.
        for name, record in files.items():
            path = _target(root, name)
            if path.exists():
                if not _matches(path, record):
                    raise ValueError(f'Refusing to overwrite existing data: {name}')
                existing += 1
            else:
                pending.append(name)
        try:
            for name in pending:
                path = _target(root, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path = _target(root, name)
                fd, temp_name = tempfile.mkstemp(prefix='.review-data-', suffix='.part', dir=path.parent)
                temp_path = Path(temp_name)
                try:
                    with os.fdopen(fd, 'wb') as output, (staging / name).open('rb') as source:
                        shutil.copyfileobj(source, output, CHUNK)
                        output.flush()
                        os.fsync(output.fileno())
                    path = _target(root, name)
                    try:
                        # Atomic create without replacing a concurrently created file.
                        os.link(temp_path, path)
                        created.append((name, path.stat().st_ino))
                    except FileExistsError:
                        if not _matches(_target(root, name), files[name]):
                            raise ValueError(f'Refusing to overwrite newly existing data: {name}')
                        existing += 1
                finally:
                    temp_path.unlink(missing_ok=True)
        except Exception:
            for name, inode in reversed(created):
                path = _target(root, name)
                if path.exists() and path.stat().st_ino == inode and _matches(path, files[name]):
                    path.unlink()
            raise
    return dict(passed=True, action='install', version=descriptor['version'], files=len(files),
                installed_files=len(created), existing_files_verified=existing,
                archive_sha256=archive_record['sha256'], numerical_trajectories_executed=0)


class _HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != 'https' or parsed.username or parsed.password:
            raise ValueError('Review-data downloads require HTTPS redirects')
        return super().redirect_request(request, fp, code, message, headers, newurl)


def download(root=ROOT, descriptor=None, timeout=90.0):
    root = _root(root)
    descriptor = load_descriptor(root, descriptor)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Download timeout must be finite and positive')
    record = descriptor['archive']
    request = urllib.request.Request(record['url'], headers={'User-Agent': 'Subsampling-review-data/' + descriptor['version']})
    opener = urllib.request.build_opener(_HTTPSRedirect())
    with tempfile.TemporaryDirectory(prefix='subsampling-review-download-') as directory:
        archive_path = Path(directory) / record['name']
        with opener.open(request, timeout=timeout) as response:
            _copy_checked(response, archive_path, record)
        result = install(archive_path, root, descriptor)
    result['action'] = 'download'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('download', 'install', 'verify'))
    parser.add_argument('--file', type=Path, help='Local review-data ZIP; required for install')
    parser.add_argument('--timeout', type=float, default=90.0, help='Download timeout in seconds')
    args = parser.parse_args(argv)
    if (args.action == 'install') != (args.file is not None):
        parser.error('Use --file PATH_TO_ZIP only with install; install requires --file')
    try:
        if args.action == 'download':
            result = download(timeout=args.timeout)
        elif args.action == 'install':
            result = install(args.file)
        else:
            result = verify()
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f'Review-data operation failed: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
