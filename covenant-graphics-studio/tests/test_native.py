import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QFileDialog,QInputDialog,QDialog

from covenant_studio.native import MainWindow
from covenant_studio.firmware import load_firmware
from covenant_studio.model import make_project,validate_project,slot

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('COVENANT_BIOS_FIXTURE'),'Private BIOS fixture not configured')
class NativeFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.stock=load_firmware(os.environ['COVENANT_BIOS_FIXTURE'])
        from covenant_studio.firmware import sha
        donor=(ROOT/'assets/doadora-hii.json').read_bytes();cls.donor=json.loads(donor)
        cls.cat=json.loads((ROOT/'assets/catalogo.json').read_text());cls.donor_sha=sha(donor)
        cls.project=make_project(cls.stock,cls.donor,cls.cat,cls.donor_sha)
    def setUp(self):
        self.window=MainWindow(ROOT);self.window.loaded((self.stock,copy.deepcopy(self.project)));self.window.show();self.app.processEvents()
    def tearDown(self):
        self.window.dirty=False;self.window.close();self.window.deleteLater();self.app.processEvents()
    def csm_control(self):
        return next(c for c in self.window.project['controls'] if c['page']=='home' and c['label']=='CSM Support')
    def test_window_is_native_and_no_browser_is_opened(self):
        with patch('webbrowser.open',side_effect=AssertionError('Browser used')):
            self.window.redraw();self.app.processEvents()
        self.assertEqual(self.window.page()['id'],'home');self.assertGreater(self.window.page_tree.topLevelItem(0).childCount(),100)
    def test_double_click_test_targets_stock_csm_not_donor_offset(self):
        c=self.csm_control();self.window.select_control(c['id'])
        with patch.object(QInputDialog,'getItem',return_value=('Enabled  [1]',True)):
            self.window.activate_control(c['id'])
        q=self.window.qmap[c['target_id']]
        self.assertEqual(q['offset'],0x74);self.assertEqual(self.window.project['test_values'][slot(q)],'1')
        self.assertEqual(self.window.display_value(c),'Enabled')
    def test_custom_stock_control_and_geometry_roundtrip(self):
        c=self.csm_control();qid=c['target_id'];self.window.stock_tree.setCurrentItem(self.window.stock_items[qid])
        self.window.add_stock_control();created=self.window.control();self.assertTrue(created['id'].startswith('custom-'))
        self.window.geometry[0].setValue(95)
        validate_project(self.window.project,self.stock,self.donor,self.cat,self.donor_sha)
        self.assertLessEqual(sum([created['rect'][0],created['rect'][2]]),1.000001)
    def test_replace_asset_uses_project_not_original_image_file(self):
        aid=self.cat['brand'];path=ROOT/'assets/imagens'/aid;original=path.read_bytes()
        self.window.import_asset(aid,original)
        self.assertIn(aid,self.window.project['asset_overrides']);self.assertEqual(path.read_bytes(),original)
    def test_save_reopen_keeps_shortcuts_and_values(self):
        c=self.csm_control();self.window.select_control(c['id']);self.window.shortcut.setText('F5');self.window.change_shortcut()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'project.json';self.window.save_to(path)
            c['shortcut']='';self.window.load_project_from(path)
            restored=self.window.cmap[c['id']];self.assertEqual(restored['shortcut'],'F5')
    def test_shortcut_opens_actual_target_value_editor(self):
        c=self.csm_control();self.window.select_control(c['id']);self.window.shortcut.setText('F5');self.window.change_shortcut()
        self.window.activateWindow();self.window.canvas.setFocus();self.app.processEvents()
        with patch.object(QInputDialog,'getItem',return_value=('Disabled  [0]',True)) as dialog:
            QTest.keyClick(self.window,Qt.Key.Key_F5);self.app.processEvents()
            self.assertTrue(dialog.called)
        q=self.window.qmap[c['target_id']];self.assertEqual(self.window.project['test_values'][slot(q)],'0')
    def test_export_button_creates_project_bundle_only(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'links.zip'
            with patch.object(QFileDialog,'getSaveFileName',return_value=(str(path),'')):
                QTest.mouseClick(self.window.export_button,Qt.MouseButton.LeftButton)
            self.assertTrue(path.is_file())
            import zipfile
            with zipfile.ZipFile(path) as z:
                manifest=json.loads(z.read('manifesto.json'));self.assertFalse(manifest['runtime_adapter_implemented'])
    def test_open_bios_button_reads_the_actual_file(self):
        self.window.dirty=False
        with patch.object(QFileDialog,'getOpenFileName',return_value=(os.environ['COVENANT_BIOS_FIXTURE'],'')):
            QTest.mouseClick(self.window.open_button,Qt.MouseButton.LeftButton)
        deadline=time.monotonic()+40
        while self.window.busy and time.monotonic()<deadline:
            self.app.processEvents();QTest.qWait(20)
        self.assertFalse(self.window.busy);self.assertEqual(self.window.stock['sha256'],self.stock['sha256'])


if __name__=='__main__':unittest.main()
