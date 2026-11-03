"""Regressions for the actual Windows JPEG packaging/startup failure."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]


class ImageStartupTests(unittest.TestCase):
    def child(self,body):
        env=os.environ.copy();env['QT_QPA_PLATFORM']='offscreen'
        code='''
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QImage, QImageReader, QPixmap
from covenant_studio.native import MainWindow
import json, base64
app=QApplication([])
root=Path.cwd()
'''+body
        p=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,capture_output=True,text=True,timeout=40)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
        return p.stdout
    def test_missing_jpeg_decoder_is_reproduced_and_png_fallback_starts(self):
        self.child('''
QCoreApplication.setLibraryPaths([])
probe=QImage(str(root/'assets/imagens/1920x1080-5b69ebfb18c44077.jpg'))
assert probe.isNull(), 'The regression did not disable JPEG decoding'
w=MainWindow(root);w.show();app.processEvents()
assert '1920x1080-5b69ebfb18c44077.jpg' in w.fallbacks_used
assert '107x15-57989313d7edf2e8.jpg' in w.fallbacks_used
assert w.asset_pixmap(w.catalog['background']).width()==1920
w.close()
''')
    def test_null_background_is_descriptive_error_not_zero_division(self):
        self.child('''
from unittest.mock import patch
w=MainWindow(root)
with patch.object(w,'asset_pixmap',return_value=QPixmap()):
    try:w.redraw()
    except ValueError as exc:assert 'fundo' in str(exc)
    else:raise AssertionError('Null background was not rejected')
w.close()
''')
    def test_missing_fallback_file_has_actionable_error(self):
        self.child('''
import tempfile,shutil
QCoreApplication.setLibraryPaths([])
with tempfile.TemporaryDirectory() as temp:
    r=Path(temp);shutil.copytree(root/'assets',r/'assets')
    (r/'assets/fallback-png/1920x1080-5b69ebfb18c44077.png').unlink()
    try:w=MainWindow(r)
    except ValueError as exc:assert 'alternativa ausente' in str(exc)
    else:raise AssertionError('Missing fallback was not reported')
''')
    def test_bad_edited_image_does_not_silently_show_original(self):
        self.child('''
w=MainWindow(root);aid=w.catalog['background'];w.pixmaps.pop(aid,None)
w.project={'asset_overrides':{aid:base64.b64encode(b'not an image').decode()}}
try:w.asset_pixmap(aid)
except ValueError as exc:assert 'imagem editada' in str(exc)
else:raise AssertionError('Bad edit was silently replaced')
w.project=None;w.close()
''')
    def test_every_default_jpeg_has_a_valid_builtin_png_fallback(self):
        self.child('''
import hashlib
QCoreApplication.setLibraryPaths([])
w=MainWindow(root)
ids=[i['id'] for i in w.catalog['images'] if i['id'].endswith(('.jpg','.jpeg'))]
assert len(ids)==45
for aid in ids:
    p=w.asset_pixmap(aid);meta=w.asset_info[aid]
    assert (p.width(),p.height())==(meta['width'],meta['height'])
assert len(w.fallbacks_used)==45
w.close()
''')


@unittest.skipUnless(os.environ.get('COVENANT_QT_WHEEL') and os.environ.get('COVENANT_RUNTIME_PACKAGE'),
                     'Windows runtime fixtures not configured')
class WindowsImagePackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('graphics_packager',ROOT/'scripts/empacotar-windows.py')
        cls.pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.pack)
        cls.wheel=Path(os.environ['COVENANT_QT_WHEEL']);cls.runtime=Path(os.environ['COVENANT_RUNTIME_PACKAGE'])
    def seed(self,folder):
        names={'qt6core.dll','qt6gui.dll','vcruntime140.dll'}
        with zipfile.ZipFile(self.runtime) as z:
            for n in z.namelist():
                if Path(n).name.casefold() in names:
                    p=folder/'runtime/windows'/Path(n).name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
    def test_plugin_is_added_to_runtime_that_originally_lacked_it(self):
        with tempfile.TemporaryDirectory() as temp:
            stage=Path(temp);self.seed(stage)
            with self.assertRaisesRegex(ValueError,'qjpeg'):self.pack.check_jpeg_runtime(stage)
            result=self.pack.install_jpeg_plugin(stage,self.wheel)
            self.assertIn('Qt6Gui.dll',result['dependencies_verified'])
            self.assertTrue((stage/result['plugin']).is_file())
    def test_missing_gui_dll_is_detected_before_packaging(self):
        with tempfile.TemporaryDirectory() as temp:
            stage=Path(temp);self.seed(stage)
            (stage/'runtime/windows/Qt6Gui.dll').unlink()
            with self.assertRaisesRegex(ValueError,'Qt6Gui'):self.pack.install_jpeg_plugin(stage,self.wheel)
    def test_unverified_wheel_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            stage=Path(temp);fake=stage/'fake.whl';fake.write_bytes(b'wrong wheel')
            with self.assertRaisesRegex(ValueError,'referência'):self.pack.install_jpeg_plugin(stage,fake)
    def test_plugin_deletion_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            stage=Path(temp);self.seed(stage);result=self.pack.install_jpeg_plugin(stage,self.wheel)
            (stage/result['plugin']).unlink()
            with self.assertRaisesRegex(ValueError,'qjpeg'):self.pack.check_jpeg_runtime(stage)


if __name__=='__main__':unittest.main()
