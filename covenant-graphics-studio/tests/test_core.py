import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from covenant_studio import model
from covenant_studio.firmware import load_firmware, inspect_bytes, section_leaves, SETUP

ROOT=Path(__file__).resolve().parents[1]


def question(qid='stock-csm',offset=0x74,size=125,prompt='CSM Support',**changes):
    q={'id':qid,'module':'setup-module','form':'stock-form','formset':'formset','form_title':'Boot',
       'kind':'oneof','prompt':prompt,'help':'','width':1,'offset':offset,'store_id':1,
       'store':{'guid':'VARIABLE-GUID','name':'Setup','size':size},'storage_valid':True,
       'conditional':False,'callback':False,'read_only':False,
       'options':[{'label':'Disabled','value':'0'},{'label':'Enabled','value':'1'}],
       'minimum':'0','maximum':'1','step':'0','signed':False}
    q.update(changes);return q


def fixture():
    sq=question();dq=question('donor-csm',0x46d,1249,form='donor-form')
    sf={'id':'stock-form','form_id':1,'formset':'formset','title':'Boot','module':'setup-module'}
    df={**sf,'id':'donor-form'}
    stock={'sha256':'a'*64,'bios_id':'X99D8 Ver:002','forms':[sf],'questions':[sq]}
    donor={'forms':[df],'questions':[dq]}
    cat={'background':'bg.png','brand':'bg.png','images':[{'id':'bg.png','width':1,'height':1}]}
    return stock,donor,cat


