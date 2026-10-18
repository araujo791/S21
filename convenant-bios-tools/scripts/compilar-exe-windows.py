#!/usr/bin/env python3
"""Cross-compile the native Windows entry point with the pinned Zig compiler."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cache',type=Path,required=True)
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env['ZIG_GLOBAL_CACHE_DIR']=str(args.cache.resolve()/'global');env['ZIG_LOCAL_CACHE_DIR']=str(args.cache.resolve()/'local')
    subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86_64-windows-gnu','-Os','-s','-municode','-Wl,--subsystem,windows',str(ROOT/'native/launcher-windows.c'),'-o',str(args.output.resolve()),'-luser32'],env=env,check=True)
    if args.output.read_bytes()[:2]!=b'MZ':raise ValueError('PE Windows não produzido.')
    print(args.output.resolve())


if __name__=='__main__':main()
