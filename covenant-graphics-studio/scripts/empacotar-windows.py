"""Package the native launcher with the previously verified Python/Qt runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from covenant_studio import __version__


def pe_imports(data):
    if len(data)<64 or data[:2]!=b'MZ':raise ValueError('DLL sem cabeçalho DOS.')
    pe=struct.unpack_from('<I',data,60)[0]
    if pe+24>len(data) or data[pe:pe+4]!=b'PE\0\0':raise ValueError('DLL sem cabeçalho PE.')
    machine,count=struct.unpack_from('<HH',data,pe+4)
    if machine!=0x8664 or not 1<=count<=96:raise ValueError('DLL precisa ser Windows x64.')
    opt=pe+24;opt_size=struct.unpack_from('<H',data,pe+20)[0]
    if opt+opt_size+count*40>len(data) or struct.unpack_from('<H',data,opt)[0]!=0x20b:raise ValueError('PE32+ inválido.')
    def offset(rva,size):
        for i in range(count):
            vs,va,rs,raw=struct.unpack_from('<4I',data,opt+opt_size+i*40+8)
            if va<=rva and rva+size<=va+rs and raw+rva-va+size<=len(data):return raw+rva-va
        raise ValueError('RVA de importação fora dos limites.')
    imports=struct.unpack_from('<I',data,opt+112+8)[0]
    if not imports:return []
    result=[]
    for i in range(4096):
        p=offset(imports+20*i,20);row=struct.unpack_from('<5I',data,p)
        if not any(row):return result
        p=offset(row[3],1);end=data.find(b'\0',p,min(p+256,len(data)))
        if end<0:raise ValueError('Nome de DLL truncado.')
        result.append(data[p:end].decode('ascii'))
    raise ValueError('Quantidade de importações excedida.')


def check_jpeg_runtime(stage):
    rel=Path('runtime/windows/Lib/site-packages/PySide6/plugins/imageformats/qjpeg.dll')
    plugin=stage/rel
    if not plugin.is_file():raise ValueError('O pacote Windows está sem qjpeg.dll.')
    imports=pe_imports(plugin.read_bytes())
    files={p.name.casefold():p for p in (stage/'runtime/windows').rglob('*.dll')}
    checked=[]
    for name in imports:
        lower=name.casefold()
        if lower.startswith(('api-ms-','ext-ms-')) or lower in {'kernel32.dll','user32.dll','gdi32.dll','advapi32.dll','ole32.dll','shell32.dll'}:continue
        if lower not in files:raise ValueError('Dependência JPEG ausente: '+name)
        pe_imports(files[lower].read_bytes());checked.append(name)
    return {'plugin':rel.as_posix(),'sha256':digest(plugin.read_bytes()),'dependencies_verified':checked}


def install_jpeg_plugin(stage,wheel):
    expected='3c0fae5550aff69f2166f46476c36e0ef56ce73d84829eac4559770b0c034b07'
    if digest(wheel.read_bytes())!=expected:raise ValueError('Wheel PySide6 diferente da referência verificada.')
    with zipfile.ZipFile(wheel) as z:blob=z.read('PySide6/plugins/imageformats/qjpeg.dll')
    pe_imports(blob)
    target=stage/'runtime/windows/Lib/site-packages/PySide6/plugins/imageformats/qjpeg.dll'
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(blob)
    return check_jpeg_runtime(stage)

def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--runtime-package',type=Path,required=True)
    p.add_argument('--qt-wheel',type=Path,required=True,help='Wheel Windows x64 PySide6 Essentials 6.8.3, de hash fixado.')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    # Exact runtime built and verified during this conversation; not a random download.
    expected='e37fef0885f526a741de34ad4588525c5e922db35d631757d62e97894698955d'
    assert digest(args.runtime_package.read_bytes())==expected,'Unexpected runtime package.'
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    stage=out/f'Covenant-Graphics-Studio-{__version__}-Windows-x64'
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
    jpeg=install_jpeg_plugin(stage,args.qt_wheel)
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
    manifest={'application':'Covenant Graphics Studio','version':__version__,'target':'Windows x86-64 GUI',
              'browser_used':False,'server_required':False,'python_install_required':False,
              'firmware_compiler_implemented':False,'flashable_rom_included':False,
              'windows_native_execution_tested':False,'jpeg_runtime':jpeg,
              'png_fallback_images':len(json.loads((stage/'assets/fallback-png/catalogo.json').read_text())),
              'files':entries}
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
    source=out/f'Covenant-Graphics-Studio-{__version__}-Fontes.zip'
    with zipfile.ZipFile(source,'x',zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(f,'Covenant-Graphics-Studio/'+f.relative_to(root).as_posix())
    (out/'SHA256SUMS.txt').write_text(''.join(digest(f.read_bytes())+'  '+f.name+'\n' for f in (archive,source)))
    print(json.dumps({'windows_zip':str(archive),'size':archive.stat().st_size,'sha256':digest(archive.read_bytes()),
                      'source_zip':str(source),'verified_files':len(entries)},indent=2))


if __name__=='__main__':main()
