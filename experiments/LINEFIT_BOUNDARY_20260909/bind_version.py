"""Bind a root-observed fixed-Version UI receipt to a fresh official source read."""
import argparse
import json
from pathlib import Path
import kaggle_io as io

parser = argparse.ArgumentParser()
parser.add_argument('--ui-receipt', required=True)
args = parser.parse_args()
ui_path = (io.ROOT / args.ui_receipt).resolve()
io.require(ui_path.is_relative_to(io.P), 'Receipt must be task-local')
ui = json.loads(ui_path.read_text())
s = io.state(); m = io.local_gate(io.sha((io.P / 'manifest.json').read_bytes()))
meta = json.loads((io.P / 'kernel-metadata.json').read_text())
io.require(ui['ref'] == io.REF and ui['version'] == s['version'] == 1, 'UI Version/ref mismatch')
sv = ui['script_version_id']
io.require(type(sv) is int and sv > 0 and f'scriptVersionId={sv}' in ui['version_url'] and io.REF in ui['version_url'], 'No fixed ScriptVersionId URL')
io.require(ui['dataset_sources'] == meta['dataset_sources'], 'Fixed-Version input sources not verified')
io.require(ui['source'] == 'CUA_FIXED_VERSION_AND_INPUTS_UI' and ui['observed_at_utc'], 'Missing direct UI provenance')

@io.readonly_tls_retry
def fetch():
    from kaggle import api
    return io.kernel(api, io.REF)

k, source = fetch()
io.require(k['kernel_id'] == s['kernel_id'] and k['version'] == 1 and k['cell_sha256'] == m['cell_sha256'], 'Platform source/Version changed')
io.require(k['is_private'] and k['enable_gpu'] and not k['enable_internet'] and k['machine_shape'] == meta['machine_shape'] and k['docker_image'] == meta['docker_image'], 'Platform runtime changed')
io.require(sorted(k['datasets']) == sorted('/'.join(v.split('/')[:2]) for v in meta['dataset_sources']), 'Platform dataset slugs changed')
s['script_version_id'] = sv
s['remote_binding'] = {'verified': True, 'observed_at_utc': io.now(), 'ref': io.REF, 'kernel_id': k['kernel_id'], 'version': 1,
                       'script_version_id': sv, 'ui_receipt': str(ui_path.relative_to(io.ROOT)), 'ui_receipt_sha256': io.sha(ui_path.read_bytes()),
                       'dataset_sources': ui['dataset_sources'], 'source_sha256': k['source_sha256'],
                       'submitted_source_sha256': m['submitted_source_sha256'], 'all_cell_sources_equal': True,
                       'serialization_note': 'Remote JSON bytes and SDK upload serialization have independent hashes; actual code cells match exactly.'}
io.persist(io.P / 'results.json', s)
print(json.dumps(s['remote_binding'], ensure_ascii=False, indent=2))
