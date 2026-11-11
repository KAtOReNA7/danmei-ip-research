import hashlib,json,sys,tempfile,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from build_recovery_supplement import build

class Recovery(unittest.TestCase):
    def test_supplement_requires_exact_verified_base(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            def pack(name,raw,expected=None):
                p=root/name
                with zipfile.ZipFile(p,'w') as z:
                    z.writestr('fact.txt',raw)
                    z.writestr('manifest.json',json.dumps({'fact.txt':expected or hashlib.sha256(raw).hexdigest()}))
                return p
            base=pack('base.zip',b'old');current=pack('current.zip',b'new')
            out=build(base,current,'private-base',root/'built')
            wrong=pack('wrong.zip',b'other')
            with self.assertRaisesRegex(AssertionError,'different base'):
                build(wrong,out['supplement'],'private-base',root/'wrong-result')
            corrupt=pack('corrupt.zip',b'broken','0'*64)
            with self.assertRaises(AssertionError):build(corrupt,current,'private-base',root/'corrupt-result')
            restored=build(base,out['supplement'],'private-base',root/'restore')
            with zipfile.ZipFile(restored['combined_archive']) as z:self.assertEqual(z.read('fact.txt'),b'new')
