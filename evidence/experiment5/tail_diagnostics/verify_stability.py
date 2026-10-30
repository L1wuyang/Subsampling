"""Check the numerical premises of the archived HBF/SOAR stability screen.

This checks supplied scalar support bounds, not regenerated HBF/SOAR probabilities.
"""
import argparse
import json
import math
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path(__file__).parent/'reference/hbf_soar_values.json')
    args=parser.parse_args()
    data=json.loads(args.input.read_text(encoding='utf-8'))
    checks=[]
    for row in data['rows']:
        q=row['dt']**2*row['B']
        if not math.isclose(q,row['h2_B'],rel_tol=1e-12,abs_tol=1e-14):
            raise ValueError('h^2 B disagrees with its supplied factors')
        if row['method']=='HBF':
            a=row['dt']*row['eta']
            if not (0<a<=.01 and 0<=q<=2):
                raise ValueError('HBF sufficient interval premises fail')
            # For the complex-root branch, |R|^2-1 <= a*(-5/6+7*a/12+a^3/24).
            margin=a*(-5/6+7*a/12+a**3/24)
            if not margin<0:
                raise ValueError('HBF sufficient strict bound fails')
        else:
            if not 0<=q<=8:
                raise ValueError('SOAR imaginary-axis stability premise fails')
        checks.append(dict(dataset=row['dataset'],method=row['method'],rule=row['rule'],h2_B=q,passed=True))
    print(json.dumps(dict(passed=True,checks=checks,scope=data['scope'],
        qualification='Conditional on the archived support-bound inputs and their stated provenance. This does not certify Monte Carlo means, rankings, complete native trajectories, or all tail mechanisms.'),indent=2))


if __name__=='__main__':
    main()
