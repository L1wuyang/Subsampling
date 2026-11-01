"""Small independent native-state/tangent and coordinate-split checks."""
import argparse
import json
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[1]/'Experiments/experiment5_native_realdata_20261025/src'))
from native_exp5.common import np,la
from native_exp5 import kernel,column_reference,row_reference


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();rng=np.random.default_rng(202610310500);checks=[]
    for tag in ['gdsc','year']:
        X=rng.normal(size=(7,11) if tag=='gdsc' else (19,7));y=rng.normal(size=len(X))
        Z=X if tag=='gdsc' else X.T;M=Z@Z.T;rhs=y if tag=='gdsc' else X.T@y
        C=la.qr(X.T,mode='economic')[1] if tag=='gdsc' else np.eye(len(M))
        L=Z.shape[1]*np.max(np.sum(Z*Z,axis=0))/.01
        for method in ['Landweber','Showalter','Nesterov']:
            p=kernel.parameters(method,np.trace(M)/len(M),L)
            target,J=kernel.influences(M,rhs,p,Z,None if tag=='gdsc' else y,C,block=127,qbatch=3)
            blocks=[]
            for lo in range(0,len(C),3):
                t,j=kernel.influences(M,rhs,p,Z,None if tag=='gdsc' else y,C[lo:lo+3],block=127,qbatch=min(3,len(C)-lo))
                assert np.allclose(t,target,rtol=1e-13,atol=1e-14)
                blocks.append(j)
            diff=np.linalg.norm(np.vstack(blocks)-J)/max(1,np.linalg.norm(J));assert diff<1e-12
            ref,jref=(column_reference.full(X,M,y,p) if tag=='gdsc' else row_reference.full(X,M,y,p))
            stateerr=np.linalg.norm(ref-target)/max(1,np.linalg.norm(ref))
            jerr=np.linalg.norm(C@jref-J)/max(1,np.linalg.norm(J))
            assert stateerr<2e-10 and jerr<3e-9
            checks.append(dict(dataset=tag,method=method,steps=p['steps'],coordinate_split_error=float(diff),
                               dense_state_error=float(stateerr),dense_derivative_error=float(jerr)))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(dict(passed=True,checks=checks),indent=2),encoding='utf-8')
    print('PILOT_PASSED',len(checks),flush=True)


if __name__=='__main__':main()
