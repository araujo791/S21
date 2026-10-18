"""Experimental v3/v4 updates for one validated E5-D8-MAX firmware layout.

Each board supplies its own two matching BIOS-region reads. Only the first two
NVRAM volumes may differ from the reviewed code profile. No flash access.
"""
import argparse
import json
import struct
from pathlib import Path

from .firmware import analyze, builder, sha

CODE_START = 0x80000
CODE_SHA256 = 'f85309edb5f9df680cefff43a805eefdfe6e304dc332152110b8e87d8cbaeb88'
BIOS_PHYSICAL_BASE = 0xFF800000
INTEL_COMMIT = builder.INTEL_COMMIT
REFERENCES = {
    '306F2': {'cpuid': 0x306F2, 'revision': 0x49, 'flags': 0x6F,
              'size': 38912, 'path': 'intel-ucode/06-3f-02',
              'sha256': '78021d5f3de826d80061317bcba9fbaa17c813626fcf3cb4b19a2f1cfa2dad52'},
    '406F1': {'cpuid': 0x406F1, 'revision': 0x0B000040, 'flags': 0xEF,
              'size': 35840, 'path': 'intel-ucode-with-caveats/06-4f-01',
              'sha256': builder.INTEL_SHA256},
}
require = builder.require


def inspect(data):
    require(len(data) >= 48 and len(data) % 4 == 0, 'Tamanho de microcódigo inválido.')
    h = struct.unpack_from('<12I', data)
    require(h[0] == h[5] == 1 and h[9:] == (0, 0, 0), 'Cabeçalho Intel não suportado.')
    require(h[8] == len(data) and h[7] + 48 == len(data), 'Tamanho declarado inválido.')
    require(sum(struct.unpack(f'<{len(data) // 4}I', data)) % (1 << 32) == 0,
            'Checksum de microcódigo inválido.')
    return {'cpuid': f'{h[3]:05X}', 'revision': f'{h[1]:08X}',
            'platform_flags': f'{h[6]:02X}', 'date_bcd': f'{h[2]:08X}',
            'size': len(data), 'sha256': sha(data)}


def reference(data, key):
    r = REFERENCES[key]
    info = inspect(data)
    require(info['sha256'] == r['sha256'] and len(data) == r['size'],
            f'Referência Intel {key} diferente do arquivo fixado.')
    require(info['cpuid'] == key and int(info['revision'], 16) == r['revision']
            and int(info['platform_flags'], 16) == r['flags'], 'CPUID/revisão/plataforma inesperados.')
    return info


