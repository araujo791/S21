#!/usr/bin/env python3
"""Package native desktop executables; no firmware or FPT is included."""
import argparse
import hashlib
import json
import shutil
import struct
import tempfile
import tarfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.2.0'
PINS={
    'python-3.12.10.nupkg':'0eb85c2dfccccf1b17352de4c397f69194035b7d37149eacc16f1147d93de3b8',
    'PySide6_Essentials-6.8.3-cp39-abi3-win_amd64.whl':'3c0fae5550aff69f2166f46476c36e0ef56ce73d84829eac4559770b0c034b07',
    'shiboken6-6.8.3-cp39-abi3-win_amd64.whl':'bca3a94513ce9242f7d4bbdca902072a1631888e0aa3a8711a52cc5dbe93588f',
    'UEFIExtract_NE_A75_win64.zip':'20ff18208913d32c99e3b002717abeddaa3b6509ac62e6699e462b0f533be646',
    'UEFIExtract_NE_A75_x64_linux.zip':'5ee05d0da0c235626de67959d6cd97767e0d7ac67d42c8839e5972e8c23fd5a5',
}


def digest(data):return hashlib.sha256(data).hexdigest()


def pe_imports(data):
    if data[:2]!=b'MZ':return []
    pe=struct.unpack_from('<I',data,0x3c)[0]
    count=struct.unpack_from('<H',data,pe+6)[0];opt_size=struct.unpack_from('<H',data,pe+20)[0];opt=pe+24
    magic=struct.unpack_from('<H',data,opt)[0];directory=opt+(112 if magic==0x20b else 96)
    rva=struct.unpack_from('<I',data,directory+8)[0]
    if not rva:return []
    def position(address):
        for index in range(count):
            s=opt+opt_size+index*40
            virtual,base,raw_size,raw=struct.unpack_from('<IIII',data,s+8)
            if base<=address<base+max(virtual,raw_size):return raw+address-base
        raise ValueError('RVA PE fora das seções.')
    pos=position(rva);result=[]
    for _ in range(256):
        entry=data[pos:pos+20]
        if entry==b'\0'*20:return result
        name=position(struct.unpack_from('<I',entry,12)[0]);end=data.index(b'\0',name)
        result.append(data[name:end].decode('ascii').lower());pos+=20
    raise ValueError('Tabela de imports PE excedida.')


def copy_source(folder):
    names=['convenant_bios_tools.py','abrir-convenant-bios-tools.sh','requirements-native.txt','requirements-build-native.txt','docs/convenant-bios-tools.md',
           'studio/__init__.py','studio/firmware.py','studio/platform_update.py',
           'scripts/atualizar-microcodigo.py','native/launcher-windows.c',
           'scripts/compilar-exe-windows.py','scripts/empacotar-nativo.py']
    names += ['convenant/'+name+'.py' for name in ('__init__','core','hardware','workspace','native')]
    for name in names:
        dest=folder/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
    (folder/'abrir-convenant-bios-tools.sh').chmod(0o755)
    shutil.copyfile(ROOT/'docs/convenant-bios-tools.md',folder/'LEIA-ME.md')
    licenses=folder/'licenses';licenses.mkdir(exist_ok=True)
    for path in (ROOT/'licenses').glob('*'):
        if path.is_file():shutil.copyfile(path,licenses/path.name)
    (folder/'tools/FPT').mkdir(parents=True,exist_ok=True)
    (folder/'tools/FPT/COLOQUE-SUA-PASTA-FPT-AQUI.txt').write_text('Copie sua pasta completa do FPT compatível aqui. Nenhum executável Intel é incluído.\n',encoding='utf-8')


def windows_runtime(folder,toolchain):
    runtime=folder/'runtime/windows';runtime.mkdir(parents=True)
    with zipfile.ZipFile(toolchain/'python-3.12.10.nupkg') as archive:
        for name in archive.namelist():
            if name.startswith('tools/') and not name.endswith('/'):
                relative=Path(name[6:])
                if '..' in relative.parts:raise ValueError('Caminho inválido no runtime.')
                dest=runtime/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(archive.read(name))
        (folder/'licenses/Python-LICENSE.txt').write_bytes(archive.read('tools/LICENSE.txt'))
    entries={}
    for filename in ('PySide6_Essentials-6.8.3-cp39-abi3-win_amd64.whl','shiboken6-6.8.3-cp39-abi3-win_amd64.whl'):
        with zipfile.ZipFile(toolchain/'native-windows'/filename) as archive:
            entries.update({n:archive.read(n) for n in archive.namelist() if not n.endswith('/')})
    site=runtime/'Lib/site-packages'
    binaries={Path(n).name.lower():n for n in entries if n.endswith(('.dll','.pyd'))}
    seeds=[n for n in entries if n.startswith('shiboken6/')]
    seeds += [n for n in entries if n.startswith('PySide6/') and
              (n in ('PySide6/QtCore.pyd','PySide6/QtGui.pyd','PySide6/QtWidgets.pyd','PySide6/QtTest.pyd') or
               n.startswith('PySide6/support/') or
               (n.count('/')==1 and n.endswith(('.py','.json','.conf','.pyi'))) or
               n in ('PySide6/plugins/platforms/qwindows.dll','PySide6/plugins/platforms/qoffscreen.dll','PySide6/plugins/platforms/qminimal.dll'))]
    pending=list(seeds);selected=set();imports={}
    while pending:
        name=pending.pop()
        if name in selected:continue
        selected.add(name)
        if name.endswith(('.dll','.pyd')):
            imports[name]=pe_imports(entries[name])
            for dependency in imports[name]:
                if dependency in binaries:pending.append(binaries[dependency])
    for name in selected:
        dest=site/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(entries[name])
    for name,data in entries.items():
        if '.dist-info/' in name and ('license' in name.lower() or name.endswith('METADATA')):
            dest=site/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    return imports


