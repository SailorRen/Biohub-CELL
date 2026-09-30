"""冻结 tracksdata 实际安装文件检查；不安装依赖，不执行模型。"""
import hashlib
import importlib
import importlib.metadata
import json
import sys
from pathlib import Path

EXPECTED_VERSION = '0.1.0rc6.dev3+g980c2d30a'
EXPECTED_FILES = {
    'tracksdata.graph._rustworkx_graph': '548db539dcf066f4a1bc331ba4bbb547d0b556d763fa9746185b19be514d1d11',
    'tracksdata.graph._base_graph': 'fd3835a3a37b0817896e063ac10f809683b632ed7582c16547d40d304df19462',
    'tracksdata.nodes._mask': '43297f42c31a9035e242825aab51faf1ba219b25dbadf081e6de7d113818c422',
}


def check_environment(receipt_path, version_reader=importlib.metadata.version, module_loader=importlib.import_module):
    receipt = dict(status='BLOCKED_ENVIRONMENT_MISMATCH', expected_version=EXPECTED_VERSION,
                   observed_version=None, files={}, errors=[], executable=sys.executable, prefix=sys.prefix,
                   worker_environment='same sys.executable, inherited environment, no dependency mutation after guard')
    try:
        receipt['observed_version'] = version_reader('tracksdata')
        if receipt['observed_version'] != EXPECTED_VERSION:
            receipt['errors'].append('TRACKSDATA_VERSION_MISMATCH')
    except Exception as exc:
        receipt['errors'].append('TRACKSDATA_VERSION_UNREADABLE:' + repr(exc))
    for name, expected in EXPECTED_FILES.items():
        item = dict(expected_sha256=expected, observed_sha256=None, path=None)
        try:
            module = module_loader(name)
            path = Path(module.__file__).resolve()
            item['path'] = str(path)
            item['observed_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            if item['observed_sha256'] != expected:
                receipt['errors'].append(name + ':SOURCE_MISMATCH')
        except Exception as exc:
            receipt['errors'].append(name + ':SOURCE_UNREADABLE:' + repr(exc))
        receipt['files'][name] = item
    if not receipt['errors']:
        receipt['status'] = 'ENVIRONMENT_VERIFIED'
    Path(receipt_path).write_text(json.dumps(receipt, indent=2) + '\n')
    print('S02_ENVIRONMENT_GUARD', json.dumps(receipt), flush=True)
    if receipt['errors']:
        raise RuntimeError('BLOCKED_ENVIRONMENT_MISMATCH: ' + '; '.join(receipt['errors']))
    return receipt