def build(base, second, intel_v3, intel_v4):
    require(len(base) == 0x800000 and base == second, 'Exige duas leituras idênticas de 8 MiB.')
    require(sha(base[CODE_START:]) == CODE_SHA256,
            'Perfil de firmware desconhecido; o nome da placa não basta para aplicar offsets.')
    before = analyze(base)
    require(not before['issues'], 'Falha estrutural da base: ' + '; '.join(before['issues']))
    require([(v['offset'], v['size']) for v in before['volumes'][:2]] ==
            [(0, 0x40000), (0x40000, 0x40000)], 'Volumes NVRAM inesperados.')
    inputs = {'306F2': intel_v3, '406F1': intel_v4}
    refs = {key: reference(data, key) for key, data in inputs.items()}
    codes = before['microcodes']
    require([m['cpuid'] for m in codes] == ['306F1', '306F2', '406F0', '406F1'],
            'Inventário de microcódigos inesperado.')
    ffs = builder.inspect_ffs(base, builder.FFS_OFFSET, builder.UCODE_GUID, 1, 8, builder.FFS_SIZE)
    pad = builder.inspect_ffs(base, builder.PAD_OFFSET, b'\xff' * 16, 0xF0, 0, builder.PAD_SIZE)
    require(base[builder.TRAILER_OFFSET:builder.PAD_OFFSET] == builder.MPDT, 'Trailer MPDT inesperado.')
    cursor, parts, changes = builder.FFS_OFFSET + 24, [], []
    for code in codes:
        original = base[code['offset']:code['offset'] + code['size']]
        old_info = inspect(original)
        replacement = inputs.get(code['cpuid'], original)
        new_info = refs.get(code['cpuid'], old_info)
        require(int(old_info['platform_flags'], 16) & ~int(new_info['platform_flags'], 16) == 0,
                'A atualização removeria suporte a uma plataforma do microcódigo.')
        changes.append({'cpuid': code['cpuid'], 'old_offset': code['offset'], 'new_offset': cursor,
                        'old': old_info, 'new': new_info, 'payload_changed': replacement != original})
        parts.append(replacement)
        cursor += len(replacement)
    payload = b''.join(parts) + builder.MPDT
    new_size = 24 + len(payload)
    delta = new_size - builder.FFS_SIZE
    new_pad = builder.PAD_OFFSET + delta
    require(delta == 0x2800 and new_pad == cursor + len(builder.MPDT), 'Crescimento inesperado.')
    require(base[builder.PAD_OFFSET + 24:new_pad + 24] == b'\xff' * delta,
            'O crescimento atingiria dados do padding.')
    out = bytearray(base)
    out[builder.FFS_OFFSET:builder.FFS_OFFSET + 24] = builder.resized_ffs(ffs, new_size)
    out[builder.FFS_OFFSET + 24:new_pad] = payload
    out[new_pad:new_pad + 24] = builder.resized_ffs(pad, builder.PAD_SIZE - delta)
    # This profile's FIT has C_V=0, inferred microcode sizes and no enabled checksum.
    # Keep those fields; only update addresses of the two relocated entries.
    fit_start, fit_size = builder.FIT_OFFSET, 26 * 16
    fit = bytearray(base[fit_start:fit_start + fit_size])
    require(fit[:8] == b'_FIT_   ' and fit[14:16] == b'\0\0', 'Cabeçalho FIT fora do perfil.')
    for index, change in enumerate(changes, 1):
        pos = index * 16
        old_address = BIOS_PHYSICAL_BASE + change['old_offset']
        require(struct.unpack_from('<Q', fit, pos)[0] == old_address
                and fit[pos + 8:pos + 11] == b'\0\0\0'
                and fit[pos + 14:pos + 16] == b'\x01\0', 'Entrada FIT fora do perfil.')
        struct.pack_into('<Q', fit, pos, BIOS_PHYSICAL_BASE + change['new_offset'])
    out[fit_start:fit_start + fit_size] = fit
    out = bytes(out)
    require(len(out) == len(base), 'Tamanho da região alterado.')
    require(out[:CODE_START] == base[:CODE_START], 'A NVRAM da placa foi alterada.')
    require(out[CODE_START:fit_start] == base[CODE_START:fit_start], 'DXE ou padding anterior alterado.')
    require(out[fit_start + fit_size:builder.FFS_OFFSET] == base[fit_start + fit_size:builder.FFS_OFFSET],
            'Inicialização anterior ao FFS alterada.')
    require(out[new_pad + 24:] == base[new_pad + 24:], 'Cauda de inicialização alterada.')
    after = analyze(out)
    require(not after['issues'], 'Falha estrutural da candidata.')
    for change in changes:
        offset = change['new_offset']
        require(out[offset:offset + change['new']['size']] ==
                inputs.get(change['cpuid'], base[change['old_offset']:change['old_offset'] + change['old']['size']]),
                'Conteúdo de microcódigo não preservado.')
    manifest = {
        'status': 'experimental_static_only_not_hardware_tested',
        'profile': 'E5-D8-MAX X99D8 Ver:002 2022-12-20; matching firmware code required',
        'input_code_sha256': CODE_SHA256, 'code_fingerprint_excludes': 'BIOS offsets 0x0..0x7FFFF (two NVRAM volumes)',
        'base_sha256': sha(base), 'output_sha256': sha(out), 'output_code_sha256': sha(out[CODE_START:]),
        'size_bytes': len(out), 'microcodes': changes,
        'intel_commit': INTEL_COMMIT,
        'intel_sources': {key: f'https://github.com/intel/Intel-Linux-Processor-Microcode-Data-Files/blob/{INTEL_COMMIT}/{r["path"]}'
                          for key, r in REFERENCES.items()},
        'own_board_nvram_preserved': True, 'other_microcode_payloads_preserved': True,
        'memory_and_power_settings_changed': False, 'cpu_memory_initialization_code_changed': False,
        'fit_microcode_addresses_adjusted': True, 'extra_bytes_used': delta,
        'new_padding_offset': new_pad, 'not_a_complete_spi_image': True,
        'physical_board_identity_verified': False, 'signatures_verified': False,
        'hardware_boot_tested': False, 'performance_measured': False, 'flash_performed': False,
        'scope': 'Shared firmware code profile, not every board sold under this model name; build from each board own reads.',
    }
    return out, manifest


def read_region(path):
    with path.open('rb') as source:
        data = source.read(0x800001)
    require(len(data) == 0x800000, 'Esperada região BIOS de 8 MiB.')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('base', 'segunda-leitura', 'microcodigo-v3', 'microcodigo-v4', 'saida', 'manifesto'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    require(args.saida.resolve() != args.manifesto.resolve(), 'Saída e manifesto devem ser distintos.')
    require(not args.saida.exists() and not args.manifesto.exists(), 'Saída ou manifesto já existe.')
    image, manifest = build(read_region(args.base), read_region(args.segunda_leitura),
                            args.microcodigo_v3.read_bytes(), args.microcodigo_v4.read_bytes())
    with args.saida.open('xb') as dest:
        dest.write(image)
    with args.manifesto.open('x', encoding='utf-8') as dest:
        json.dump(manifest, dest, indent=2, ensure_ascii=False)
        dest.write('\n')
    print(json.dumps({'status': manifest['status'], 'sha256': manifest['output_sha256'],
                      'own_board_nvram_preserved': True}, indent=2))