def package(folder,destination,metadata):
    metadata['files']={str(p.relative_to(folder)).replace('\\','/'):digest(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()}
    (folder/'manifesto-pacote.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    if destination.exists():raise ValueError('Saída já existe: '+str(destination))
    if destination.name.endswith('.tar.gz'):
        def normalize(info):
            info.uid=info.gid=0;info.uname=info.gname='';return info
        with tarfile.open(destination,'x:gz',dereference=False,compresslevel=7) as archive:
            archive.add(folder,arcname=folder.name,filter=normalize)
    else:
        with zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED,compresslevel=7) as archive:
            for path in sorted(folder.rglob('*')):
                if path.is_file():archive.write(path,str(path.relative_to(folder.parent)))
        with zipfile.ZipFile(destination) as archive:
            if archive.testzip():raise ValueError('ZIP inválido.')
    return {'name':destination.name,'bytes':destination.stat().st_size,'sha256':digest(destination.read_bytes())}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--toolchain',type=Path,required=True)
    parser.add_argument('--windows-exe',type=Path,required=True)
    parser.add_argument('--linux-dist',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for name,expected in PINS.items():
        path=args.toolchain/('native-windows/'+name if name.endswith('.whl') else name)
        if digest(path.read_bytes())!=expected:raise ValueError('Componente inesperado: '+name)
    exe=args.windows_exe.read_bytes();pe=struct.unpack_from('<I',exe,0x3c)[0]
    if exe[:2]!=b'MZ' or struct.unpack_from('<H',exe,pe+24+68)[0]!=2:raise ValueError('Exige executável Windows GUI.')
    results=[]
    for system in ('Windows','CachyOS'):
        with tempfile.TemporaryDirectory(prefix='convenant-native-package-') as temp:
            folder=Path(temp)/('Convenant-BIOS-Tools-'+VERSION+'-'+system);folder.mkdir()
            if system=='CachyOS':
                shutil.copytree(args.linux_dist,folder,dirs_exist_ok=True,symlinks=True)
                if (folder/'Convenant-BIOS-Tools').read_bytes()[:4]!=b'\x7fELF':raise ValueError('ELF Linux ausente.')
            copy_source(folder)
            metadata={'name':'Convenant BIOS Tools','version':VERSION,'interface':'Qt Widgets native',
                      'browser_required':False,'http_server_started':False,'system':system,
                      'private_firmware_included':False,'intel_fpt_included':False,
                      'native_windows_execution_tested':False,'hardware_flash_tested':False}
            if system=='Windows':
                shutil.copyfile(args.windows_exe,folder/'Convenant-BIOS-Tools.exe')
                metadata['pe_dependencies']=windows_runtime(folder,args.toolchain)
                (folder/'Abrir-Convenant-BIOS-Tools.bat').write_bytes(b'@echo off\r\nstart "" "%~dp0Convenant-BIOS-Tools.exe"\r\n')
            uefi='UEFIExtract.exe' if system=='Windows' else 'uefiextract'
            archive=args.toolchain/('UEFIExtract_NE_A75_win64.zip' if system=='Windows' else 'UEFIExtract_NE_A75_x64_linux.zip')
            with zipfile.ZipFile(archive) as z:
                dest=folder/'tools/uefi'/('windows' if system=='Windows' else 'linux')/uefi
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(uefi));dest.chmod(0o755)
            extension='.zip' if system=='Windows' else '.tar.gz'
            results.append(package(folder,args.output/('Convenant-BIOS-Tools-'+VERSION+'-'+system+'-x64'+extension),metadata))
    (args.output/'SHA256SUMS-0.2.0.txt').write_text(''.join(r['sha256']+'  '+r['name']+'\n' for r in results))
    print(json.dumps(results,indent=2))


if __name__=='__main__':main()
