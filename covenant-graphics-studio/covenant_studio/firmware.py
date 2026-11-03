"""Bounded read-only inspection of the Machinist 002 and its actual HII."""
from pathlib import Path
import hashlib
import lzma
import re
import struct
import uuid

from .hii import resources, parse

SETUP = '899407D7-99FE-43D8-9A21-79EC328CAC21'
PLATFORM = 'ABBCE13D-E25A-4D9F-A1F9-2F7710786892'
LZMA_GUID = 'EE4E5898-3914-4259-9D6E-DC7BD79403CF'
FVS = {'8C8CE578-8A3D-4F1C-9935-896185C32DD3', '5473C07A-3DCB-4DCA-BD6F-1E9689E7349A'}
EXPECTED = {SETUP: '4633f058bcb627bc3e521ec94ddaf0b783a531dbbc32c47505c009051170c921',
            PLATFORM: 'a493d4b841c7a0e7798ffd367234ce1570dfdf889746aeaef55a51c9b410ef77'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def section_leaves(data, depth=0, budget=None):
    require(depth <= 8, 'Profundidade de seções excedida.')
    if budget is None:
        budget = [32 * 1024 * 1024]
    budget[0] -= len(data)
    require(budget[0] >= 0, 'Limite de descompressão excedido.')
    pos = count = 0
    result = []
    while pos + 4 <= len(data):
        size, kind = int.from_bytes(data[pos:pos+3], 'little'), data[pos+3]
        require(4 <= size < 0xFFFFFF and pos + size <= len(data) and count < 4096,
                'Cabeçalho de seção inválido.')
        if kind == 2:
            require(size >= 24, 'Seção comprimida truncada.')
            guid = str(uuid.UUID(bytes_le=data[pos+4:pos+20])).upper()
            offset, attrs = struct.unpack_from('<HH', data, pos+20)
            require(guid == LZMA_GUID and attrs == 1 and 24 <= offset <= size,
                    'Encapsulamento do Setup não suportado.')
            decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE, memlimit=64*1024*1024)
            body = decoder.decompress(data[pos+offset:pos+size], max_length=8*1024*1024+1)
            require(len(body) <= 8*1024*1024 and decoder.eof and not decoder.unused_data,
                    'Fluxo LZMA inválido ou grande demais.')
            result.extend(section_leaves(body, depth+1, budget))
        else:
            require(kind != 1, 'Compressão EFI/Tiano no Setup não suportada nesta versão.')
            result.append((kind, data[pos+4:pos+size]))
        pos = (pos+size+3)&~3
        count += 1
    require(pos >= len(data) or all(x in (0,255) for x in data[pos:]), 'Cauda de seção inesperada.')
    return result


def bios_region(data):
    require(len(data) in (0x800000, 0x1000000), 'Abra uma região BIOS de 8 MiB ou um chip de 16 MiB.')
    if len(data) == 0x800000:
        return data, None
    require(data[16:20] == bytes.fromhex('5aa5f00f'), 'Descriptor Intel ausente.')
    frba = ((struct.unpack_from('<I',data,20)[0]>>16)&255)<<4
    require(0x20 <= frba <= 0xFE0, 'Tabela de regiões fora dos limites.')
    raw = struct.unpack_from('<I',data,frba+4)[0]
    start, end = (raw&0x7FFF)<<12, (((raw>>16)&0x7FFF)+1)<<12
    require((start,end) == (0x800000,0x1000000),
            'O mapa desta ROM não corresponde à região BIOS de 8 MiB da 002.')
    return data[start:end], {'start':start,'end':end}


