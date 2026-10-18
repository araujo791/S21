"""Explicit operations only: no force, erase, descriptor writes or arbitrary commands."""
import ctypes
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .core import MIB, check_write_candidate, deep_check, inspect_blob, sha

REGIONS = {'full': (None, None, 16 * MIB), 'bios': ('-bios', 'bios', 8 * MIB),
           'descriptor': ('-desc', 'fd', 4096), 'sps': ('-me', 'me', 0x7FF000)}


def inventory():
    result = {'os': platform.system(), 'architecture': platform.machine(), 'board': '',
              'bios': '', 'cpus': [], 'memory_bytes': None}
    if os.name == 'nt':
        script = "$b=Get-CimInstance Win32_BaseBoard; $f=Get-CimInstance Win32_BIOS; " \
                 "$c=Get-CimInstance Win32_Processor; $m=Get-CimInstance Win32_ComputerSystem; " \
                 "@{board=($b.Manufacturer+' '+$b.Product);bios=($f.SMBIOSBIOSVersion);" \
                 "cpus=@($c|ForEach-Object {$_.Name});memory_bytes=$m.TotalPhysicalMemory}|ConvertTo-Json -Compress"
        p = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                           capture_output=True, encoding='utf-8', errors='replace', timeout=25)
        if p.returncode == 0:
            try:
                result.update(json.loads(p.stdout.strip('\ufeff \r\n')))
            except ValueError:
                result['inventory_error'] = 'Não foi possível interpretar a identificação Windows.'
        else:
            result['inventory_error'] = p.stderr[-2000:]
    else:
        def read(name):
            try:
                return Path('/sys/class/dmi/id', name).read_text().strip()
            except OSError:
                return ''
        result['board'] = (read('board_vendor') + ' ' + read('board_name')).strip()
        result['bios'] = (read('bios_version') + ' ' + read('bios_date')).strip()
        try:
            text = Path('/proc/cpuinfo').read_text()
            result['cpus'] = sorted(set(re.findall(r'^model name\s*:\s*(.+)$', text, re.M)))
            mem = re.search(r'^MemTotal:\s*(\d+)', Path('/proc/meminfo').read_text(), re.M)
            result['memory_bytes'] = int(mem[1]) * 1024 if mem else None
        except OSError:
            pass
    return result


def is_admin():
    return bool(ctypes.windll.shell32.IsUserAnAdmin()) if os.name == 'nt' else os.geteuid() == 0


def find_tools(root, configured_fpt=''):
    folder = Path(root) / 'tools'
    fpt = str(Path(configured_fpt).resolve()) if configured_fpt else ''
    if not fpt and folder.exists():
        candidates = sorted(p for p in folder.rglob('*') if p.name.lower() == 'fptw64.exe')
        if len(candidates) == 1:
            fpt = str(candidates[0].resolve())
    system = 'windows' if os.name == 'nt' else 'linux'
    uefi = folder / 'uefi' / system / ('UEFIExtract.exe' if os.name == 'nt' else 'uefiextract')
    # Some upstream archives use a lowercase name on Windows.
    if os.name == 'nt' and not uefi.exists():
        uefi = uefi.with_name('uefiextract.exe')
    return {'backend': 'fpt' if os.name == 'nt' else 'flashrom',
            'fpt': fpt if fpt and Path(fpt).is_file() else '',
            'flashrom': shutil.which('flashrom') or '',
            'uefiextract': str(uefi) if uefi.is_file() else '', 'administrator': is_admin()}


def command(backend, executable, action, region=None, path=None):
    if backend not in ('fpt', 'flashrom') or action not in ('probe', 'read', 'write'):
        raise ValueError('Operação de hardware desconhecida.')
    if action == 'probe':
        return [str(executable), '-i'] if backend == 'fpt' else [str(executable), '-p', 'internal']
    if region not in REGIONS or (action == 'write' and region != 'bios') or path is None:
        raise ValueError('Somente a região BIOS pode ser gravada.')
    fpt_region, flash_region, _ = REGIONS[region]
    if backend == 'fpt':
        return [str(executable)] + ([fpt_region] if fpt_region else []) + [('-d' if action == 'read' else '-f'), str(path)]
    args = [str(executable), '-p', 'internal']
    if flash_region:
        args += ['--ifd', '-i', flash_region + ':' + str(path)]
    if action == 'write':
        return args + ['--noverify-all', '-w']
    return args + (['-r'] if flash_region else ['-r', str(path)])


