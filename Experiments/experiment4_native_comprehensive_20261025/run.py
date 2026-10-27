"""Explicit native IV commands; never automatically starts another experiment."""
from pathlib import Path
import argparse,importlib.util,subprocess,sys
HERE=Path(__file__).resolve().parent
if importlib.util.find_spec('numba') is None:
    fallback=Path('D:/anaconda1/python.exe')
    if not fallback.is_file():raise RuntimeError('Install requirements.txt including numba in this interpreter.')
    if __name__=='__main__':sys.exit(subprocess.call([str(fallback),'-B',str(Path(__file__).resolve()),*sys.argv[1:]]))
sys.path.insert(0,str(HERE/'src'))
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['pilot','freeze','formal','analyze','verify','paper','render','package'])
    parser.add_argument('--output');parser.add_argument('--workers',type=int,default=6)
    args=parser.parse_args()
    if args.command in ['pilot','freeze']:
        from native_exp4 import pilot as module
    elif args.command=='formal':
        from native_exp4 import formal as module
    elif args.command=='analyze':
        from native_exp4 import analysis as module
    elif args.command=='verify':
        from native_exp4 import verification as module
    else:
        from native_exp4 import delivery as module
    module.main(args)
if __name__=='__main__':main()
