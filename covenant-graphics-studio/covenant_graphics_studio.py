import argparse
import sys
import traceback
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description='Covenant Graphics Studio — aplicativo nativo de projeto e vínculos.')
    parser.add_argument('--smoke-bios',help=argparse.SUPPRESS)
    parser.add_argument('--smoke-report',help=argparse.SUPPRESS)
    parser.add_argument('--smoke-screenshot',help=argparse.SUPPRESS)
    args=parser.parse_args()
    from covenant_studio.native import start
    return start(args)


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        if sys.platform=='win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,str(exc),'Covenant Graphics Studio',0x10)
        else:
            traceback.print_exc()
        raise SystemExit(1)
