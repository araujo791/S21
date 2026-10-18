#!/usr/bin/env python3
"""Build an experimental BIOS-region image for the single validated E5-D8-MAX dump.

No hardware access or flashing. Input fingerprints are intentionally restrictive.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

BASE_SHA256 = '392fc916c4b5c3d27fde2e5799bbae3a59a2c4d809f88f3938b4c054ef0ba58f'
INTEL_SHA256 = 'e3242ce8ec36a416af379475c04bf4d10178905c3bec5643d2690bd136aa18fa'
INTEL_COMMIT = 'bdc92abe5c499c3fd7988b76a128d05c9120a520'
FFS_OFFSET = 0x691118
UCODE_OFFSET = 0x6A9930
OLD_UCODE_SIZE = 0x7800
TRAILER_OFFSET = 0x6B1130
PAD_OFFSET = 0x6B1140
FIT_OFFSET = 0x590000
FFS_SIZE = 0x20028
PAD_SIZE = 0x14CD78
UCODE_GUID = bytes.fromhex('728508177f37ef448f4eb09fff46a070')
MPDT = bytes.fromhex('4d504454000100001000000000001000')


class FirmwareError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise FirmwareError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def inspect_microcode(data, signature, revision):
    require(len(data) >= 48 and len(data) % 4 == 0, 'Tamanho de microcódigo inválido')
    header = struct.unpack_from('<12I', data)
    require(header[0] == 1 and header[5] == 1, 'Formato de microcódigo inesperado')
    require(header[3] == signature and header[1] == revision, 'CPUID/revisão inesperado')
    require(header[6] == 0xEF and header[9:] == (0, 0, 0), 'Plataforma/cabeçalho inesperado')
    require(header[8] == len(data) and header[7] + 48 == len(data), 'Tamanho declarado inválido')
    require(sum(struct.unpack(f'<{len(data) // 4}I', data)) % (1 << 32) == 0,
            'Checksum do microcódigo inválido')
    return {'cpuid': f'0x{header[3]:05X}', 'revision': f'0x{header[1]:08X}',
            'date_bcd': f'{header[2]:08X}', 'platform_flags': f'0x{header[6]:02X}',
            'size_bytes': len(data), 'sha256': sha256(data)}


def inspect_ffs(image, offset, guid, kind, attrs, size):
    h = image[offset:offset + 24]
    require(len(h) == 24 and h[:16] == guid, 'GUID/cabeçalho FFS inesperado')
    require(h[18] == kind and h[19] == attrs and h[23] == 0xF8, 'Tipo/atributos/estado FFS inesperado')
    require(int.from_bytes(h[20:23], 'little') == size, 'Tamanho FFS inesperado')
    require((sum(h) - h[17] - h[23]) % 256 == 0 and h[17] == 0xAA,
            'Checksum de cabeçalho FFS inválido')
    return h


def resized_ffs(header, size):
    require(24 <= size < 0xFFFFFF, 'Tamanho FFS fora do formato suportado')
    h = bytearray(header)
    h[20:23] = size.to_bytes(3, 'little')
    h[16] = 0
    h[16] = (-(sum(h) - h[17] - h[23])) % 256
    return bytes(h)


def build_candidate(base, second, intel):
    require(len(base) == 0x800000 and base == second, 'As leituras de 8 MiB precisam ser idênticas')
    require(sha256(base) == BASE_SHA256, 'Base desconhecida; este helper aceita somente a leitura validada')
    target = inspect_microcode(intel, 0x406F1, 0x0B000040)
    require(sha256(intel) == INTEL_SHA256, 'O arquivo não corresponde à referência Intel fixada')
    old = base[UCODE_OFFSET:UCODE_OFFSET + OLD_UCODE_SIZE]
    previous = inspect_microcode(old, 0x406F1, 0x0B000038)
    h = inspect_ffs(base, FFS_OFFSET, UCODE_GUID, 1, 8, FFS_SIZE)
    pad = inspect_ffs(base, PAD_OFFSET, b'\xFF' * 16, 0xF0, 0, PAD_SIZE)
    require(FFS_OFFSET + FFS_SIZE == PAD_OFFSET and UCODE_OFFSET + len(old) == TRAILER_OFFSET,
            'Limites do arquivo de microcódigos inesperados')
    require(base[TRAILER_OFFSET:PAD_OFFSET] == MPDT, 'Trailer MPDT inesperado')
    delta = len(intel) - len(old)
    require(delta == 0x1400, 'Esta variante foi revisada somente para crescimento de 5 KiB')
    new_pad = PAD_OFFSET + delta
    require(base[PAD_OFFSET + 24:new_pad + 24] == b'\xFF' * delta,
            'O crescimento atingiria conteúdo não vazio')
    fit_count = int.from_bytes(base[FIT_OFFSET + 8:FIT_OFFSET + 11], 'little')
    require(base[FIT_OFFSET:FIT_OFFSET + 8] == b'_FIT_   ' and fit_count == 26,
            'Tabela FIT inesperada')
    fit = base[FIT_OFFSET:FIT_OFFSET + fit_count * 16]
    entry = fit[64:80]
    require(struct.unpack_from('<Q', entry)[0] == 0xFFEA9930 and entry[8:11] == b'\0\0\0'
            and entry[14] & 0x7F == 1, 'Entrada FIT do microcódigo inesperada')

    patched = bytearray(base)
    patched[FFS_OFFSET:FFS_OFFSET + 24] = resized_ffs(h, FFS_SIZE + delta)
    patched[UCODE_OFFSET:UCODE_OFFSET + len(intel)] = intel
    patched[UCODE_OFFSET + len(intel):new_pad] = MPDT
    patched[new_pad:new_pad + 24] = resized_ffs(pad, PAD_SIZE - delta)
    patched = bytes(patched)

    require(len(patched) == len(base), 'O tamanho da região foi alterado')
    require(patched[:FFS_OFFSET] == base[:FFS_OFFSET], 'Conteúdo anterior ao arquivo FFS mudou')
    require(patched[FFS_OFFSET + 24:UCODE_OFFSET] == base[FFS_OFFSET + 24:UCODE_OFFSET],
            'Outros microcódigos foram alterados')
    require(patched[new_pad + 24:] == base[new_pad + 24:], 'Conteúdo posterior ao pad foi alterado')
    require(patched[FIT_OFFSET:FIT_OFFSET + len(fit)] == fit, 'A tabela FIT foi alterada')
    require(patched[UCODE_OFFSET:UCODE_OFFSET + len(intel)] == intel, 'Payload Intel foi alterado')
    inspect_ffs(patched, FFS_OFFSET, UCODE_GUID, 1, 8, FFS_SIZE + delta)
    inspect_ffs(patched, new_pad, b'\xFF' * 16, 0xF0, 0, PAD_SIZE - delta)
    manifest = {
        'status': 'experimental_static_validation_only_not_hardware_tested',
        'scope': 'BIOS region only; Intel 406F1 microcode 0B000038 -> 0B000040; original interface',
        'size_bytes': len(patched), 'base_sha256': sha256(base), 'output_sha256': sha256(patched),
        'intel_source': f'https://github.com/intel/Intel-Linux-Processor-Microcode-Data-Files/blob/{INTEL_COMMIT}/intel-ucode-with-caveats/06-4f-01',
        'intel_source_commit': INTEL_COMMIT,
        'previous_microcode': previous, 'new_microcode': target,
        'fit_unchanged': True, 'other_microcodes_unchanged': True, 'mpdt_bytes_preserved': True,
        'nvram_and_dxe_unchanged': True, 'following_startup_ap_data_and_volume_top_unchanged': True,
        'microcode_ffs': {'offset': hex(FFS_OFFSET), 'old_size': FFS_SIZE, 'new_size': FFS_SIZE + delta},
        'padding_ffs': {'old_offset': hex(PAD_OFFSET), 'new_offset': hex(new_pad),
                        'old_size': PAD_SIZE, 'new_size': PAD_SIZE - delta},
        'not_a_complete_spi_image': True, 'graphical_interface_integrated': False,
        'flash_performed': False, 'boot_validation': 'not_run',
    }
    return patched, manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--segunda-leitura', type=Path, required=True)
    p.add_argument('--microcodigo', type=Path, required=True)
    p.add_argument('--saida', type=Path, required=True)
    p.add_argument('--manifesto', type=Path, required=True)
    args = p.parse_args()
    require(args.saida.resolve() != args.manifesto.resolve(), 'Saída e manifesto devem ser distintos')
    for dest in (args.saida, args.manifesto):
        require(not dest.exists(), f'Arquivo já existe; não será sobrescrito: {dest}')
    patched, manifest = build_candidate(args.base.read_bytes(), args.segunda_leitura.read_bytes(),
                                        args.microcodigo.read_bytes())
    with args.saida.open('xb') as f:
        f.write(patched)
    with args.manifesto.open('x') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(json.dumps({'status': manifest['status'], 'output_sha256': manifest['output_sha256'],
                      'size_bytes': len(patched)}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (FirmwareError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
