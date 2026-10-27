"""Explicit commands; inspection/analysis never starts another numerical run."""
from pathlib import Path
import sys
import argparse
sys.path.insert(0, str(Path(__file__).resolve().parent/'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['pilot', 'freeze', 'formal', 'analyze', 'verify', 'paper', 'render', 'package'])
    parser.add_argument('--output', default=None, help='New output directory for pilot/formal; existing directory for analysis')
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    if args.command in ['pilot', 'freeze']:
        from native_exp3.pilot import main as execute
    elif args.command == 'formal':
        from native_exp3.formal import main as execute
    elif args.command == 'analyze':
        from native_exp3.analysis import main as execute
    elif args.command == 'verify':
        from native_exp3.verification import main as execute
    else:
        from native_exp3.delivery import main as execute
    execute(args)


if __name__ == '__main__': main()
