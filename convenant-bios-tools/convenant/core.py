"""Read-only checks shared by the GUI and the privileged hardware worker."""
import hashlib
import re
import struct
import subprocess
import tempfile
import shutil
from pathlib import Path

from studio.firmware import analyze, sha
from studio.platform_update import CODE_SHA256, build

MIB = 1024 * 1024
UPDATED_CODE = 'd54e3a3656ea1153b02aa46457ef100cc6fe04083b8ef5d9bcac8d659e2fc373'
PROFILES = {CODE_SHA256: '002-original', UPDATED_CODE: '002-microcodigos-experimental'}


def descriptor(data):
    if len(data) < 4096 or data[16:20] != bytes.fromhex('5aa5f00f'):
        raise ValueError('Descriptor Intel ausente ou incompleto.')
    f0, f1 = struct.unpack_from('<II', data, 20)
    frba, fmba = ((f0 >> 16) & 255) << 4, (f1 & 255) << 4
    if not (0x20 <= frba <= 0xFEC and 0x20 <= fmba <= 0xFF4):
        raise ValueError('Tabelas do descriptor fora dos limites.')
    regions = []
    for index, name in enumerate(('descriptor', 'bios', 'me_sps', 'gbe', 'pdr')):
        value = struct.unpack_from('<I', data, frba + index * 4)[0]
        start = (value & 0x7FFF) << 12
        end = (((value >> 16) & 0x7FFF) + 1) << 12
        regions.append({'name': name, 'start': start, 'end': end, 'present': start < end})
    master = struct.unpack_from('<I', data, fmba)[0]
    return {'signature_valid': True, 'regions': regions,
            'cpu_read_mask': (master >> 16) & 255, 'cpu_write_mask': (master >> 24) & 255,
            'scope': 'Mapa e permissões declaradas; não autentica o firmware.'}


def sps_bup(data, desc):
    """Bounded check of Grantley's FTPR BUP, not all SPS modules or signatures."""
    region = next((r for r in desc['regions'] if r['name'] == 'me_sps' and r['present']), None)
    unknown = {'status': 'not_checked', 'scope': 'BUP FTPR apenas; demais módulos SPS não verificados.'}
    if not region or region['end'] > len(data):
        return unknown
    start, end = region['start'], region['end']
    fpt = data.find(b'$FPT', start, min(start + 0x1000, end))
    if fpt < 0 or fpt + 32 > end:
        return unknown
    count = struct.unpack_from('<I', data, fpt + 4)[0]
    if not 1 <= count <= 64 or fpt + 32 + count * 32 > end:
        return unknown
    for index in range(count):
        entry = fpt + 32 + index * 32
        if data[entry:entry + 4] != b'FTPR':
            continue
        offset, size = struct.unpack_from('<II', data, entry + 8)
        base, limit = start + offset, start + offset + size
        if not start <= base < limit <= end or data[base + 28:base + 32] != b'$MN2':
            return unknown
        header, total = (struct.unpack_from('<I', data, base + off)[0] * 4 for off in (4, 24))
        if not 0x284 <= header <= total <= size:
            return unknown
        table = data.find(b'$MME', base + header, base + total)
        if table < 0 or table + 0x44 > limit or data[table + 4:table + 20].rstrip(b'\0') != b'BUP':
            return unknown
        relative = struct.unpack_from('<I', data, table + 0x38)[0]
        length = struct.unpack_from('<I', data, table + 0x40)[0]
        if not 0 < length <= size or not base + total <= base + relative < base + relative + length <= limit:
            return unknown
        expected = data[table + 0x14:table + 0x34][::-1].hex()
        actual = sha(data[base + relative:base + relative + length])
        return {**unknown, 'status': 'hash_matches' if expected == actual else 'hash_mismatch',
                'expected_sha256': expected, 'actual_sha256': actual,
                'offset': base + relative, 'size': length, 'manifest_signature_checked': False}
    return unknown


