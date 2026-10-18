"""Bounded, read-only FV/FFS inspection and a narrowly scoped experimental build."""
import hashlib
import importlib.util
import io
import json
import re
import struct
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('microcode_builder', ROOT / 'scripts/atualizar-microcodigo.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
MICROCODE_GUID = '17088572-377F-44EF-8F4E-B09FFF46A070'
FILESYSTEMS = {'8C8CE578-8A3D-4F1C-9935-896185C32DD3',
               '5473C07A-3DCB-4DCA-BD6F-1E9689E7349A',
               '7A9354D9-0468-444A-81CE-0BF617D890DF'}
NAMES = {MICROCODE_GUID: 'Microcódigos Intel',
         'B1DA0ADF-4F77-4070-A88E-BFFE1C60529A': 'AMITSE',
         'FE612B72-203C-47B1-8560-A66D946EB371': 'AMITSESetupData',
         '899407D7-99FE-43D8-9A21-79EC328CAC21': 'Setup',
         '3B87CD35-0D65-415E-8B35-0DDADA13F30E': 'CoolGUIDxe',
         'B7246C46-4200-4D44-BAE0-39CFDCAC6584': 'CoolSetupDataDxe',
         'C7A7030C-C3D8-45EE-BED9-5D9E76762953': 'MouseDriver'}
DEFAULT_PROJECT = {'format': 'machinist-studio-theme', 'version': 1,
                   'title': 'MACHINIST', 'subtitle': 'E5-D8 MAX',
                   'accent': '#e83d48', 'background': '#101116', 'foreground': '#ebedf2',
                   'font_size': 16, 'radius': 8, 'mode': 'easy',
                   'cards': ['system', 'cpu', 'memory', 'boot', 'storage', 'fans']}
CARD_IDS = set(DEFAULT_PROJECT['cards'])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_project(project):
    if not isinstance(project, dict) or set(project) != set(DEFAULT_PROJECT):
        raise ValueError('Formato do projeto inválido ou campos desconhecidos.')
    if project['format'] != DEFAULT_PROJECT['format'] or type(project['version']) is not int or project['version'] != 1:
        raise ValueError('Versão de projeto não suportada.')
    for key in ('title', 'subtitle'):
        if not isinstance(project[key], str) or not 1 <= len(project[key]) <= 48 or any(ord(c) < 32 for c in project[key]):
            raise ValueError('Use títulos de 1 a 48 caracteres imprimíveis.')
    for key in ('accent', 'background', 'foreground'):
        if not isinstance(project[key], str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', project[key]):
            raise ValueError('Cor inválida no projeto.')
    for key, low, high in [('font_size', 12, 22), ('radius', 0, 20)]:
        if type(project[key]) is not int or not low <= project[key] <= high:
            raise ValueError('Dimensão inválida no projeto.')
    if project['mode'] not in ('easy', 'classic'):
        raise ValueError('Modo de visualização inválido.')
    cards = project['cards']
    if not isinstance(cards, list) or len(cards) != 6 or any(not isinstance(c, str) for c in cards) or set(cards) != CARD_IDS:
        raise ValueError('O projeto deve conter os seis painéis, sem repetição.')
    return dict(project, cards=list(cards))


def microcodes(data, start, end, issues):
    result = []
    pos = start
    for _ in range(64):
        if pos + 48 > end or data[pos:pos + 4] != b'\x01\0\0\0':
            break
        header = struct.unpack_from('<12I', data, pos)
        size = header[8] or 2048
        if size < 48 or size % 4 or pos + size > end:
            issues.append(f'Microcódigo fora dos limites em 0x{pos:X}.')
            break
        valid = sum(struct.unpack_from(f'<{size // 4}I', data, pos)) % (1 << 32) == 0
        result.append({'offset': pos, 'cpuid': f'{header[3]:05X}', 'revision': f'{header[1]:08X}',
                       'date_bcd': f'{header[2]:08X}', 'size': size, 'checksum_valid': valid})
        if not valid:
            issues.append(f'Checksum inválido do microcódigo {header[3]:05X} em 0x{pos:X}.')
        pos += size
    return result


def analyze(data):
    if len(data) not in (8 * 1024 * 1024, 16 * 1024 * 1024):
        raise ValueError('Abra uma região BIOS de 8 MiB ou uma imagem SPI de 16 MiB.')
    data = bytes(data)
    report = {'size': len(data), 'sha256': sha(data), 'known_base': sha(data) == builder.BASE_SHA256,
              'volumes': [], 'files': [], 'microcodes': [], 'issues': [],
              'structural_scope': 'FV headers, top-level FFS headers/data checksums, raw Intel microcodes',
              'decompression_checked': False, 'signatures_checked': False, 'boot_tested': False,
              'graphical_integration_available': False}
    if len(data) == 16 * 1024 * 1024 and data[16:20] == b'\x5a\xa5\xf0\x0f':
        frba = ((struct.unpack_from('<I', data, 20)[0] >> 16) & 255) << 4
        if 0x20 <= frba <= 0xFE0:
            region = struct.unpack_from('<I', data, frba + 4)[0]
            start, end = (region & 0x7FFF) << 12, (((region >> 16) & 0x7FFF) + 1) << 12
            if 0 <= start < end <= len(data):
                report['bios_region'] = {'start': start, 'end': end, 'sha256': sha(data[start:end])}
    cursor = 0
    while True:
        marker = data.find(b'_FVH', cursor)
        if marker < 0:
            break
        cursor = marker + 4
        start = marker - 40
        if start < 0 or start + 56 > len(data):
            continue
        guid = str(uuid.UUID(bytes_le=data[start + 16:start + 32])).upper()
        if guid not in FILESYSTEMS:
            continue
        size = struct.unpack_from('<Q', data, start + 32)[0]
        header_size = struct.unpack_from('<H', data, start + 48)[0]
        if size < 56 or start + size > len(data) or not 56 <= header_size <= min(size, 4096) or header_size % 2:
            report['issues'].append(f'Volume fora dos limites em 0x{start:X}.')
            continue
        header_valid = sum(struct.unpack_from(f'<{header_size // 2}H', data, start)) % 65536 == 0
        report['volumes'].append({'offset': start, 'size': size, 'checksum_valid': header_valid})
        # This inspector enumerates top-level volumes, never unbounded overlapping candidates.
        cursor = start + size
        if not header_valid:
            report['issues'].append(f'Checksum de volume inválido em 0x{start:X}.')
        ext = struct.unpack_from('<H', data, start + 52)[0]
        file_start = header_size
        if ext:
            if ext + 20 > size:
                report['issues'].append(f'Extensão de volume fora dos limites em 0x{start:X}.')
                continue
            ext_size = struct.unpack_from('<I', data, start + ext + 16)[0]
            if ext_size < 20 or ext + ext_size > size:
                report['issues'].append(f'Tamanho de extensão inválido em 0x{start:X}.')
                continue
            file_start = max(file_start, ext + ext_size)
        pos, end = (start + file_start + 7) & ~7, start + size
        for _ in range(4096):
            if pos + 24 > end or data[pos:pos + 24] in (b'\xff' * 24, b'\0' * 24):
                break
            header = data[pos:pos + 24]
            file_size = int.from_bytes(header[20:23], 'little')
            if header[19] & 1 or file_size == 0xFFFFFF:
                report['issues'].append(f'FFS estendido não suportado em 0x{pos:X}; análise parcial.')
                break
            if file_size < 24 or pos + file_size > end:
                report['issues'].append(f'FFS fora dos limites em 0x{pos:X}; análise parcial.')
                break
            file_guid = str(uuid.UUID(bytes_le=header[:16])).upper()
            hvalid = (sum(header) - header[17] - header[23]) % 256 == 0
            dvalid = ((sum(data[pos + 24:pos + file_size]) + header[17]) % 256 == 0
                      if header[19] & 0x40 else header[17] == 0xAA)
            item = {'offset': pos, 'size': file_size, 'guid': file_guid,
                    'name': NAMES.get(file_guid, 'Padding' if header[18] == 0xF0 else file_guid),
                    'type': header[18], 'header_valid': hvalid, 'data_checksum_valid': dvalid}
            report['files'].append(item)
            if not hvalid or not dvalid:
                report['issues'].append(f'Checksum FFS inválido em 0x{pos:X} ({item["name"]}).')
            if file_guid == MICROCODE_GUID:
                report['microcodes'].extend(microcodes(data, pos + 24, pos + file_size, report['issues']))
            pos = (pos + file_size + 7) & ~7
    if not report['volumes']:
        report['issues'].append('Nenhum volume UEFI reconhecido; arquivo não validado.')
    report['plan'] = [
        {'action': 'microcode_406f1_040', 'status': 'experimental_available' if report['known_base'] else 'blocked_unknown_base',
         'detail': 'Exige segunda leitura idêntica e referência Intel de hash fixado; não altera outros códigos.'},
        {'action': 'graphical_interface', 'status': 'design_only',
         'detail': 'Prévia e projeto exportáveis. Renderizador AMI e callbacks da Machinist ainda não integrados.'},
        {'action': 'flash', 'status': 'not_available', 'detail': 'O aplicativo não grava a flash.'}]
    return report


def package(base, second, intel, project):
    project = validate_project(project)
    image, manifest = builder.build_candidate(base, second, intel)
    report = analyze(image)
    if report['issues']:
        raise ValueError('A candidata falhou na análise estrutural: ' + '; '.join(report['issues']))
    manifest['theme_applied_to_firmware'] = False
    manifest['project_role'] = 'visual_design_only_separate_from_firmware'
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('E5-D8-MAX-MCU040-EXPERIMENTAL-8MiB.bin', image)
        for name, payload in [('manifest.json', manifest), ('analysis.json', report), ('theme-project.json', project)]:
            bundle.writestr(name, json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
        bundle.writestr('LEIA-ME.txt', 'EXPERIMENTAL: sem teste de boot; não liberada para gravação.\n'
                        'Região BIOS de 8 MiB, não é imagem integral de 16 MiB.\n'
                        'A candidata altera somente microcódigo. O tema JSON é uma prévia separada, não integrada.\n')
    return output.getvalue()
