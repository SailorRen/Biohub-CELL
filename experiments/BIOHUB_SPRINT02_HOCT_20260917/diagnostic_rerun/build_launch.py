"""仅向固定源码安装完成处添加环境检查；保持原件和其余源码逐字不变。"""
import ast,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
    source=B/'interface_fix/diagnostic_fixed.ipynb'
    assert sha(source)=='1f4cbb3c98089bfb5f3fa0901922e87edb6cb88636e12af1dec6f645a919c729'
    nb=json.loads(source.read_text());original=[''.join(c['source']) for c in nb['cells']]
    code=(P/'env_guard.py').read_text();ast.parse(code)
    block="\n# BEGIN AUTHORIZED ENVIRONMENT GUARD ADDENDUM\n"+code+"\ncheck_environment(OUT/'environment_guard.json')\n# END AUTHORIZED ENVIRONMENT GUARD ADDENDUM\n"
    anchor="assert package_before == {n:importlib.metadata.version(n) for n in package_before}\n"
    assert original[7].count(anchor)==1
    nb['cells'][7]['source']=original[7].replace(anchor,anchor+block)
    for i,c in enumerate(nb['cells']):
        s=''.join(c['source']);ast.parse(s)
        assert not c['outputs'] and c['execution_count'] is None
        assert s.replace(block,'')==original[i]
    output=P/'diagnostic_launch.ipynb';output.write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
    meta=json.loads((B/'diagnostic/kernel-metadata.json').read_text());meta['code_file']='diagnostic_launch.ipynb'
    (P/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (P/'launch.diff').write_text(''.join(difflib.unified_diff(original[7].splitlines(True),nb['cells'][7]['source'].splitlines(True),fromfile='fixed/cell7',tofile='launch/cell7')))
    result=dict(original_sha256=sha(source),launch_sha256=sha(output),guard_sha256=sha(P/'env_guard.py'),changed_cells=[7],
      cell_mapping={str(i):i for i in range(8)},all_original_source_preserved=True,outputs_empty=True,
      guard_position='after offline pip install and package_before equality; before first subprocess worker',
      worker_environment='same sys.executable; Popen inherits environment; no dependency changes after guard',
      cells=[hashlib.sha256(''.join(c['source']).encode()).hexdigest() for c in nb['cells']])
    (P/'launch_receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
