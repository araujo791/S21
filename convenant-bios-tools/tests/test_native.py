"""Qt Widgets workflow checks, with no browser, listener or physical flash."""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from convenant.native import MainWindow, STYLE
from convenant import hardware


class NativeWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(STYLE)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        with patch('socket.socket', side_effect=AssertionError('No socket allowed')), patch('webbrowser.open', side_effect=AssertionError('No browser allowed')):
            self.window = MainWindow(data=Path(self.tmp.name), identify=False)
            self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.wait_done()
        self.window.close(); self.app.processEvents(); self.tmp.cleanup()

    def wait_done(self):
        deadline = time.time() + 90
        while self.window.busy and time.time() < deadline:
            self.app.processEvents(); QTest.qWait(10)
        self.assertFalse(self.window.busy, 'Background operation did not finish')
        self.app.processEvents()

    def fixture(self):
        path = Path(os.environ.get('MACHINIST_BIOS_BASE','missing.bin'))
        if not path.is_file(): self.skipTest('Provide MACHINIST_BIOS_BASE')
        return path

    def import_fixtures(self, paths):
        with patch.object(QFileDialog,'getOpenFileNames',return_value=([str(p) for p in paths],'')):
            self.window.choose_files()
        self.wait_done()
        self.assertNotIn('error',self.window.last_report)
        return {f['name']: f['id'] for f in self.window.files}

    def select(self, widget, ident):
        widget.setCurrentIndex(widget.findData(ident))

    def test_native_navigation_without_network_or_browser(self):
        self.assertEqual(self.window.pages.count(),6)
        for index in range(6):
            self.window.navigation.setCurrentRow(index)
            self.app.processEvents();self.assertEqual(self.window.pages.currentIndex(),index)
        self.assertFalse(self.window.write_confirm.isEnabled())

    def test_analyze_via_native_button(self):
        source=self.fixture();ids=self.import_fixtures([source])
        self.window.navigation.setCurrentRow(2)
        self.select(self.window.analysis_file,ids[source.name])
        QTest.mouseClick(self.window.analyze_button,Qt.LeftButton);self.wait_done()
        report=self.window.last_report
        self.assertEqual(report['profile'],'002-original');self.assertFalse(report['issues'])
        self.assertIn('CPUID',self.window.summary.toPlainText())

    def test_compare_via_native_button(self):
        source=self.fixture();second=Path(self.tmp.name)/'second.bin';second.write_bytes(source.read_bytes())
        ids=self.import_fixtures([source,second]);self.window.navigation.setCurrentRow(2)
        self.select(self.window.compare_first,ids[source.name]);self.select(self.window.compare_second,ids[second.name])
        QTest.mouseClick(self.window.compare_button,Qt.LeftButton);self.wait_done()
        self.assertTrue(self.window.last_report['identical'])

    def test_microcode_generation_via_native_button(self):
        source=self.fixture()
        refs=[Path(os.environ.get(key,'missing.bin')) for key in ('INTEL_UCODE_306F2','INTEL_UCODE_406F1')]
        if not all(p.is_file() for p in refs):self.skipTest('Provide Intel references')
        second=Path(self.tmp.name)/'second.bin';second.write_bytes(source.read_bytes())
        ids=self.import_fixtures([source,second,*refs]);self.window.navigation.setCurrentRow(3)
        for widget,path in zip((self.window.build_base,self.window.build_second,self.window.build_v3,self.window.build_v4),(source,second,*refs)):
            self.select(widget,ids[path.name])
        QTest.mouseClick(self.window.build_button,Qt.LeftButton);self.wait_done()
        from convenant.core import UPDATED_CODE
        self.assertEqual(self.window.last_report['manifest']['output_code_sha256'],UPDATED_CODE)
        candidate=self.window.workspace.file(self.window.last_report['file']['id']).read_bytes()
        self.assertEqual(candidate[:0x80000],source.read_bytes()[:0x80000])
        self.assertTrue(self.window.last_report['manifest']['own_board_nvram_preserved'])

    def test_write_selection_invalidates_preparation(self):
        self.window.preparation='example';self.window.write_confirm.setEnabled(True)
        self.window.write_file.addItem('another', 'new');self.window.write_file.setCurrentIndex(1)
        self.assertIsNone(self.window.preparation);self.assertFalse(self.window.write_confirm.isEnabled())

    def test_closing_busy_window_is_blocked(self):
        self.window.set_busy(True)
        with patch.object(QMessageBox,'information'):
            self.assertFalse(self.window.close())
        self.window.set_busy(False)

    def test_frozen_worker_uses_executable_not_python_arguments(self):
        with patch('sys.frozen',True,create=True), patch('convenant.hardware.is_admin',return_value=True), patch('convenant.hardware.subprocess.Popen') as process:
            hardware.launch_worker(Path(self.tmp.name)/'job.json',Path('/not-used.py'))
            args=process.call_args.args[0]
            self.assertEqual(args[1:3],['--worker',str(Path(self.tmp.name)/'job.json')])
            self.assertNotIn('-E',args)


if __name__=='__main__':unittest.main()
