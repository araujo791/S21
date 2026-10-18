"""Authenticated loopback interface. Backups stay in the portable folder."""
import json
import os
import secrets
import subprocess
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .core import MIB, build_candidate, compare_blobs, deep_check, descriptor, inspect_blob, sha
from .hardware import find_tools, inventory, launch_worker

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).with_name('static')
ASSETS = {'/': ('index.html', 'text/html; charset=utf-8'),
          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
          '/style.css': ('style.css', 'text/css; charset=utf-8')}


class App(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, data, port=0):
        self.root = ROOT
        self.data = Path(data).resolve()
        self.data.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in ('files', 'jobs'):
            (self.data / name).mkdir(exist_ok=True, mode=0o700)
        self.token = secrets.token_urlsafe(32)
        self.jobs, self.prepared, self.lock = {}, {}, threading.Lock()
        self.fpt = ''
        self.hardware = inventory()
        super().__init__(('127.0.0.1', port), Handler)

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


class Handler(BaseHTTPRequestHandler):
    server_version = 'ConvenantBiosTools/' + __version__

    def log_message(self, *_args):
        pass

    def local(self):
        port = self.server.server_address[1]
        return self.headers.get('Host') in (f'127.0.0.1:{port}', f'localhost:{port}')

    def respond(self, status, data, content_type='application/json; charset=utf-8', filename=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; "
                         "connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        if filename:
            self.send_header('Content-Disposition', 'attachment; filename="' + filename + '"')
        self.end_headers()
        self.wfile.write(data)

    def json(self, status, value):
        self.respond(status, json.dumps(value, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        if not self.local():
            return self.json(403, {'error': 'Host local inválido.'})
        path = urlsplit(self.path).path
        if path in ASSETS:
            name, mime = ASSETS[path]
            return self.respond(200, (STATIC / name).read_bytes(), mime)
        if path == '/api/config':
            return self.json(200, {'token': self.server.token, 'version': __version__,
                                   'inventory': self.server.hardware, 'tools': self.server.tools(),
                                   'data_directory': str(self.server.data)})
        # Reports, uploaded firmware and job logs require the session token too.
        if not secrets.compare_digest(self.headers.get('X-Convenant-Token', ''), self.server.token):
            return self.json(403, {'error': 'Sessão local inválida.'})
        try:
            if path.startswith('/api/jobs/'):
                state = self.server.jobs.get(path.rsplit('/', 1)[1])
                return self.json(200, state) if state else self.json(404, {'error': 'Operação não encontrada.'})
            if path.startswith('/api/download/'):
                p = self.server.file(path.rsplit('/', 1)[1])
                return self.respond(200, p.read_bytes(), 'application/octet-stream', 'convenant-' + p.stem + '.bin')
            if path == '/api/files':
                files = [json.loads(p.read_text(encoding='utf-8')) for p in (self.server.data / 'files').glob('*.meta.json')]
                return self.json(200, files)
            return self.json(404, {'error': 'Rota não encontrada.'})
        except (OSError, ValueError) as exc:
            return self.json(400, {'error': str(exc)})

    def do_POST(self):
        origin = self.headers.get('Origin')
        if (not self.local() or (origin and origin != 'http://' + self.headers.get('Host', ''))
                or not secrets.compare_digest(self.headers.get('X-Convenant-Token', ''), self.server.token)):
            return self.json(403, {'error': 'Solicitação externa ou sessão inválida.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16 * MIB:
                return self.json(413, {'error': 'Limite de arquivo: 16 MiB.'})
            self.connection.settimeout(40)
            body = self.rfile.read(size)
            if len(body) != size:
                raise ValueError('Envio incompleto.')
            path = urlsplit(self.path).path
            if path == '/api/upload':
                name = parse_qs(urlsplit(self.path).query).get('name', ['firmware.bin'])[0]
                return self.json(200, self.server.save_blob(body, name))
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError('Objeto JSON esperado.')
            if path == '/api/settings':
                fpt = data.get('fpt', '')
                if not isinstance(fpt, str):
                    raise ValueError('Caminho do FPT inválido.')
                if fpt and (not Path(fpt).is_file() or Path(fpt).name.lower() != 'fptw64.exe'):
                    raise ValueError('Selecione o caminho completo para fptw64.exe.')
                self.server.fpt = fpt
                return self.json(200, self.server.tools())
            if path == '/api/analyze':
                p = self.server.file(data.get('file'))
                report = inspect_blob(p.read_bytes())
                uefi = self.server.tools()['uefiextract']
                report['deep'] = deep_check(p, uefi) if uefi and p.stat().st_size != 4096 else {'available': False, 'passed': False}
                if report['deep']['available'] and not report['deep']['passed']:
                    report['status'] = 'deep_analysis_errors'
                p.with_suffix('.analysis.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
                return self.json(200, report)
            if path == '/api/compare':
                a, b = (self.server.file(data.get(k)).read_bytes() for k in ('first', 'second'))
                return self.json(200, compare_blobs(a, b))
            if path == '/api/extract':
                b = self.server.file(data.get('file')).read_bytes()
                if len(b) != 16 * MIB:
                    raise ValueError('Selecione uma imagem SPI de 16 MiB.')
                desc = descriptor(b)
                region = next(r for r in desc['regions'] if r['name'] == 'bios')
                if not region['present'] or region['end'] > len(b) or region['end'] - region['start'] != 8 * MIB:
                    raise ValueError('Região BIOS de 8 MiB não encontrada.')
                return self.json(200, self.server.save_blob(b[region['start']:region['end']], 'BIOS-extraida-8MiB.bin'))
            if path == '/api/build':
                values = [self.server.file(data.get(k)).read_bytes() for k in ('base', 'second', 'v3', 'v4')]
                image, manifest = build_candidate(*values)
                meta = self.server.save_blob(image, 'E5-D8-MAX-002-V3-V4-EXPERIMENTAL-8MiB.bin')
                self.server.file(meta['id']).with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
                return self.json(200, {'file': meta, 'manifest': manifest})
            if path == '/api/job':
                return self.json(202, self.server.start_job(data))
            if path == '/api/shutdown':
                if self.server.lock.locked():
                    raise ValueError('Aguarde a operação de hardware terminar antes de fechar.')
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return self.json(200, {'closed': True})
            return self.json(404, {'error': 'Operação não encontrada.'})
        except (ValueError, OSError, KeyError, TimeoutError, subprocess.SubprocessError) as exc:
            return self.json(400, {'error': str(exc)})


def serve(args):
    data = args.data or ROOT / 'dados-convenant'
    try:
        server = App(data, args.port)
    except OSError as exc:
        print('Não foi possível abrir a pasta portátil ou iniciar: ' + str(exc))
        return 1
    host, port = server.server_address
    address = 'http://%s:%d/' % (host, port)
    print('Convenant BIOS Tools — interface local: ' + address, flush=True)
    print('Arquivos locais: ' + str(server.data), flush=True)
    print('Mantenha esta janela aberta. Nenhum acesso ao chip ocorre ao iniciar.', flush=True)
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if server.lock.locked():
            print('Há uma operação de hardware ativa. Não interrompa nem reinicie durante gravação.', flush=True)
            # The worker is a separate process; closing the UI must not kill it.
    finally:
        server.server_close()
    return 0