class MatchingTests(unittest.TestCase):
    def test_translates_donor_csm_offset_to_actual_stock_slot(self):
        s,d,c=fixture();r=model.auto_match(d['questions'][0],s)
        self.assertEqual(r['target_id'],'stock-csm');self.assertEqual(r['status'],'linked')
        self.assertEqual(s['questions'][0]['offset'],0x74)
    def test_different_variable_is_not_matched_by_label(self):
        s,d,c=fixture();d['questions'][0]['store']['name']='IntelSetup'
        self.assertEqual(model.auto_match(d['questions'][0],s)['status'],'unmatched')
    def test_different_guid_is_not_matched(self):
        s,d,c=fixture();d['questions'][0]['store']['guid']='ANOTHER'
        self.assertIsNone(model.auto_match(d['questions'][0],s)['target_id'])
    def test_ambiguous_storage_locations_are_not_guessed(self):
        s,d,c=fixture();s['questions'].append(question('another',offset=0x23))
        self.assertEqual(model.auto_match(d['questions'][0],s)['status'],'unmatched')
    def test_callbacks_remain_review_items(self):
        s,d,c=fixture();s['questions'][0]['callback']=True
        self.assertEqual(model.auto_match(d['questions'][0],s)['status'],'review')
    def test_hidden_conditions_remain_review_items(self):
        s,d,c=fixture();d['questions'][0]['conditional']=True
        self.assertEqual(model.auto_match(d['questions'][0],s)['status'],'review')
    def test_option_labels_translate_values(self):
        s,d,c=fixture();s['questions'][0]['options']=[{'label':'Disabled','value':'4'},{'label':'Enabled','value':'7'}]
        self.assertEqual(model.auto_match(d['questions'][0],s)['value_map'],{'0':'4','1':'7'})
    def test_incompatible_option_does_not_link(self):
        s,d,c=fixture();d['questions'][0]['options'].append({'label':'Special mode','value':'2'})
        self.assertEqual(model.auto_match(d['questions'][0],s)['status'],'unmatched')
    def test_numeric_range_cannot_be_silently_truncated(self):
        s=question(kind='numeric',options=[],maximum='10');d=question('d',kind='numeric',options=[],maximum='100')
        mapping,error=model.value_map(d,s);self.assertIsNone(mapping)
    def test_opposite_option_meanings_are_not_linked_by_number(self):
        s,d,c=fixture();s['questions'][0]['options']=[{'label':'Enabled','value':'0'},{'label':'Disabled','value':'1'}]
        self.assertEqual(model.auto_match(d['questions'][0],s)['value_map'],{'0':'1','1':'0'})


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.stock,self.donor,self.cat=fixture();self.project=model.make_project(self.stock,self.donor,self.cat,'catalog')
    def validate(self):return model.validate_project(self.project,self.stock,self.donor,self.cat,'catalog')
    def test_default_stock_control_points_to_its_own_field(self):
        controls=[c for c in self.project['controls'] if c['source_origin']=='stock' and c['source_id']=='stock-csm']
        self.assertTrue(controls);self.assertTrue(all(c['target_id']=='stock-csm' for c in controls));self.validate()
    def test_project_from_other_firmware_is_rejected(self):
        self.project['stock_sha256']='b'*64
        with self.assertRaises(ValueError):self.validate()
    def test_runtime_compiler_flag_cannot_be_forged(self):
        self.project['firmware_compiler_implemented']=True
        with self.assertRaises(ValueError):self.validate()
    def test_unknown_page_form_is_rejected(self):
        self.project['pages'][0]['form']='not-a-form'
        with self.assertRaises(ValueError):self.validate()
    def test_unknown_target_rejected(self):
        self.project['controls'][0]['target_id']='foreign-field'
        with self.assertRaises(ValueError):self.validate()
    def test_nonfinite_geometry_rejected(self):
        self.project['controls'][0]['rect'][0]=float('nan')
        with self.assertRaises(ValueError):self.validate()
    def test_out_of_scene_geometry_rejected(self):
        self.project['controls'][0]['rect']=[.9,.1,.5,.1]
        with self.assertRaises(ValueError):self.validate()
    def test_shortcut_collision_in_one_page_rejected(self):
        c=copy.deepcopy(self.project['controls'][0]);c['id']='another';c['shortcut']='F5';self.project['controls'][0]['shortcut']='F5';self.project['controls'].append(c)
        with self.assertRaises(ValueError):self.validate()
    def test_test_values_enforce_actual_target_options(self):
        with self.assertRaises(ValueError):model.set_test_value(self.project,self.stock['questions'][0],'999')
        model.set_test_value(self.project,self.stock['questions'][0],'1');self.validate()
        self.assertEqual(self.project['test_values'][model.slot(self.stock['questions'][0])],'1')
    def test_readonly_value_cannot_be_test_written(self):
        self.stock['questions'][0]['read_only']=True
        with self.assertRaises(ValueError):model.set_test_value(self.project,self.stock['questions'][0],'1')
    def test_invalid_asset_path_is_rejected(self):
        self.project['controls'][0]['asset']='../../other.png'
        with self.assertRaises(ValueError):self.validate()
    def test_roundtrip_and_export_do_not_include_rom(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'p.json';z=Path(temp)/'links.zip'
            model.write_project(p,self.project,self.stock,self.donor,self.cat,'catalog')
            self.assertEqual(model.read_project(p,self.stock,self.donor,self.cat,'catalog'),self.project)
            manifest=model.export_package(z,self.project,self.stock,self.donor,self.cat,'catalog')
            self.assertFalse(manifest['flashable_rom_included'])
            with zipfile.ZipFile(z) as archive:
                self.assertIsNone(archive.testzip());self.assertFalse(any(n.endswith(('.rom','.efi','.bin')) for n in archive.namelist()))
    def test_csv_formula_in_label_is_escaped(self):
        self.project['controls'][0]['label']='=1+1'
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'export.zip';model.export_package(p,self.project,self.stock,self.donor,self.cat,'catalog')
            with zipfile.ZipFile(p) as archive:self.assertIn("'=1+1",archive.read('vinculos.csv').decode())
    def test_saving_or_exporting_cannot_overwrite_input(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'original.json';p.write_bytes(b'original BIOS bytes')
            self.stock['_input_path']=str(p.resolve())
            with self.assertRaises(ValueError):model.write_project(p,self.project,self.stock,self.donor,self.cat,'catalog')
            with self.assertRaises(ValueError):model.export_package(p,self.project,self.stock,self.donor,self.cat,'catalog')
            self.assertEqual(p.read_bytes(),b'original BIOS bytes')
    def test_wrong_output_extension_cannot_disguise_project_as_rom(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'wrong.rom'
            with self.assertRaises(ValueError):model.write_project(p,self.project,self.stock,self.donor,self.cat,'catalog')
            self.assertFalse(p.exists())
    def test_bad_base64_image_rejected(self):
        self.project['asset_overrides']['bg.png']='not base64!'
        with self.assertRaises(ValueError):self.validate()
    def test_truncated_compression_is_rejected(self):
        with self.assertRaises((ValueError,Exception)):section_leaves(b'\x20\0\0\x02bad')
    def test_wrong_input_size_is_rejected(self):
        with self.assertRaises(ValueError):inspect_bytes(b'not a BIOS')


@unittest.skipUnless(os.environ.get('COVENANT_BIOS_FIXTURE'),'Private BIOS fixture not configured')
class ActualFirmwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=Path(os.environ['COVENANT_BIOS_FIXTURE']);cls.data=cls.path.read_bytes();cls.stock=load_firmware(cls.path)
    def test_real_hii_includes_csm_in_correct_varstore(self):
        qs=[q for q in self.stock['questions'] if q['prompt']=='CSM Support' and q.get('store') and q['store']['name']=='Setup']
        self.assertEqual(len(qs),1);self.assertEqual(qs[0]['offset'],0x74);self.assertEqual(qs[0]['store']['size'],125)
        self.assertEqual(len(self.stock['questions']),5377)
    def test_8_and_16_mib_have_identical_hii(self):
        other=inspect_bytes(self.data[0x800000:] if len(self.data)==0x1000000 else self.data)
        self.assertEqual(other['questions'],self.stock['questions']);self.assertEqual(other['forms'],self.stock['forms'])
    def test_corrupt_ffs_header_is_rejected(self):
        import uuid
        bad=bytearray(self.data);offset=bad.find(uuid.UUID(SETUP).bytes_le);self.assertGreater(offset,0)
        bad[offset+16]^=1
        with self.assertRaises(ValueError):inspect_bytes(bytes(bad))
    def test_real_inputs_unchanged_after_analysis(self):
        from covenant_studio.firmware import sha
        self.assertEqual(sha(self.path.read_bytes()),self.stock['sha256'])


if __name__=='__main__':unittest.main()
