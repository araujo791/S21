"""Local application state; importing or constructing it opens no network listener."""
import json
import os
import secrets
import sys
import threading
import time
import uuid
from pathlib import Path
from .core import sha, MIB
from .hardware import inventory, find_tools, launch_worker


def app_root():
    return Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]


class Workspace:
    def __init__(self, data, root=None, initialize_inventory=True):
        self.root = Path(root) if root else app_root()
        self.data = Path(data).resolve()
        self.data.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in ('files', 'jobs'):
            (self.data / name).mkdir(exist_ok=True, mode=0o700)
        self.token = secrets.token_urlsafe(32)
        self.jobs, self.prepared, self.lock = {}, {}, threading.Lock()
        self.fpt = ''
        self.hardware = inventory() if initialize_inventory else {}

    def file(self, ident):
        if not isinstance(ident, str) or len(ident) != 32 or any(c not in '0123456789abcdef' for c in ident):
            raise ValueError('Identificador de arquivo inválido.')
        path = self.data / 'files' / (ident + '.bin')
        if not path.is_file():
            raise ValueError('Arquivo não encontrado nesta pasta portátil.')
        return path

    def save_blob(self, data, name):
        if not 0 < len(data) <= 16 * MIB:
            raise ValueError('Arquivo vazio ou maior que 16 MiB.')
        ident = uuid.uuid4().hex
        p = self.data / 'files' / (ident + '.bin')
        with p.open('xb') as out:
            out.write(data)
        p.chmod(0o600)
        title = Path(name.replace('\\', '/')).name[:120] or 'firmware.bin'
        metadata = {'id': ident, 'name': title, 'size': len(data), 'sha256': sha(data)}
        p.with_suffix('.meta.json').write_text(json.dumps(metadata, ensure_ascii=False), encoding='utf-8')
        return metadata

    def tools(self):
        return find_tools(self.root, self.fpt)

    def start_job(self, payload):
        if not self.lock.acquire(blocking=False):
            raise ValueError('Já existe uma operação de hardware em andamento.')
        try:
            action = payload.get('action')
            if action not in ('probe', 'backup', 'prepare', 'write'):
                raise ValueError('Operação inválida.')
            tools = self.tools()
            backend = tools['backend']
            executable = tools[backend]
            if not executable:
                raise ValueError('Windows: coloque sua pasta do FPT em tools/FPT ou configure o caminho. CachyOS: instale flashrom.')
            ident = uuid.uuid4().hex
            directory = self.data / 'jobs' / ident
            directory.mkdir(mode=0o700)
            job = {'action': action, 'directory': str(directory), 'backend': backend,
                   'executable': executable, 'uefiextract': tools['uefiextract']}
            if action == 'backup':
                region = payload.get('region')
                if region not in ('full', 'bios', 'descriptor', 'sps'):
                    raise ValueError('Região inválida.')
                job.update(region=region, double=True)
            if action in ('prepare', 'write'):
                candidate = self.file(payload.get('file'))
                job['candidate'] = str(candidate)
            if action == 'write':
                preparation = self.prepared.pop(payload.get('preparation', ''), None)
                if not preparation or preparation['file'] != payload.get('file'):
                    raise ValueError('Prepare e confira esta imagem antes de gravar.')
                if payload.get('confirmation') != 'GRAVAR BIOS' or payload.get('acknowledged') is not True:
                    raise ValueError('Confirme os dados e digite GRAVAR BIOS.')
                if preparation['sha256'] != sha(candidate.read_bytes()):
                    raise ValueError('Arquivo mudou desde a preparação.')
                job['prepared_directory'] = preparation['directory']
            job_path = directory / 'job.json'
            job_path.write_text(json.dumps(job, indent=2), encoding='utf-8')
            state = {'id': ident, 'action': action, 'status': 'running',
                     'message': 'Aguardando autorização do sistema ou execução. Não feche durante gravação.'}
            self.jobs[ident] = state
            thread = threading.Thread(target=self.monitor, args=(job_path, state, payload), daemon=True)
            thread.start()
            return dict(state)
        except Exception:
            self.lock.release()
            raise

    def monitor(self, job_path, state, payload):
        directory = job_path.parent
        try:
            proc = launch_worker(job_path, self.root / 'convenant_bios_tools.py')
            while not (directory / 'result.json').is_file():
                if proc and proc.poll() is not None:
                    # A completed worker writes its result before exiting.
                    if not (directory / 'result.json').is_file():
                        raise ValueError('Operação não iniciou ou autorização foi cancelada. Nenhum resultado foi produzido.')
                time.sleep(0.35)
            outcome = json.loads((directory / 'result.json').read_text(encoding='utf-8'))
            state.update(**outcome)
            if outcome['ok']:
                result = outcome['result']
                state['artifacts'] = []
                for path in directory.glob('*.bin'):
                    meta = self.save_blob(path.read_bytes(), path.name)
                    state['artifacts'].append(meta)
                if state['action'] == 'prepare':
                    key = secrets.token_urlsafe(24)
                    self.prepared[key] = {'directory': str(directory), 'file': payload['file'],
                                          'sha256': result['candidate_sha256']}
                    state['preparation'] = key
            state['log'] = (directory / 'operation.log').read_text(encoding='utf-8', errors='replace')[-2_000_000:]
            state['status'] = 'done' if outcome['ok'] else 'error'
        except Exception as exc:
            state.update(status='error', ok=False, error=str(exc))
        finally:
            self.lock.release()
