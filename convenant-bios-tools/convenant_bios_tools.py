#!/usr/bin/env python3
"""Portable launcher. Hardware is touched only by explicit, elevated worker jobs."""
import argparse
import sys
import os
import traceback
from pathlib import Path


def main():
    if sys.version_info < (3, 10):
        print('Convenant BIOS Tools requer Python 3.10 ou posterior.')
        return 1
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--smoke-output', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--smoke-input', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        from convenant.hardware import worker
        return worker(args.worker)
    from convenant.native import start
    return start(args)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        error = traceback.format_exc()
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, 'Não foi possível iniciar. Extraia a pasta completa do aplicativo.\n\n' + error[-3500:], 'Convenant BIOS Tools', 0x10)
        elif sys.stderr:
            sys.stderr.write(error)
        raise SystemExit(1)
