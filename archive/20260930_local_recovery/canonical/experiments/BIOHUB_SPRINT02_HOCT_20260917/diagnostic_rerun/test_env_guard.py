import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from env_guard import check_environment
class GuardTests(unittest.TestCase):
    def test_real_match(self):
        with tempfile.TemporaryDirectory() as d:
            r=check_environment(Path(d)/'r.json');self.assertEqual(r['status'],'ENVIRONMENT_VERIFIED')
    def test_version_stops(self):
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.json'
            with self.assertRaisesRegex(RuntimeError,'BLOCKED_ENVIRONMENT_MISMATCH'):
                check_environment(p,version_reader=lambda _:'incorrect');calls.append('inference')
            self.assertEqual(calls,[]);self.assertEqual(json.loads(p.read_text())['observed_version'],'incorrect')
    def test_source_stops(self):
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.json';bad=Path(d)/'bad.py';bad.write_text('# wrong source')
            with self.assertRaisesRegex(RuntimeError,'BLOCKED_ENVIRONMENT_MISMATCH'):
                check_environment(p,module_loader=lambda _:SimpleNamespace(__file__=str(bad)));calls.append('inference')
            self.assertEqual(calls,[]);self.assertEqual(len(json.loads(p.read_text())['errors']),3)
if __name__=='__main__':unittest.main(verbosity=2)
