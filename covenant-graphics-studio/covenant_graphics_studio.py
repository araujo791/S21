import argparse
import sys
import traceback
import tempfile
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
        report=traceback.format_exc()
        error_path=None
        for folder in (Path(__file__).resolve().parent,Path(tempfile.gettempdir())):
            try:
                error_path=folder/'Covenant-Graphics-Studio-erro.txt'
                error_path.write_text(report,encoding='utf-8');break
            except OSError:
                error_path=None
        message=str(exc)+(f'\n\nDetalhes gravados em:\n{error_path}' if error_path else '')
        if sys.platform=='win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,message,'Covenant Graphics Studio',0x10)
        else:
            traceback.print_exc()
        raise SystemExit(1)
