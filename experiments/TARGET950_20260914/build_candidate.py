"""Build one offline official-score selector from the exact 0.947 notebook."""
import ast
import copy
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
BASE_SHA = 'bb6dbf2766fff1b4f7d1c96f3c1145c700d4d44e4695d924c7be8ccbe1b07af7'
REF = 'sailorren/biohub-947-official-selector-20260914'
OFFICIAL_COMMIT = '075fc5f5a52d11077f9dc2b074644618f26939e2'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make_notebook():
    raw = (P / 'baseline/candidate.ipynb').read_bytes()
    assert sha(raw) == BASE_SHA
    baseline = json.loads(raw)
    candidate = copy.deepcopy(baseline)
    assert len(candidate['cells']) == 12
    files = {'__init__.py': ''}
    receipt = json.loads((P / 'official_source_receipt.json').read_text())
    assert receipt['commit'] == OFFICIAL_COMMIT
    for row in receipt['files']:
        data = (P / 'vendor/official_075fc5' / row['file']).read_bytes()
        assert sha(data) == row['sha256']
        files[row['file']] = data.decode('utf-8')
    hashes = {name: sha(text.encode()) for name, text in files.items()}
    installer = '''
# TARGET950: evaluate the same held-out graphs with the fixed public scorer.
# This changes automatic PP selection only. It does not claim the private
# Kaggle deployment is byte-identical or that a higher local score is a gain.
import hashlib as _official_hashlib
import importlib.util as _official_importlib
import sys as _official_sys
_official_files = FILE_PAYLOAD
_official_file_hashes = HASH_PAYLOAD
_official_package_dir = WORKING_DIR / "official_scorer_075fc5"
_official_package_dir.mkdir(parents=True, exist_ok=True)
for _name, _contents in _official_files.items():
    _data = _contents.encode("utf-8")
    if _official_hashlib.sha256(_data).hexdigest() != _official_file_hashes[_name]:
        raise RuntimeError("OFFICIAL_SCORER_PAYLOAD_HASH_MISMATCH: " + _name)
    _target = _official_package_dir / _name
    _target.write_bytes(_data)
    if _official_hashlib.sha256(_target.read_bytes()).hexdigest() != _official_file_hashes[_name]:
        raise RuntimeError("OFFICIAL_SCORER_DISK_HASH_MISMATCH: " + _name)
_official_package_name = "biohub_official_075fc5"
_official_spec = _official_importlib.spec_from_file_location(
    _official_package_name, _official_package_dir / "__init__.py",
    submodule_search_locations=[str(_official_package_dir)],
)
_official_package = _official_importlib.module_from_spec(_official_spec)
_official_sys.modules[_official_package_name] = _official_package
_official_spec.loader.exec_module(_official_package)
_official_metrics_spec = _official_importlib.spec_from_file_location(
    _official_package_name + ".metrics", _official_package_dir / "metrics.py"
)
OFFICIAL_METRICS = _official_importlib.module_from_spec(_official_metrics_spec)
_official_sys.modules[_official_package_name + ".metrics"] = OFFICIAL_METRICS
_official_metrics_spec.loader.exec_module(OFFICIAL_METRICS)
'''
    installer = installer.replace('FILE_PAYLOAD', repr(files)).replace('HASH_PAYLOAD', repr(hashes))
    adapter = (P / 'official_selector_adapter.py').read_text()
    assert not any(isinstance(x, ast.ImportFrom) and x.module == '__future__' for x in ast.parse(adapter).body)
    source = ''.join(baseline['cells'][8]['source'])
    source += installer + '\n' + adapter + '\ninstall_official_selector(globals())\n'
    source += '\nprint("TARGET950: selector uses fixed official score; legacy proxy fields are diagnostic only.")\n'
    candidate['cells'][8]['source'] = source.splitlines(keepends=True)
    # Keep every original cell byte-for-byte except the scorer cell. The final
    # extra cell only serializes existing scalar metrics and resolved settings.
    audit = (P / 'runtime_audit.py').read_text()
    candidate['cells'].append({'cell_type': 'code', 'execution_count': None,
                               'metadata': {}, 'outputs': [],
                               'source': audit.splitlines(keepends=True)})
    for cell in candidate['cells']:
        ast.parse(''.join(cell['source']))
    for i in range(12):
        if i != 8:
            assert candidate['cells'][i] == baseline['cells'][i]
    assert ''.join(candidate['cells'][10]['source']) == ''.join(baseline['cells'][10]['source'])
    return candidate


def make_metadata():
    metadata = json.loads((P / 'baseline/kernel-metadata.json').read_text())
    metadata.pop('id_no', None)
    metadata.update(id=REF, title='Biohub 0.947 Official Selector 20260914', code_file='candidate.ipynb')
    inputs = json.loads((P / 'fixed_inputs_browser_receipt.json').read_text())['input_dataset_versions']
    assert metadata['dataset_sources'] == [x['ref'] for x in inputs]
    metadata['dataset_sources'] = [x['ref'] + '/' + str(x['version']) for x in inputs]
    return metadata


def main():
    for name, value in [('candidate.ipynb', make_notebook()), ('kernel-metadata.json', make_metadata())]:
        (P / name).write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'candidate': REF, 'source_sha256': sha((P / 'candidate.ipynb').read_bytes()),
                      'status': 'BUILT_NOT_RUN', 'modified_original_cells': [8],
                      'additional_observation_cells': 1}))


if __name__ == '__main__':
    main()