def parse_probe(text):
    permissions = {}
    for label, read, write in re.findall(r'^\s*(Desc|Host|ME|GbE|PDR)\s*:\s*(Yes|No)\s+(Yes|No)', text, re.M | re.I):
        permissions[label.lower()] = {'read': read.lower() == 'yes', 'write': write.lower() == 'yes'}
    locked = bool(re.search(r'Error\s*26\b|does not have read access|read.*(?:denied|locked)', text, re.I))
    return {'permissions': permissions, 'read_access_denied': locked,
            'message': 'Permissões do descriptor; proteções adicionais podem existir.'}


def run_checked(args, backend, log, writing=False):
    log.append('COMANDO: ' + subprocess.list2cmdline([str(v) for v in args]))
    p = subprocess.run(args, cwd=str(Path(args[0]).resolve().parent), stdin=subprocess.DEVNULL,
                       capture_output=True, encoding='utf-8', errors='replace',
                       timeout=None if writing else 180)
    text = p.stdout + p.stderr
    log.append(text[-2_000_000:])
    bad = p.returncode != 0 or bool(re.search(r'Error\s+\d+\s*:', text, re.I))
    if backend == 'fpt' and 'FPT Operation Passed' not in text:
        bad = True
    if bad:
        if parse_probe(text)['read_access_denied']:
            raise ValueError('Leitura negada pelo descriptor (Error 26). Nenhuma opção de força foi aplicada.')
        raise ValueError(('Falha durante gravação. Não reinicie; preserve o log e os backups.' if writing
                          else 'O motor de hardware não concluiu a operação. Consulte o log.'))
    return text


def read_region(backend, executable, region, dest, log):
    if dest.exists():
        raise ValueError('O arquivo de saída já existe; não será sobrescrito.')
    run_checked(command(backend, executable, 'read', region, dest), backend, log)
    if not dest.is_file() or dest.stat().st_size != REGIONS[region][2]:
        raise ValueError('O motor não produziu o tamanho de região esperado. Arquivo não aprovado.')
    return dest.read_bytes()


def checked_analysis(path, uefi):
    result = inspect_blob(path.read_bytes())
    result['deep'] = deep_check(path, uefi) if uefi and path.stat().st_size != 4096 else {'available': False, 'passed': False}
    if result['deep']['available'] and not result['deep']['passed']:
        result['status'] = 'deep_analysis_errors'
    return result


