"""Offline regression tests. Subprocesses are mocked: not a Kaggle/pip install proof."""
import ast
import contextlib
import hashlib
import importlib.metadata as md
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import rebuild_dependency_minfix as builder

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / 'prepare_bundle.py'
if not SCRIPT.exists():
    SCRIPT = HERE.parent / 'prepare_bundle.py'


class FixTests(unittest.TestCase):
    def execute_mocked(self, preflight_failure=False, invalid_source=False):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'bundle'; root.mkdir()
            support = Path(td) / 'support'; (support/'wheels').mkdir(parents=True)
            for name in ['imagecodecs-2026.6.26-py3-none-any.whl', 'zarr-3.2.1-py3-none-any.whl']:
                (support/'wheels'/name).write_bytes(b'FIXTURE_ONLY_NOT_A_REAL_WHEEL')
            (root/'dependency_specs.json').write_text('["zarr", "imagecodecs"]')
            commands = []
            def mock_run(args, **kwargs):
                commands.append(args)
                if 'download' in args:
                    destination = Path(args[args.index('-d')+1])
                    for name in ['imagecodecs-2026.3.6-py3-none-any.whl', 'openvino-2026.4.0-py3-none-any.whl', 'openvino_telemetry-2025.2.0-py3-none-any.whl']:
                        (destination/name).write_bytes(b'FIXTURE_ONLY_NOT_A_REAL_WHEEL')
                if '--dry-run' in args and preflight_failure:
                    raise subprocess.CalledProcessError(1, args, stderr='fixture resolver error')
                if '--report' in args:
                    wheel = root/'wheels'/'imagecodecs-2026.3.6-py3-none-any.whl'
                    foreign = Path(td)/'foreign.whl'; foreign.write_bytes(b'fixture')
                    rows = [{'metadata': {'name': 'imagecodecs', 'version': '2026.3.6'}, 'download_info': {'url': (foreign if invalid_source else wheel).as_uri()}},
                            {'metadata': {'name': 'zarr', 'version': '3.2.1'}, 'download_info': {'url': (support/'wheels'/'zarr-3.2.1-py3-none-any.whl').as_uri()}}]
                    Path(args[args.index('--report')+1]).write_text(json.dumps({'install':rows}))
                output = json.dumps({'numpy':'2.0.2','imagecodecs':'2026.3.6'}) if '-c' in args and args[1:2] == ['-c'] else ''
                return subprocess.CompletedProcess(args,0,output,'')
            tree = ast.parse(SCRIPT.read_text())
            replacements = {'/kaggle/working/cpu_bundle':str(root), '/kaggle/input/datasets/pilkwang/biohub-tracking-support-pack-50ep-v1':str(support)}
            class Paths(ast.NodeTransformer):
                def visit_Constant(self,node):
                    if isinstance(node.value,str) and node.value in replacements:
                        return ast.copy_location(ast.Constant(replacements[node.value]), node)
                    return node
            tree=ast.fix_missing_locations(Paths().visit(tree))
            error=None
            with patch.dict(os.environ, {'CPU_PREP_DEADLINE_EPOCH':str(time.time()+1800),'CPU_BATCH_TASK_ID':'LOCAL_MOCK_TEST'}), patch.object(subprocess,'run',side_effect=mock_run), patch.object(md,'distributions',return_value=[]), patch.object(md,'version',side_effect=lambda name: {'numpy':'2.0.2','torch':'2.10.0+cpu'}[name]), contextlib.redirect_stdout(io.StringIO()):
                try: exec(compile(tree,str(SCRIPT),'exec'),{'__name__':'mocked_prepare'})
                except BaseException as e: error=e
            files={p.relative_to(root).as_posix():p.read_text() for p in root.rglob('*') if p.is_file() and p.suffix in {'.json','.txt','.lock'}}
            return commands,files,error

    def test_constraints_override_codec_only(self):
        _,f,e=self.execute_mocked(); self.assertIsNone(e)
        pins=f['support_constraints.txt'].splitlines()
        for pin in ['numpy==2.0.2','torch==2.10.0+cpu','imagecodecs==2026.3.6','zarr==3.2.1']: self.assertIn(pin,pins)
        self.assertNotIn('imagecodecs==2026.6.26',pins)

    def test_supplement_download_precedes_combined_resolution(self):
        c,_,e=self.execute_mocked(); self.assertIsNone(e)
        download=next(i for i,x in enumerate(c) if 'download' in x)
        dry=next(i for i,x in enumerate(c) if '--dry-run' in x)
        install=next(i for i,x in enumerate(c) if 'install' in x and '--dry-run' not in x)
        self.assertLess(download,dry); self.assertLess(dry,install)
        for p in ['imagecodecs==2026.3.6','openvino==2026.4.0','openvino-telemetry==2025.2.0']: self.assertIn(p,c[dry])
        self.assertEqual(c[dry].count('--find-links'),2)
        self.assertTrue(all('--no-deps' not in x for x in c if 'install' in x))

    def test_preflight_failure_stops_before_install_or_conversion(self):
        c,f,e=self.execute_mocked(preflight_failure=True)
        self.assertIsInstance(e,subprocess.CalledProcessError)
        self.assertFalse(any('install' in x and '--dry-run' not in x for x in c))
        self.assertFalse(any(any(a.endswith('convert_bundle.py') for a in x) for x in c))
        self.assertIn('preparation_error.json',f)

    def test_staged_codec_no_self_copy_and_is_locked(self):
        _,f,e=self.execute_mocked(); self.assertIsNone(e)
        self.assertIn('imagecodecs==2026.3.6',f['requirements.lock'].splitlines())
        self.assertEqual(f['requirements.lock'].splitlines().count('imagecodecs==2026.3.6'),1)

    def test_foreign_artifact_path_rejected(self):
        _,_,e=self.execute_mocked(invalid_source=True); self.assertIsInstance(e,AssertionError)

    def test_notebook_rebuilder_preserves_other_payload_and_cells(self):
        old='print("original fixture")\n'
        payload={'prepare_bundle.py':old,'other.py':'x=2\n'}
        hashes={k:hashlib.sha256(v.encode()).hexdigest() for k,v in payload.items()}
        nb={'cells':[{'cell_type':'code','source':[f'PAYLOAD={payload!r}\n',f'HASHES={hashes!r}\n',"SOURCE_DIGEST='old'\n"], 'outputs':[],'execution_count':None}, {'cell_type':'code','source':['print("unchanged")\n'],'outputs':[],'execution_count':None}]}
        replacement=SCRIPT.read_text()
        with patch.object(builder,'OLD_SCRIPT_SHA256',hashes['prepare_bundle.py']):
            fixed,receipt=builder.rebuild(nb,replacement)
            again,_=builder.rebuild(fixed,replacement)
        self.assertEqual(fixed,again); self.assertTrue(receipt['other_payload_files_unchanged'])
        self.assertEqual(fixed['cells'][1],nb['cells'][1])
        namespace={}; exec(''.join(fixed['cells'][0]['source']),namespace)
        self.assertEqual(namespace['PAYLOAD']['prepare_bundle.py'],replacement)
        self.assertEqual(namespace['PAYLOAD']['other.py'],payload['other.py'])

    def test_notebook_rebuilder_rejects_unreviewed_drift(self):
        payload={'prepare_bundle.py':'pass\n'}
        hashes={k:hashlib.sha256(v.encode()).hexdigest() for k,v in payload.items()}
        nb={'cells':[{'cell_type':'code','source':[f'PAYLOAD={payload!r}\n',f'HASHES={hashes!r}\n',"SOURCE_DIGEST='old'\n"]}]}
        with self.assertRaisesRegex(ValueError,'drift'): builder.rebuild(nb,SCRIPT.read_text())

if __name__=='__main__': unittest.main(verbosity=2)
