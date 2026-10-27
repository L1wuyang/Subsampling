import os
for key in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS']:
    os.environ[key]='1'
from pathlib import Path
import hashlib,json,math,time
import numpy as np
import scipy.linalg as la
HERE=Path(__file__).resolve().parents[2]
ROOT=HERE.parents[1]
METHODS=['Ridge','Landweber','Showalter','HBF','Nesterov','SOAR']
RULES=['UNI','NORM','LEV','OPT']
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def guard():
    def blocked(*a,**kw):raise AssertionError('Spectral trajectory shortcut prohibited')
    for n in ['eig','eigh','eigvals','eigvalsh','svd','matrix_power']:setattr(np.linalg,n,blocked)
    for n in ['eig','eigh','eigvals','eigvalsh','svd','svdvals','expm','funm','fractional_matrix_power']:setattr(la,n,blocked)