def inspect_bytes(data):
    region, desc = bios_region(data)
    message = re.search(rb'BIOS Message: ([ -~]{1,130})',region)
    identity = message[1].decode() if message else ''
    require(identity.startswith('X99D8 Ver:002 '), 'A imagem não foi identificada como X99D8 Ver:002.')
    volumes, files, microcodes = [], [], []
    cursor = 0
    while True:
        marker = region.find(b'_FVH',cursor)
        if marker < 0:
            break
        cursor = marker+4
        start = marker-40
        if start < 0 or start+56 > len(region):
            continue
        guid = str(uuid.UUID(bytes_le=region[start+16:start+32])).upper()
        if guid not in FVS:
            continue
        size = struct.unpack_from('<Q',region,start+32)[0]
        header = struct.unpack_from('<H',region,start+48)[0]
        require(56 <= header <= min(size,4096) and header%2 == 0
                and start+size <= len(region), 'Volume UEFI fora dos limites.')
        require(sum(struct.unpack_from('<%dH'%(header//2),region,start))%65536 == 0,
                'Checksum de volume UEFI inválido.')
        volumes.append({'offset':start,'size':size})
        cursor = start+size
        ext = struct.unpack_from('<H',region,start+52)[0]
        if ext:
            require(ext+20 <= size, 'Extensão de volume truncada.')
            extra = struct.unpack_from('<I',region,start+ext+16)[0]
            require(20 <= extra and ext+extra <= size, 'Extensão de volume inválida.')
            header = max(header,ext+extra)
        pos, end = (start+header+7)&~7,start+size
        for _ in range(4096):
            if pos+24>end:
                break
            h = region[pos:pos+24]
            if len(h)<24 or h in (b'\xff'*24,b'\0'*24):
                break
            length = int.from_bytes(h[20:23],'little')
            require(not(h[19]&1) and 24 <= length < 0xFFFFFF and pos+length <= end,
                    'FFS inválido ou estendido não suportado.')
            require((sum(h)-h[17]-h[23])%256 == 0, 'Checksum de cabeçalho FFS inválido.')
            require(((sum(region[pos+24:pos+length])+h[17])%256 == 0) if h[19]&0x40
                    else h[17] == 0xAA, 'Checksum de dados FFS inválido.')
            fg = str(uuid.UUID(bytes_le=h[:16])).upper()
            files.append({'guid':fg,'offset':pos,'size':length,'type':h[18],
                          'sha256':sha(region[pos:pos+length])})
            if fg == '17088572-377F-44EF-8F4E-B09FFF46A070':
                at = pos+24
                for _ in range(64):
                    if region[at:at+4] != b'\x01\0\0\0' or at+48 > pos+length:
                        break
                    u = struct.unpack_from('<12I',region,at)
                    n = u[8] or 2048
                    require(n>=48 and n%4 == 0 and at+n <= pos+length, 'Microcódigo fora dos limites.')
                    require(sum(struct.unpack_from('<%dI'%(n//4),region,at))%2**32 == 0,
                            'Checksum de microcódigo inválido.')
                    microcodes.append({'cpuid':f'{u[3]:05X}','revision':f'{u[1]:08X}'})
                    at += n
            pos = (pos+length+7)&~7
    require([(v['offset'],v['size']) for v in volumes] ==
            [(0,0x40000),(0x40000,0x40000),(0x90000,0x500000),(0x5A0000,0x260000)],
            'Layout de volumes diferente do perfil 002.')
    forms, questions, module_hashes = [], [], {}
    for guid in (SETUP, PLATFORM):
        matches = [f for f in files if f['guid']==guid]
        require(len(matches)==1, 'Setup/Platform ausente ou duplicado.')
        f = matches[0];module_hashes[guid] = f['sha256']
        parsed_count = 0
        for kind, body in section_leaves(region[f['offset']+24:f['offset']+f['size']]):
            if kind != 0x10:
                continue
            for resource in resources(body):
                a = parse(resource,guid,max_questions=16384)
                forms += a['forms'];questions += a['questions'];parsed_count += 1
        require(parsed_count == 1, 'Esperada uma lista HII por módulo da 002.')
    require(len({q['id'] for q in questions})==len(questions), 'Identificadores HII duplicados.')
    stores = {(q['store']['guid'],q['store']['name'],q['store']['size'])
              for q in questions if q.get('store')}
    guid = 'EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9'
    require((guid,'Setup',125) in stores and (guid,'IntelSetup',6091) in stores,
            'Layout das variáveis diferente da 002 suportada.')
    return {'sha256':sha(data),'size':len(data),'bios_id':identity,'descriptor_region':desc,
            'forms':forms,'questions':questions,'volumes':volumes,'ffs_count':len(files),
            'microcodes':microcodes,'module_hashes':module_hashes,
            'original_ui_modules':module_hashes==EXPECTED,
            'scope':'Leitura de FV/FFS, microcódigos e HII Setup/Platform; não testa boot, callbacks ou todos os módulos.'}


def load_firmware(path):
    with Path(path).open('rb') as source:
        data = source.read(0x1000001)
    result=inspect_bytes(data)
    result['_input_path']=str(Path(path).resolve())
    return result