def inspect_blob(data):
    if len(data) not in (4096, 8 * MIB, 16 * MIB):
        raise ValueError('Use um descriptor de 4 KiB, BIOS de 8 MiB ou SPI de 16 MiB.')
    report = {'size': len(data), 'sha256': sha(data), 'hardware_tested': False,
              'status': 'analysis_only', 'issues': [], 'complete_recovery_verified': False}
    desc = None
    if len(data) in (4096, 16 * MIB):
        try:
            desc = descriptor(data)
            report['descriptor'] = desc
        except ValueError as exc:
            report['issues'].append(str(exc))
        if len(data) == 4096:
            report['status'] = 'descriptor_structure_checked' if desc else 'invalid'
            return report
    a = analyze(data)
    report.update(issues=report['issues'] + a['issues'], volumes=a['volumes'],
                  ffs_count=len(a['files']), microcodes=a['microcodes'])
    region = data
    if len(data) == 16 * MIB:
        if desc:
            bios = next(r for r in desc['regions'] if r['name'] == 'bios')
            if bios['present'] and bios['end'] <= len(data):
                region = data[bios['start']:bios['end']]
                report['bios_region'] = {**bios, 'sha256': sha(region)}
            report['sps_bup'] = sps_bup(data, desc)
            if report['sps_bup']['status'] == 'hash_mismatch':
                report['issues'].append('BUP do SPS com hash diferente dos metadados.')
    messages = re.findall(rb'BIOS Message: ([ -~]{1,120})', region)
    report['bios_id'] = messages[0].decode('ascii') if messages else 'Não identificado'
    report['profile'] = PROFILES.get(sha(region[0x80000:]), 'unknown') if len(region) == 8 * MIB else 'unknown'
    report['status'] = 'structural_errors' if report['issues'] else 'structure_checked_not_boot_tested'
    report['scope'] = 'Headers FV/FFS e microcódigos. Descompressão requer UEFIExtract; boot e estabilidade não testados.'
    return report


def deep_check(path, executable):
    """A zero exit code alone is not a successful UEFIExtract integrity check."""
    with tempfile.TemporaryDirectory(prefix='convenant-uefi-') as directory:
        target = Path(directory) / 'image.bin'
        shutil.copyfile(path, target)
        p = subprocess.run([str(executable), str(target), 'report'], capture_output=True,
                           encoding='utf-8', errors='replace', timeout=120)
        report_file = Path(str(target) + '.report.txt')
        inventory = report_file.read_text(errors='replace') if report_file.is_file() else ''
    log = p.stdout + p.stderr
    warnings, errors = [], []
    for line in log.splitlines():
        if not re.match(r'(?:[A-Za-z]+Parser::)?(?:parse|find)[A-Za-z]*:', line):
            continue
        if ('unable to parse ACM' in line or 'unknown JEDEC ID' in line
                or 'real FIT table found' in line):
            warnings.append(line)
        else:
            errors.append(line)
    if p.returncode:
        errors.append('UEFIExtract retornou código %d.' % p.returncode)
    parsed = any(line.split('|')[0].strip() == 'Volume' for line in inventory.splitlines())
    if not parsed:
        errors.append('UEFIExtract não produziu inventário de volumes.')
    return {'available': True, 'passed': not errors, 'warnings': warnings, 'errors': errors, 'log': log,
            'ffs_count': sum(line.split('|')[0].strip() == 'File' for line in inventory.splitlines())}


def compare_blobs(first, second):
    def region(a, b):
        changed = added = removed = 0
        for x, y in zip(a, b):
            if x != y:
                changed += 1
                added += (y & ~x).bit_count()
                removed += (x & ~y).bit_count()
        return {'different_bytes': changed, 'bits_0_to_1': added, 'bits_1_to_0': removed,
                'extra_bytes': abs(len(a) - len(b))}
    result = {'identical': first == second, 'same_size': len(first) == len(second),
              'first_sha256': sha(first), 'second_sha256': sha(second), 'whole': region(first, second)}
    a, b = first, second
    if len(a) == 16 * MIB:
        d = descriptor(a)
        r = next(x for x in d['regions'] if x['name'] == 'bios')
        a = a[r['start']:r['end']]
    if len(b) == 16 * MIB:
        d = descriptor(b)
        r = next(x for x in d['regions'] if x['name'] == 'bios')
        b = b[r['start']:r['end']]
    if len(a) == len(b) == 8 * MIB:
        result['bios'] = region(a, b)
        result['code_excluding_first_512KiB_nvram'] = region(a[0x80000:], b[0x80000:])
    return result


def check_write_candidate(candidate, current, board):
    """Restrict programming to the reviewed 002 code family, on the same board family."""
    normalized = re.sub(r'[^A-Z0-9]', '', board.upper())
    if 'E5D8MAX' not in normalized:
        raise ValueError('A placa não foi identificada como E5-D8 Max pelo sistema.')
    if len(candidate) != 8 * MIB or len(current) != 8 * MIB:
        raise ValueError('Gravação restrita à região BIOS de 8 MiB.')
    before, after = inspect_blob(current), inspect_blob(candidate)
    if before['issues'] or after['issues']:
        raise ValueError('A leitura atual ou a imagem candidata tem erros estruturais.')
    if before['profile'] == 'unknown' or after['profile'] == 'unknown':
        raise ValueError('Gravação não liberada para esta base. A versão 006 e perfis desconhecidos exigem investigação de compatibilidade.')
    return {'current_sha256': sha(current), 'candidate_sha256': sha(candidate),
            'profile': after['profile'], 'nvram_will_change': candidate[:0x80000] != current[:0x80000],
            'experimental': after['profile'].endswith('experimental'), 'hardware_compatibility_proven': False}


def build_candidate(first, second, v3, v4):
    return build(first, second, v3, v4)