def perform(job, log):
    """Runs inside the elevated worker, always rechecking write prerequisites."""
    action = job['action']
    if action not in ('probe', 'backup', 'prepare', 'write'):
        raise ValueError('Operação não permitida.')
    directory = Path(job['directory']).resolve()
    if not directory.is_dir():
        raise ValueError('Pasta de trabalho ausente.')
    backend, executable = job['backend'], str(Path(job['executable']).resolve())
    if not Path(executable).is_file():
        raise ValueError('Motor não encontrado. Configure o FPT ou instale flashrom.')
    if backend == 'fpt' and Path(executable).name.lower() != 'fptw64.exe':
        raise ValueError('Selecione fptw64.exe e mantenha os arquivos auxiliares da mesma versão.')
    if backend == 'flashrom' and Path(executable).name != 'flashrom':
        raise ValueError('Executável flashrom inválido.')
    uefi = job.get('uefiextract', '')
    if action == 'probe':
        text = run_checked(command(backend, executable, 'probe'), backend, log)
        return {**parse_probe(text), 'inventory': inventory(), 'log': text}
    if action == 'backup':
        region = job['region']
        if region not in REGIONS:
            raise ValueError('Região inválida.')
        paths, reports = [], []
        for index in range(2 if job.get('double', True) else 1):
            path = directory / ('backup-%s-%d.bin' % (region, index + 1))
            data = read_region(backend, executable, region, path, log)
            paths.append(path.name)
            reports.append({'size': len(data), 'sha256': sha(data), 'analysis': checked_analysis(path, uefi)
                            if region != 'sps' else {'scope': 'SPS isolado: integridade não verificada.'}})
        equal = reports[0]['sha256'] == reports[-1]['sha256']
        return {'files': paths, 'reports': reports, 'two_reads': len(paths) == 2,
                'identical': equal, 'complete_recovery_verified': False}
    candidate_path = Path(job['candidate']).resolve()
    candidate = candidate_path.read_bytes()
    if action == 'prepare':
        if not uefi:
            raise ValueError('UEFIExtract necessário para a preparação de gravação.')
        hardware = inventory()
        text = run_checked(command(backend, executable, 'probe'), backend, log)
        perms = parse_probe(text)['permissions']
        if perms.get('host', {}).get('write') is False:
            raise ValueError('O descriptor não permite gravar a BIOS.')
        first = read_region(backend, executable, 'bios', directory / 'antes-1.bin', log)
        second = read_region(backend, executable, 'bios', directory / 'antes-2.bin', log)
        if first != second:
            raise ValueError('As duas leituras atuais diferem. Gravação bloqueada.')
        check = check_write_candidate(candidate, first, hardware['board'])
        for path in (directory / 'antes-1.bin', candidate_path):
            deep = deep_check(path, uefi)
            if not deep['passed']:
                raise ValueError('Análise UEFI detalhada reprovada: ' + '\n'.join(deep['errors'][:8]))
        result = {**check, 'candidate': str(candidate_path), 'inventory': hardware,
                  'created_at': time.time(), 'backup_files': ['antes-1.bin', 'antes-2.bin']}
        (directory / 'prepared.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        return result
    # A write requires a successful preparation, two identical backups and a fresh read.
    prepared_dir = Path(job['prepared_directory']).resolve()
    prepared = json.loads((prepared_dir / 'prepared.json').read_text(encoding='utf-8'))
    if time.time() - prepared['created_at'] > 600:
        raise ValueError('Preparação expirou. Prepare novamente antes de gravar.')
    if sha(candidate) != prepared['candidate_sha256']:
        raise ValueError('A imagem mudou desde a preparação.')
    first = (prepared_dir / 'antes-1.bin').read_bytes()
    if first != (prepared_dir / 'antes-2.bin').read_bytes() or sha(first) != prepared['current_sha256']:
        raise ValueError('Backups prévios alterados.')
    current = read_region(backend, executable, 'bios', directory / 'imediatamente-antes.bin', log)
    if current != first:
        raise ValueError('A BIOS mudou desde a preparação. Nenhuma gravação foi iniciada; prepare novamente.')
    hardware = inventory()
    check_write_candidate(candidate, current, hardware['board'])
    if not uefi or not deep_check(candidate_path, uefi)['passed']:
        raise ValueError('Verificação detalhada da imagem reprovada.')
    run_checked(command(backend, executable, 'write', 'bios', candidate_path), backend, log, writing=True)
    after = read_region(backend, executable, 'bios', directory / 'apos-gravacao.bin', log)
    if after != candidate:
        raise ValueError('A leitura posterior não coincide com a imagem. Não reinicie; preserve o log e os backups.')
    return {'written': True, 'bios_sha256': sha(after), 'readback_matches': True,
            'regions_written': ['bios'], 'boot_tested': False,
            'message': 'Gravação e leitura posterior concluídas. Inicialização ainda não testada.'}


def worker(job_path):
    job_path = Path(job_path).resolve()
    job = json.loads(job_path.read_text(encoding='utf-8'))
    directory = Path(job['directory']).resolve()
    if directory != job_path.parent or directory.parent.name != 'jobs':
        raise ValueError('Pasta de operação inválida.')
    log, result = [], {}
    try:
        result = {'ok': True, 'result': perform(job, log)}
    except Exception as exc:
        result = {'ok': False, 'error': str(exc)}
    finally:
        (directory / 'operation.log').write_text('\n'.join(log), encoding='utf-8')
        temporary = directory / 'result.tmp'
        temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
        if os.name != 'nt' and os.geteuid() == 0:
            owner = job_path.stat()
            for path in directory.rglob('*'):
                if path.is_file():
                    os.chown(path, owner.st_uid, owner.st_gid)
                    path.chmod(0o600)
        # Publish completion only after the unprivileged UI can read all artifacts.
        temporary.replace(directory / 'result.json')
    return 0 if result.get('ok') else 1


def launch_worker(job_path, launcher):
    args = [sys.executable, '-E', '-s', str(launcher), '--worker', str(job_path)]
    if not is_admin():
        if os.name == 'nt':
            def literal(value):
                return "'" + value.replace("'", "''") + "'"
            # Quote each PowerShell literal; ArgumentList receives Windows-quoted argv.
            script = "$ErrorActionPreference='Stop';try {$p=Start-Process -FilePath " + literal(sys.executable) + \
                     ' -ArgumentList ' + literal(subprocess.list2cmdline(args[1:])) + \
                     ' -Verb RunAs -Wait -PassThru;exit $p.ExitCode}catch{exit 1}'
            args = ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script]
        else:
            if not shutil.which('pkexec'):
                raise ValueError('Instale/ative o polkit (pkexec) para autorizar operações de hardware no CachyOS.')
            args = ['pkexec'] + args
    return subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
