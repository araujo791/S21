#!/usr/bin/env python3
"""Portable launcher. Hardware is touched only by explicit, elevated worker jobs."""
import argparse
import sys
from pathlib import Path


def main():
    if sys.version_info < (3, 10):
        print('Convenant BIOS Tools requer Python 3.10 ou posterior.')
        return 1
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--data', type=Path)
    args = parser.parse_args()
    if args.worker:
        from convenant.hardware import worker
        return worker(args.worker)
    from convenant.server import serve
    return serve(args)


if __name__ == '__main__':
    raise SystemExit(main())
