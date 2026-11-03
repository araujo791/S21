"""Package the native launcher with the previously verified Python/Qt runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import zipfile


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--runtime-package',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    # Exact runtime built and verified during this conversation; not a random download.
    expected='e37fef0885f526a741de34ad4588525c5e922db35d631757d62e97894698955d'
    assert digest(args.runtime_package.read_bytes())==expected,'Unexpected runtime package.'
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    stage=out/'Covenant-Graphics-Studio-0.1.0-Windows-x64'
    stage.mkdir(exist_ok=False)
    prefix='Convenant-BIOS-Tools-0.2.0-Windows/'
    notices=('Python-LICENSE.txt','Qt-GPL-3.0-only.txt','Qt-LGPL-3.0-only.txt')
    with zipfile.ZipFile(args.runtime_package) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.startswith(prefix):continue
            rel=Path(info.filename[len(prefix):])
            if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe runtime member.')
            if rel.as_posix().startswith('runtime/windows/') or (len(rel.parts)==2 and rel.parts[0]=='licenses' and rel.name in notices):
                target=stage/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(info))
    files=[root/'covenant_graphics_studio.py',root/'README.md',root/'requirements.txt']
    for folder in ('covenant_studio','assets','native','scripts','tests'):
        files += [f for f in (root/folder).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc']
    if (root/'docs/validation.json').is_file():files.append(root/'docs/validation.json')
    if (root/'docs/janela.png').is_file():files.append(root/'docs/janela.png')
    for f in files:
        target=stage/f.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
    shutil.copyfile(root/'build/Covenant-Graphics-Studio.exe',stage/'Covenant-Graphics-Studio.exe')
    exe=(stage/'Covenant-Graphics-Studio.exe').read_bytes();pe=struct.unpack_from('<I',exe,60)[0]
    assert exe[pe:pe+4]==b'PE\0\0' and struct.unpack_from('<H',exe,pe+4)[0]==0x8664
    assert struct.unpack_from('<H',exe,pe+24+68)[0]==2,'Launcher must be Windows GUI subsystem.'
    (stage/'licenses/Qt-SOURCES-AND-NOTICES.md').write_text('''# Qt 6.8.3 — bibliotecas compartilhadas

Este aplicativo utiliza PySide6 Essentials/Shiboken 6.8.3 e bibliotecas Qt compartilhadas. As bibliotecas continuam separadas dos fontes do aplicativo e podem ser substituídas por versões compatíveis.

Textos LGPL-3.0 e GPL-3.0 estão nesta pasta. Código-fonte correspondente do Qt: https://code.qt.io/cgit/qt/ e https://download.qt.io/archive/qt/6.8/6.8.3/ . PySide/Shiboken: https://code.qt.io/cgit/pyside/pyside-setup.git/tag/?h=v6.8.3 .

Os fontes Python/C deste aplicativo estão no próprio pacote. O código do aplicativo não foi ligado estaticamente às bibliotecas Qt. O Python possui licença própria incluída.
''')
    entries=[]
    for f in sorted(stage.rglob('*')):
        if f.is_file():entries.append({'file':f.relative_to(stage).as_posix(),'size':f.stat().st_size,'sha256':digest(f.read_bytes())})
    manifest={'application':'Covenant Graphics Studio','version':'0.1.0','target':'Windows x86-64 GUI',
              'browser_used':False,'server_required':False,'python_install_required':False,
              'firmware_compiler_implemented':False,'flashable_rom_included':False,
              'windows_native_execution_tested':False,'files':entries}
    (stage/'BUNDLE-MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    archive=out/(stage.name+'.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(stage.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(stage.parent).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for item in entries:
            assert digest(z.read(stage.name+'/'+item['file']))==item['sha256']
        assert not any(n.lower().endswith(('.rom','.ffs')) for n in z.namelist())
    source=out/'Covenant-Graphics-Studio-0.1.0-Fontes.zip'
    with zipfile.ZipFile(source,'x',zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(f,'Covenant-Graphics-Studio/'+f.relative_to(root).as_posix())
    (out/'SHA256SUMS.txt').write_text(''.join(digest(f.read_bytes())+'  '+f.name+'\n' for f in (archive,source)))
    print(json.dumps({'windows_zip':str(archive),'size':archive.stat().st_size,'sha256':digest(archive.read_bytes()),
                      'source_zip':str(source),'verified_files':len(entries)},indent=2))


if __name__=='__main__':main()
