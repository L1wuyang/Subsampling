"""Run III/IV into a new output directory, without historical paper delivery.

Examples (from the extracted package root)::
    python -m repro1026.exp34 --experiment 3 --mode smoke --output runs/III_smoke
    python -m repro1026.exp34 --experiment 4 --mode formal --output runs/IV_formal

Formal mode runs the unchanged historical scientific entry point and its frozen
pilot gates. Smoke mode explicitly reduces only dimensions/replication and is
never represented as reproducing the paper's formal statistical conclusions.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = {
    3: 'experiment3_native_comprehensive_20261024',
    4: 'experiment4_native_comprehensive_20261025',
}


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf8')


def fresh_directory(path: Path, *, create: bool = True) -> Path:
    path = path.expanduser().resolve()
    for name in ['Experiments','Data','Paper_Versions','provenance','repro1026']:
        protected=ROOT/name
        if path==protected or path.is_relative_to(protected):
            raise ValueError(f'Output is inside protected package input: {path}')
    if path==ROOT or ROOT.is_relative_to(path):
        raise ValueError('Output cannot replace the package or one of its parents')
    if path.exists():
        if not path.is_dir() or any(path.iterdir()):
            raise FileExistsError(f'Output must be new or empty: {path}')
        if not create:
            path.rmdir()  # Only a verified empty directory; formal mkdir owns it.
    elif create:
        path.mkdir(parents=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def archive(experiment: int) -> Path:
    folder = ROOT/'Experiments'/EXPERIMENTS[experiment]
    if not (folder/'formal_protocol.json').is_file():
        raise FileNotFoundError(f'Missing packaged scientific source: {folder}')
    return folder


def library(folder: Path, experiment: int):
    sys.path.insert(0, str(folder/'src'))
    return importlib.import_module(f'native_exp{experiment}.common')


def execute_formal(experiment: int, output: Path, workers: int):
    """Invoke unchanged kernels, normalizing historical manifest separators only."""
    folder = archive(experiment)
    common = library(folder, experiment)
    formal = importlib.import_module(f'native_exp{experiment}.formal')
    original_sha = common.sha
    formal.sha = lambda path: original_sha(Path(str(path).replace('\\', '/')))
    formal.main(SimpleNamespace(output=str(output), workers=workers))


def source_snapshot(folder: Path, output: Path) -> dict:
    files = [folder/'run.py', folder/'formal_protocol.json', folder/'requirements.txt']
    files.extend(sorted((folder/'src').rglob('*.py')))
    manifest = {}
    for path in files:
        relative = path.relative_to(folder)
        destination = output/'source_snapshot'/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        manifest[relative.as_posix()] = sha(path)
    write_json(output/'frozen_sources.json', manifest)
    return manifest


def smoke_protocol(original: dict, experiment: int) -> dict:
    config = copy.deepcopy(original)
    config.update(dimension=6, objects=48, data_ids=[1],
                  run_mode='smoke', formal_paper_replication=False,
                  smoke_note='Same actual algorithms; deliberately smaller data, budgets and repeats.')
    config['main'] = dict(data_ids=[1], budgets=[8,32], repetitions=3)
    config['robustness'] = dict(data_ids=[], budgets=[8,32], repetitions=3)
    if experiment == 3:
        config['sensitivity'] = dict(data_ids=[], budgets=[8], repetitions=1, c_values=[.5,2.])
        config['zero_response'] = dict(data_ids=[1], budgets=[8], repetitions=1)
        config['replication_counts'] = dict(main=72, sensitivity=0, zero_response=12)
    else:
        config['tails'] = dict(data_ids=[1], budgets=[6], repetitions=3,
                               methods=['HBF','Nesterov','SOAR'], stream=1)
        config['zero_response'] = dict(data_ids=[1], budgets=[8], repetitions=1, stream=2)
    return config


def smoke_III(folder: Path, output: Path, config: dict) -> dict:
    common = library(folder,3)
    formal = importlib.import_module('native_exp3.formal')
    import numpy as np
    import pandas as pd
    (output/'data').mkdir()
    manifest = {}
    for direction in config['directions']:
        path=output/'data'/f'{direction}_01.npz'
        np.savez_compressed(path, **common.base(config['data_seed'],direction,1,config['dimension'],config['objects']))
        manifest[path.relative_to(output).as_posix()] = sha(path)
    write_json(output/'data_manifest.json',manifest)
    completions=[]
    for direction in config['directions']:
        for arm in formal.arms_for(config,1):
            completions.append(formal.run_arm(output,config,direction,1,arm))
    for filename in ['results','full_reference','costs']:
        for sensitivity in [False,True]:
            frames=[]
            for q in completions:
                if (q['arm']!='main')==sensitivity:
                    frames.append(pd.read_csv(output/f"{q['direction']}_01"/q['arm']/(filename+'.csv')))
            if frames:
                pd.concat(frames,ignore_index=True).to_csv(output/(('sensitivity_' if sensitivity else '')+filename+'.csv'),index=False)
    total=sum(q['rows'] for q in completions)
    assert total==84
    return dict(completed=True,total_records=total,completions=completions,
                formal_paper_replication=False,run_mode='smoke')


def smoke_IV(folder: Path, output: Path, config: dict) -> dict:
    common=library(folder,4)
    kernel=importlib.import_module('native_exp4.kernel')
    import numpy as np
    parameters=[];data_manifest={};records=0;chunks=0
    for direction in config['directions']:
        data=common.dataset(config['data_seed'],direction,1,d=config['dimension'],N=config['objects'])
        setup=common.full_setup(data)
        destination=output/f'{direction}_01'
        destination.mkdir()
        np.savez_compressed(destination/'data.npz',**{k:v for k,v in data.items() if k!='direction'})
        data_manifest[(destination/'data.npz').relative_to(output).as_posix()]=sha(destination/'data.npz')
        common.save(destination/'setup.json',setup)
        for tag,stream,zero in [('main',0,False),('tails',1,False),('zero_response',2,True)]:
            spec=config[tag]
            methods=spec.get('methods',common.METHODS)
            arm=destination/tag;arm.mkdir()
            actual={**data,'y':np.zeros_like(data['y'])} if zero else data
            for N in spec['budgets']:
                counts=common.counts_for(config['sampling_seed'],direction,1,N,spec['repetitions'],stream,N=config['objects'])
                states={m:[] for m in methods};ls_states=[];ranks=[];reduction=[];rows=[]
                paths={m:common.parameters(setup,N,m) for m in methods}
                parameters.extend(dict(direction=direction,data_id=1,arm=tag,**p) for p in paths.values())
                for rep,count in enumerate(counts):
                    M,rhs,Z,ix,weights=common.sketch(actual,count)
                    ls,rank=common.ls_reference(actual,rhs,Z,ix,weights)
                    reduced=kernel.reduce(M)
                    ls_states.append(ls);ranks.append(rank);reduction.append([reduced[3],reduced[4]])
                    for method in methods:
                        p=paths[method];tick=time.perf_counter();state=kernel.solve(M,rhs,p,reduced)
                        seconds=time.perf_counter()-tick;finite=np.isfinite(state).all()
                        states[method].append(state)
                        values=common.metrics(actual,state,ls,N) if finite else {k:np.nan for k in common.metrics(actual,np.zeros_like(state),ls,N)}
                        rows.append(dict(direction=direction,data_id=1,arm=tag,budget=N,rep=rep,method=method,
                                         status='zero_response' if zero and finite else 'complete' if finite else 'numerical_failure',
                                         rank=rank,unique_objects=len(ix),spike_draws=int(count@actual['spike_mask']),
                                         executed_steps=p['steps'],seconds=seconds,**values))
                stem=arm/f'r{N}_c0000'
                np.savez_compressed(stem.with_suffix('.npz'),counts=counts,ls_state=np.array(ls_states),rank=np.array(ranks),
                                    reduction_errors=np.array(reduction),**{m+'_state':np.array(v) for m,v in states.items()})
                common.write(stem.with_suffix('.csv'),rows)
                common.save(stem.with_suffix('.json'),dict(completed=True,records=len(rows),rep_start=0,rep_stop=len(counts)))
                records+=len(rows);chunks+=1
    common.write(output/'parameters.csv',parameters)
    write_json(output/'data_manifest.json',data_manifest)
    assert records==102
    return dict(completed=True,records=records,chunks=chunks,formal_paper_replication=False,run_mode='smoke')


def run(experiment: int, output: Path, mode: str='smoke', workers: int=1) -> Path:
    folder=archive(experiment)
    original=json.loads((folder/'formal_protocol.json').read_text(encoding='utf8'))
    tick=time.perf_counter()
    if mode=='formal':
        output=fresh_directory(output,create=False)
        env=os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE']='1'
        # Numba's cache locator may create its directory during module import,
        # before the historical formal runner creates the new output itself.
        env['NUMBA_CACHE_DIR']=str(output.parent/'.repro1026_numba_cache'/output.name)
        command=[sys.executable,'-B','-m','repro1026.exp34','--execute-formal',
                 '--experiment',str(experiment),'--output',str(output),'--workers',str(workers)]
        subprocess.run(command,env=env,check=True)
        write_json(output/'adapter_run.json',dict(experiment=experiment,mode=mode,completed=True,
            original_protocol_sha256=sha(folder/'formal_protocol.json'),scientific_parameters_changed=False,
            historical_paper_delivery_called=False,seconds=time.perf_counter()-tick))
    else:
        output=fresh_directory(output)
        os.environ['NUMBA_CACHE_DIR']=str(output/'numba_cache')
        for name in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS']:
            os.environ[name]='1'
        os.environ['PYTHONDONTWRITEBYTECODE']='1'
        config=smoke_protocol(original,experiment)
        sources=source_snapshot(folder,output)
        write_json(output/'protocol.json',config)
        execution=(smoke_III if experiment==3 else smoke_IV)(folder,output,config)
        execution.update(seconds=time.perf_counter()-tick,historical_paper_delivery_called=False,
                         original_protocol_sha256=sha(folder/'formal_protocol.json'))
        assert all(sha(folder/p)==digest for p,digest in sources.items())
        write_json(output/'execution.json',execution)
        write_json(output/'adapter_run.json',dict(experiment=experiment,mode=mode,completed=True,
            formal_paper_replication=False,scientific_algorithms_changed=False,smoke_dimensions_changed=True,
            historical_paper_delivery_called=False,seconds=execution['seconds']))
    print(json.dumps(dict(completed=True,experiment=experiment,mode=mode,output=str(output)),ensure_ascii=False),flush=True)
    return output


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment',type=int,choices=[3,4],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',choices=['smoke','formal'],default='smoke')
    parser.add_argument('--workers',type=int,default=1)
    parser.add_argument('--execute-formal', action='store_true', help=argparse.SUPPRESS)
    args=parser.parse_args(argv)
    if args.workers<1:
        parser.error('--workers must be positive')
    if args.execute_formal:
        execute_formal(args.experiment,args.output,args.workers)
    else:
        run(args.experiment,args.output,args.mode,args.workers)


if __name__=='__main__':
    main()
