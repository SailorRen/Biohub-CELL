"""Rebuild the embedded preparation script locally; never launch Kaggle.

Run from any directory after fetching the repaired research branch. The old
notebook is retained as evidence; a new .ipynb and matching metadata are written
into prepare_batch/dependency_minfix/. Existing unequal outputs are not replaced.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path

OLD_SCRIPT_SHA256 = '3819b84aa9ecb4335a5cf84c0be315ec1ee95a029fdab8b42e775f0b3abd9785'


def rebuild(notebook: dict, replacement: str) -> tuple[dict, dict]:
    result = copy.deepcopy(notebook)
    cell = result['cells'][0]
    source = ''.join(cell['source'])
    assignments = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {'PAYLOAD', 'HASHES', 'SOURCE_DIGEST'}:
                assignments[target.id] = node
    if set(assignments) != {'PAYLOAD', 'HASHES', 'SOURCE_DIGEST'}:
        raise ValueError('Unexpected preparation notebook layout; do not guess a patch')
    payload = ast.literal_eval(assignments['PAYLOAD'].value)
    hashes = ast.literal_eval(assignments['HASHES'].value)
    actual = {k: hashlib.sha256(v.encode('utf-8')).hexdigest() for k, v in payload.items()}
    if actual != hashes:
        raise ValueError('Original embedded payload hashes do not match')
    new_hash = hashlib.sha256(replacement.encode('utf-8')).hexdigest()
    if actual['prepare_bundle.py'] not in {OLD_SCRIPT_SHA256, new_hash}:
        raise ValueError('Unreviewed preparation-script drift; refusing overwrite')
    compile(replacement, 'prepare_bundle.py', 'exec')
    payload['prepare_bundle.py'] = replacement
    hashes['prepare_bundle.py'] = new_hash
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode('utf-8')).hexdigest()
    lines = source.splitlines(keepends=True)
    values = {'PAYLOAD': payload, 'HASHES': hashes, 'SOURCE_DIGEST': digest}
    for name, node in sorted(assignments.items(), key=lambda pair: pair[1].lineno, reverse=True):
        lines[node.lineno - 1:node.end_lineno] = [name + '=' + repr(values[name]) + '\n']
    cell['source'] = ''.join(lines).splitlines(keepends=True)
    for item in result['cells']:
        if item['cell_type'] == 'code':
            item['execution_count'] = None
            item['outputs'] = []
            compile(''.join(item['source']), '<rebuilt notebook>', 'exec')
    return result, {'old_prepare_sha256': actual['prepare_bundle.py'],
                    'new_prepare_sha256': new_hash,
                    'payload_files': len(payload),
                    'other_payload_files_unchanged': all(hashes[k] == actual[k] for k in hashes if k != 'prepare_bundle.py'),
                    'source_digest': digest, 'platform_writes': 0}


def write_once(path: Path, content: str) -> None:
    if path.exists():
        if path.read_text(encoding='utf-8') != content:
            raise FileExistsError(f'Refusing to overwrite different generated file: {path}')
        return
    path.write_text(content, encoding='utf-8')


def main() -> None:
    here = Path(__file__).resolve().parent
    parent = here.parent
    original = json.loads((here / 'preparation_batch.ipynb').read_text(encoding='utf-8'))
    fixed, receipt = rebuild(original, (parent / 'prepare_bundle.py').read_text(encoding='utf-8'))
    destination = here / 'dependency_minfix'
    destination.mkdir(exist_ok=True)
    write_once(destination / 'preparation_batch.ipynb', json.dumps(fixed, ensure_ascii=False, indent=1) + '\n')
    metadata = json.loads((here / 'kernel-metadata.json').read_text(encoding='utf-8'))
    metadata['code_file'] = 'preparation_batch.ipynb'
    if metadata.get('enable_gpu') or metadata.get('enable_tpu') or not metadata.get('is_private'):
        raise ValueError('Unexpected accelerator or visibility; do not launch')
    write_once(destination / 'kernel-metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    receipt['notebook_sha256'] = hashlib.sha256((destination / 'preparation_batch.ipynb').read_bytes()).hexdigest()
    write_once(destination / 'rebuild_receipt.json', json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'output': str(destination), **receipt}, indent=2))


if __name__ == '__main__':
    main()
