"""Acquire/check the exact three Experiment V inputs without bundling raw data.

python -m repro1026.data_sources check --dataset all
python -m repro1026.data_sources download --dataset gdsc
python -m repro1026.data_sources download --dataset year --file year_archive=/local/data.zip
Uses only the Python standard library; existing files are never overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import ssl
import sys
import time
import urllib.parse
import urllib.request
import zipfile

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PACKAGE_ROOT/'provenance/data_sources.json'
CHUNK = 1024*1024


class DataIntegrityError(ValueError):
    """Incomplete/wrong-version bytes must not be published as usable data."""


def load_manifest(path=MANIFEST_PATH):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def required_files(dataset='all', manifest=None):
    if dataset not in ['all','gdsc','year']:
        raise ValueError('Dataset must be all, gdsc or year')
    manifest=manifest or load_manifest()
    return {key:spec for key,spec in manifest['files'].items()
            if dataset=='all' or spec['dataset']==dataset}


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(CHUNK),b''):digest.update(chunk)
    return digest.hexdigest()


def _target(root,spec):
    root=Path(root).expanduser().resolve()
    target=(root/spec['path']).resolve()
    if not target.is_relative_to(root/'Data'):
        raise ValueError('Data destination must stay in ROOT/Data')
    return target


def inspect_file(path,spec):
    path=Path(path).expanduser().resolve()
    result={'path':str(path),'expected_bytes':spec['bytes'],'expected_sha256':spec['sha256']}
    if not path.is_file():return {**result,'status':'missing','valid':False}
    size=path.stat().st_size
    if size!=spec['bytes']:
        return {**result,'status':'size_mismatch','valid':False,'actual_bytes':size}
    actual=sha256(path)
    valid=actual==spec['sha256']
    return {**result,'status':'verified' if valid else 'sha256_mismatch','valid':valid,
            'actual_bytes':size,'actual_sha256':actual}


def _verify(path,spec):
    result=inspect_file(path,spec)
    if not result['valid']:
        raise DataIntegrityError(json.dumps(result,ensure_ascii=False))
    return result


def check_split(root=PACKAGE_ROOT,manifest=None):
    manifest=manifest or load_manifest();spec=manifest['frozen_split']
    result=inspect_file(Path(root)/spec['path'],spec)
    if not result['valid']:return result
    split=json.loads(Path(result['path']).read_text(encoding='utf-8'))
    ids=split['matched_ids'];train=split['train_ids'];test=split['test_ids']
    valid=(split['drug_id']==spec['drug_id'] and len(ids)==spec['matched_cells']
           and len(train)==spec['training_cells'] and len(test)==spec['test_cells']
           and len(set(ids))==len(ids) and len(set(train))==len(train)
           and len(set(test))==len(test) and not set(train)&set(test)
           and set(train)|set(test)==set(ids))
    return {**result,'valid':valid,'status':'verified' if valid else 'split_partition_mismatch',
            'matched_cells':len(ids),'training_cells':len(train),'test_cells':len(test)}


def _overrides(files):
    overrides={}
    for value in files or []:
        key,separator,path=value.partition('=')
        if not separator or key not in ['expression','response','year','year_archive'] or not path:
            raise ValueError('--file requires expression=PATH, response=PATH, year=PATH or year_archive=PATH')
        if key in overrides:raise ValueError(f'Duplicate --file key: {key}')
        overrides[key]=Path(path).expanduser().resolve()
    return overrides


def check_data(root=PACKAGE_ROOT,dataset='all',files=None,manifest=None):
    manifest=manifest or load_manifest();overrides=_overrides(files)
    checks={}
    for key,spec in required_files(dataset,manifest).items():
        checks[key]=inspect_file(overrides.get(key,_target(root,spec)),spec)
    if 'year_archive' in overrides:
        checks['year_archive']=inspect_file(overrides['year_archive'],manifest['files']['year']['archive'])
    split=check_split(root,manifest) if dataset in ['all','gdsc'] else None
    return {'action':'check','dataset':dataset,'root':str(Path(root).resolve()),'files':checks,
            'frozen_split':split,'passed':all(x['valid'] for x in checks.values()) and (split is None or split['valid'])}


class _HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        if urllib.parse.urlsplit(newurl).scheme!='https':
            raise ValueError('Refusing an HTTPS download redirect to a non-HTTPS URL')
        return super().redirect_request(request,fp,code,msg,headers,newurl)


def _open_https(url,timeout):
    if urllib.parse.urlsplit(url).scheme!='https':raise ValueError('Only HTTPS source URLs are accepted')
    opener=urllib.request.build_opener(_HTTPSRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    request=urllib.request.Request(url,headers={'User-Agent':'Repro1026-Lite-Data/1.0','Accept-Encoding':'identity'})
    return opener.open(request,timeout=timeout)


def _publish(part,target):
    # A same-directory hard link atomically refuses an existing target on Windows and POSIX.
    # If unsupported by the filesystem, leave the verified .part for manual installation.
    os.link(part,target)
    part.unlink()


def _write_part(target,spec,source_factory):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():return _verify(target,spec)
    part=target.with_name(target.name+'.part')
    digest=hashlib.sha256();count=0;last=time.monotonic()
    # Exclusive creation refuses both concurrent writers and leftovers from a failed transfer.
    with part.open('xb') as output:
        with source_factory() as source:
            for chunk in iter(lambda:source.read(CHUNK),b''):
                output.write(chunk);digest.update(chunk);count+=len(chunk)
                if count>spec['bytes']:raise DataIntegrityError('Transfer exceeds the frozen byte count; .part retained')
                if time.monotonic()-last>15:
                    print(f'{target.name}: {count}/{spec["bytes"]} bytes',file=sys.stderr,flush=True);last=time.monotonic()
        output.flush();os.fsync(output.fileno())
    if count!=spec['bytes'] or digest.hexdigest()!=spec['sha256']:
        raise DataIntegrityError(f'Wrong version/incomplete bytes for {target.name}; .part retained: {count} bytes, SHA256 {digest.hexdigest()}')
    _publish(part,target)
    return {'path':str(target.resolve()),'status':'verified','valid':True,
            'actual_bytes':count,'actual_sha256':digest.hexdigest()}


def _obtain(target,spec,local=None,timeout=90):
    if target.exists():return _verify(target,spec)
    if local is not None:
        local=Path(local);_verify(local,spec)
        return _write_part(target,spec,lambda:local.open('rb'))
    return _write_part(target,spec,lambda:_open_https(spec['url'],timeout))


def download_data(root=PACKAGE_ROOT,dataset='all',files=None,timeout=90,manifest=None):
    manifest=manifest or load_manifest();overrides=_overrides(files);records={}
    if dataset in ['all','gdsc']:
        split=check_split(root,manifest)
        if not split['valid']:raise DataIntegrityError('Frozen split is missing or invalid: '+json.dumps(split))
    for key,spec in required_files(dataset,manifest).items():
        target=_target(root,spec)
        if target.exists():records[key]=_verify(target,spec);continue
        if key in overrides or 'archive' not in spec:
            records[key]=_obtain(target,spec,overrides.get(key),timeout);continue
        archive=spec['archive'];archive_path=overrides.get('year_archive',_target(root,archive))
        if 'year_archive' in overrides:_verify(archive_path,archive)
        else:records['year_archive']=_obtain(archive_path,archive,timeout=timeout)
        with zipfile.ZipFile(archive_path) as zipped:
            info=zipped.getinfo(archive['member'])
            if info.is_dir() or info.file_size!=spec['bytes']:
                raise DataIntegrityError('Unexpected frozen ZIP member size/type')
            # Read exactly one named member; never extract arbitrary archive paths.
            records[key]=_write_part(target,spec,lambda:zipped.open(info,'r'))
    result=check_data(root,dataset,manifest=manifest)
    result.update(action='download',operations=records)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['download','check'])
    parser.add_argument('--dataset',choices=['all','gdsc','year'],default='all')
    parser.add_argument('--root',type=Path,default=PACKAGE_ROOT,help='Package/data root; canonical files live under ROOT/Data')
    parser.add_argument('--file',action='append',default=[],metavar='KEY=PATH',help='Check a manual path, or import its verified bytes during download; year_archive accepts the official ZIP')
    parser.add_argument('--timeout',type=float,default=90.)
    args=parser.parse_args(argv)
    if args.timeout<=0:parser.error('--timeout must be positive')
    try:
        result=(download_data(args.root,args.dataset,args.file,args.timeout) if args.action=='download'
                else check_data(args.root,args.dataset,args.file))
    except (OSError,ValueError,zipfile.BadZipFile,KeyError,http.client.HTTPException,EOFError) as error:
        print(json.dumps({'action':args.action,'passed':False,'error':str(error),
                          'existing_targets_unchanged':True,'partial_files_preserved':True},ensure_ascii=False,indent=2))
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
