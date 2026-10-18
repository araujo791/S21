"""No hardware access: exercise command boundaries, worker verification and HTTP."""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from convenant import core, hardware
from convenant.server import App

ROOT = Path(__file__).resolve().parents[1]


class CommandBoundaries(unittest.TestCase):
    def test_fpt_region_only_backup(self):
        self.assertEqual(hardware.command('fpt', 'fptw64.exe', 'read', 'bios', 'a.bin'),
                         ['fptw64.exe', '-bios', '-d', 'a.bin'])

    def test_full_read_does_not_restrict_to_bios(self):
        self.assertEqual(hardware.command('fpt', 'fptw64.exe', 'read', 'full', 'a.bin'),
                         ['fptw64.exe', '-d', 'a.bin'])

    def test_flashrom_region_sized_write_verifies_selected_region(self):
        self.assertEqual(hardware.command('flashrom', 'flashrom', 'write', 'bios', 'a.bin'),
                         ['flashrom', '-p', 'internal', '--ifd', '-i', 'bios:a.bin', '--noverify-all', '-w'])

    def test_no_force_or_arbitrary_operations(self):
        for backend in ('fpt', 'flashrom'):
            for operation in ('erase', 'unlock', 'force', 'reset', 'arbitrary'):
                with self.assertRaises(ValueError):
                    hardware.command(backend, 'tool', operation, 'bios', 'a.bin')
            for region in ('full', 'sps', 'descriptor'):
                with self.assertRaises(ValueError):
                    hardware.command(backend, 'tool', 'write', region, 'a.bin')

    def test_probe_permissions_preserve_locked_sps(self):
        value = hardware.parse_probe('Desc : Yes No\nHost : Yes Yes\nME : No No\n')
        self.assertFalse(value['permissions']['me']['read'])
        self.assertTrue(value['permissions']['host']['write'])

    def test_error26_even_zero_exit_is_failure(self):
        p = type('P', (), {'stdout': 'Error 26: The host CPU does not have read access', 'stderr': '', 'returncode': 0})()
        with patch('subprocess.run', return_value=p):
            with self.assertRaisesRegex(ValueError, 'Error 26'):
                hardware.run_checked(['tool', '-d', 'out'], 'fpt', [])

    def test_success_without_file_is_not_backup(self):
        with tempfile.TemporaryDirectory() as tmp, patch('convenant.hardware.run_checked'):
            with self.assertRaisesRegex(ValueError, 'tamanho'):
                hardware.read_region('fpt', 'tool', 'bios', Path(tmp) / 'out', [])

    def test_existing_backup_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'out'; path.write_bytes(b'keep')
            with self.assertRaisesRegex(ValueError, 'sobrescrito'):
                hardware.read_region('fpt', 'tool', 'bios', path, [])
            self.assertEqual(path.read_bytes(), b'keep')

    def test_all_windows_write_argv_use_region_flag(self):
        args = hardware.command('fpt', 'fptw64.exe', 'write', 'bios', r'C:\Com espaços\bios.bin')
        self.assertEqual(args[1:3], ['-bios', '-f'])
        self.assertEqual(len(args), 4)


class HttpBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.app = App(Path(cls.tmp.name))
        cls.thread = threading.Thread(target=cls.app.serve_forever, daemon=True); cls.thread.start()
        cls.url = 'http://127.0.0.1:%d' % cls.app.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.app.shutdown(); cls.app.server_close(); cls.thread.join(); cls.tmp.cleanup()

    def request(self, path, body=None, token=True, origin=None, host=None):
        headers = {'X-Convenant-Token': self.app.token} if token else {}
        if origin: headers['Origin'] = origin
        if host: headers['Host'] = host
        data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
        return urllib.request.urlopen(urllib.request.Request(self.url + path, data=data, headers=headers), timeout=10)

    def test_interface_and_no_implicit_hardware(self):
        with patch('convenant.server.launch_worker') as worker:
            with self.request('/') as response:
                self.assertIn(b'CONVENANT', response.read())
            worker.assert_not_called()

    def test_unauthenticated_post_is_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.request('/api/upload', b'abc', token=False)
        self.assertEqual(cm.exception.code, 403)

    def test_cross_origin_is_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.request('/api/settings', {}, origin='https://example.org')
        self.assertEqual(cm.exception.code, 403)

    def test_host_rebinding_is_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.request('/', host='attacker.invalid')
        self.assertEqual(cm.exception.code, 403)

    def test_uploaded_firmware_requires_token_to_download(self):
        with self.request('/api/upload?name=example.bin', b'abc') as response:
            ident = json.loads(response.read())['id']
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.request('/api/download/' + ident, token=False)
        self.assertEqual(cm.exception.code, 403)
        with self.request('/api/download/' + ident) as response:
            self.assertEqual(response.read(), b'abc')

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            self.app.file('../../etc/passwd')

    def test_busy_worker_blocks_second_operation(self):
        self.app.lock.acquire()
        try:
            with self.assertRaisesRegex(ValueError, 'andamento'):
                self.app.start_job({'action': 'backup', 'region': 'bios'})
        finally:
            self.app.lock.release()

    def test_write_without_preparation_cannot_start_worker(self):
        meta = self.app.save_blob(b'abc', 'a.bin')
        with patch.object(self.app, 'tools', return_value={'backend':'fpt','fpt':sys.executable,'uefiextract':''}), patch('convenant.server.launch_worker') as worker:
            with self.assertRaisesRegex(ValueError, 'Prepare'):
                self.app.start_job({'action':'write','file':meta['id'],'confirmation':'GRAVAR BIOS','acknowledged':True})
            worker.assert_not_called()


class PrivateFirmwareFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get('MACHINIST_BIOS_BASE', ROOT / 'inputs/bios-1.bin'))
        if not path.is_file():
            raise unittest.SkipTest('Provide MACHINIST_BIOS_BASE for real-firmware checks')
        cls.base = path.read_bytes()

    def test_good_002_is_recognized_and_006_not_silently_accepted(self):
        a = core.inspect_blob(self.base)
        self.assertEqual(a['profile'], '002-original'); self.assertFalse(a['issues'])
        wrong = bytearray(self.base); wrong[0x100000] ^= 1
        with self.assertRaises(ValueError):
            core.check_write_candidate(bytes(wrong), self.base, 'MACHINIST E5-D8-MAX')

    def test_wrong_board_blocked(self):
        with self.assertRaisesRegex(ValueError, 'placa'):
            core.check_write_candidate(self.base, self.base, 'Other board')

    def test_full_spi_cannot_be_used_as_bios_region(self):
        with self.assertRaisesRegex(ValueError, '8 MiB'):
            core.check_write_candidate(self.base * 2, self.base, 'E5-D8-MAX')

    def test_nvram_difference_not_counted_as_code_difference(self):
        second = bytearray(self.base); second[0x170] ^= 1
        report = core.compare_blobs(self.base, bytes(second))
        self.assertEqual(report['whole']['different_bytes'], 1)
        self.assertEqual(report['code_excluding_first_512KiB_nvram']['different_bytes'], 0)

    def test_deep_parser_failure_detected_even_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'image.bin'; p.write_bytes(self.base)
            process = type('P', (), {'stdout':'parse: not a single Volume Top File is found, the image may be corrupted\n', 'stderr':'', 'returncode':0})()
            with patch('convenant.core.subprocess.run', return_value=process):
                r = core.deep_check(p, 'tool')
            self.assertFalse(r['passed'])
            self.assertTrue(any('Volume Top File' in e for e in r['errors']))

    def test_write_worker_requires_two_unchanged_preflight_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); tool = directory / 'fptw64.exe'; tool.write_bytes(b'fake')
            candidate = directory / 'candidate.bin'; candidate.write_bytes(self.base)
            prepared = directory / 'prepared'; prepared.mkdir()
            (prepared / 'prepared.json').write_text(json.dumps({'created_at':__import__('time').time(), 'candidate_sha256':core.sha(self.base),'current_sha256':core.sha(self.base)}))
            (prepared / 'antes-1.bin').write_bytes(self.base); (prepared / 'antes-2.bin').write_bytes(b'changed')
            job = {'action':'write','directory':str(directory),'backend':'fpt','executable':str(tool),'candidate':str(candidate),'prepared_directory':str(prepared),'uefiextract':'tool'}
            with patch('convenant.hardware.run_checked') as run:
                with self.assertRaisesRegex(ValueError, 'Backups'):
                    hardware.perform(job, [])
                run.assert_not_called()

    def fake_controller(self, directory, bad_write=False):
        state = directory / 'chip-state.bin'; state.write_bytes(self.base)
        tool = directory / 'fptw64.exe'
        tool.write_text('#!' + sys.executable + '\n'
                        'import sys,shutil\nfrom pathlib import Path\n'
                        'state=Path(' + repr(str(state)) + ')\n'
                        'args=sys.argv[1:]\n'
                        'if "-d" in args: shutil.copyfile(state,args[args.index("-d")+1])\n'
                        'if "-f" in args:\n'
                        ' shutil.copyfile(args[args.index("-f")+1],state)\n'
                        ' Path(' + repr(str(directory / 'write-marker')) + ').write_text("written")\n'
                        + (' data=bytearray(state.read_bytes());data[0x170]^=1;state.write_bytes(data)\n' if bad_write else '') +
                        'print("Host : Yes Yes\\nME : No No\\nFPT Operation Passed")\n')
        tool.chmod(0o755)
        candidate = directory / 'candidate with spaces.bin'
        changed = bytearray(self.base); changed[0x2C170] ^= 1; candidate.write_bytes(changed)
        prepared = directory / 'prepared'; prepared.mkdir()
        writing = directory / 'writing'; writing.mkdir()
        common = {'backend':'fpt','executable':str(tool),'candidate':str(candidate),'uefiextract':'fake-uefi'}
        prepare = {**common,'action':'prepare','directory':str(prepared)}
        write = {**common,'action':'write','directory':str(writing),'prepared_directory':str(prepared)}
        return state, candidate, prepare, write

    def test_preparation_and_write_with_real_fake_cli_and_readback(self):
        with tempfile.TemporaryDirectory(prefix='convenant with spaces ') as tmp:
            directory = Path(tmp)
            state, candidate, prepare, write = self.fake_controller(directory)
            with patch('convenant.hardware.inventory', return_value={'board':'MACHINIST E5-D8-MAX'}), patch('convenant.hardware.deep_check', return_value={'passed':True}):
                prepared = hardware.perform(prepare, [])
                self.assertTrue(prepared['nvram_will_change'])
                result = hardware.perform(write, [])
            self.assertTrue(result['readback_matches'])
            self.assertEqual(state.read_bytes(), candidate.read_bytes())
            self.assertTrue((directory / 'write-marker').is_file())
            self.assertEqual((Path(prepare['directory'])/'antes-1.bin').read_bytes(), self.base)

    def test_changed_chip_since_preparation_blocks_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            state, candidate, prepare, write = self.fake_controller(directory)
            with patch('convenant.hardware.inventory', return_value={'board':'MACHINIST E5-D8-MAX'}), patch('convenant.hardware.deep_check', return_value={'passed':True}):
                hardware.perform(prepare, [])
                changed = bytearray(self.base); changed[0x170] ^= 1; state.write_bytes(changed)
                with self.assertRaisesRegex(ValueError,'mudou desde'):
                    hardware.perform(write, [])
            self.assertFalse((directory/'write-marker').exists())

    def test_readback_mismatch_is_failure_after_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            state, candidate, prepare, write = self.fake_controller(directory, bad_write=True)
            with patch('convenant.hardware.inventory', return_value={'board':'MACHINIST E5-D8-MAX'}), patch('convenant.hardware.deep_check', return_value={'passed':True}):
                hardware.perform(prepare, [])
                with self.assertRaisesRegex(ValueError,'Não reinicie'):
                    hardware.perform(write, [])
            self.assertTrue((directory/'write-marker').exists())
            self.assertNotEqual(state.read_bytes(),candidate.read_bytes())


if __name__ == '__main__':
    unittest.main()
