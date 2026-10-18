#!/usr/bin/env python3
"""Build a portable ZIP from pinned official runtimes, never private firmware."""
import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    'python': ('0eb85c2dfccccf1b17352de4c397f69194035b7d37149eacc16f1147d93de3b8',
               'https://api.nuget.org/v3-flatcontainer/python/3.12.10/python.3.12.10.nupkg'),
    'uefi_windows': ('20ff18208913d32c99e3b002717abeddaa3b6509ac62e6699e462b0f533be646',
                     'https://github.com/LongSoft/UEFITool/releases/download/A75/UEFIExtract_NE_A75_win64.zip'),
    'uefi_linux': ('5ee05d0da0c235626de67959d6cd97767e0d7ac67d42c8839e5972e8c23fd5a5',
                   'https://github.com/LongSoft/UEFITool/releases/download/A75/UEFIExtract_NE_A75_x64_linux.zip'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(args):
    for key, (expected, _url) in PINS.items():
        if digest(getattr(args, key)) != expected:
            raise ValueError('Hash inesperado no componente ' + key)
    if args.output.exists():
        raise ValueError('A saída já existe. Escolha outro nome para preservar a entrega anterior.')
    with tempfile.TemporaryDirectory(prefix='convenant-package-') as tmp:
        folder = Path(tmp) / 'Convenant-BIOS-Tools-0.1.0'
        folder.mkdir()
        sources = ['convenant_bios_tools.py', 'Abrir-Convenant-BIOS-Tools.bat',
                   'abrir-convenant-bios-tools.sh', 'studio/__init__.py', 'studio/firmware.py',
                   'studio/platform_update.py', 'scripts/atualizar-microcodigo.py',
                   'scripts/empacotar-convenant.py', 'scripts/verificar-interface-convenant.py',
                   'tests/test_convenant.py', 'docs/convenant-bios-tools.md',
                   'docs/evidencias/convenant-validation.json']
        sources += [str(p.relative_to(ROOT)) for p in (ROOT / 'convenant').rglob('*')
                    if p.is_file() and p.suffix in ('.py', '.html', '.css', '.js')]
        for name in sources:
            dest = folder / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        (folder / 'abrir-convenant-bios-tools.sh').chmod(0o755)
        bat = folder / 'Abrir-Convenant-BIOS-Tools.bat'
        bat.write_bytes(bat.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        shutil.copyfile(ROOT / 'docs/convenant-bios-tools.md', folder / 'LEIA-ME.md')
        (folder / 'tools/FPT').mkdir(parents=True)
        (folder / 'tools/FPT/COLOQUE-SUA-PASTA-FPT-AQUI.txt').write_text(
            'Copie a pasta completa do seu FPT compatível aqui, incluindo fptw64.exe e arquivos auxiliares.\n'
            'O pacote não inclui nem baixa executáveis Intel.\n', encoding='utf-8')
        (folder / 'licenses').mkdir()
        shutil.copyfile(args.uefi_license, folder / 'licenses/UEFITool-LICENSE.md')
        with zipfile.ZipFile(args.python) as archive:
            for name in archive.namelist():
                if name.startswith('tools/') and not name.endswith('/'):
                    relative = Path(name.removeprefix('tools/'))
                    if '..' in relative.parts:
                        raise ValueError('Entrada inválida no pacote Python.')
                    dest = folder / 'runtime/windows' / relative
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(archive.read(name))
            (folder / 'licenses/Python-LICENSE.txt').write_bytes(archive.read('tools/LICENSE.txt'))
        for key, system, name in (('uefi_windows','windows','UEFIExtract.exe'), ('uefi_linux','linux','uefiextract')):
            with zipfile.ZipFile(getattr(args, key)) as archive:
                dest = folder / 'tools/uefi' / system / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.read(name)); dest.chmod(0o755)
        manifest = {'name':'Convenant BIOS Tools', 'version':'0.1.0',
                    'components':{k:{'sha256':v[0],'source':v[1]} for k,v in PINS.items()},
                    'private_firmware_included':False, 'intel_fpt_included':False,
                    'files':{str(p.relative_to(folder)).replace('\\','/'):digest(p)
                             for p in sorted(folder.rglob('*')) if p.is_file()}}
        (folder / 'manifesto-pacote.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(args.output,'x',zipfile.ZIP_DEFLATED,compresslevel=7) as archive:
            for p in sorted(folder.rglob('*')):
                if p.is_file():
                    archive.write(p,arcname=str(p.relative_to(folder.parent)))
        with zipfile.ZipFile(args.output) as archive:
            if archive.testzip() is not None:
                raise ValueError('Arquivo ZIP não passou na verificação.')
    print(json.dumps({'output':str(args.output.resolve()),'size':args.output.stat().st_size,'sha256':digest(args.output)},indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('python','uefi-windows','uefi-linux','uefi-license','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    build(args)


if __name__=='__main__':
    main()
