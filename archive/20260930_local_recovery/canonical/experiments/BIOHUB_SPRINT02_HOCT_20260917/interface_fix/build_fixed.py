"""从不可变V1归档替换修复模块；只写本地NOT_RUN文件，绝不导入旧构建器。"""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    original=B/'diagnostic/candidate.ipynb'
    assert sha(original)=='62464d4fd8b372e39cec76de6f798588b6b017b76fb8a371e0210bd8c4a86ae9'
    nb=json.loads(original.read_text());tree=ast.parse(''.join(nb['cells'][5]['source']));changed=[]
    for n in tree.body:
        if not isinstance(n,ast.Expr) or not isinstance(n.value,ast.Call):continue
        c=n.value
        if not isinstance(c.func,ast.Attribute) or c.func.attr!='write_text':continue
        name=Path(ast.literal_eval(c.func.value.args[0])).name
        if name in ['hoct_observer.py','hoct_worker.py']:
            c.args[0]=ast.Constant((B/name).read_text());changed.append(name)
    assert set(changed)=={'hoct_observer.py','hoct_worker.py'}
    nb['cells'][5]['source']=ast.unparse(tree)+'\n'
    nb['cells'][7]['source']=(B/'diagnostic_runtime.py').read_text()
    for c in nb['cells']:
        ast.parse(''.join(c['source']));c['outputs']=[];c['execution_count']=None
    out=P/'diagnostic_fixed.ipynb';out.write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
    receipt=dict(status='BUILT_LOCAL',cloud_status='NOT_RUN',version=None,script_version_id=None,source_sha256=sha(out),
       original_sha256=sha(original),changed_cells=[5,7],embedded_files=changed,
       module_sha256={n:sha(B/n) for n in ['hoct_observer.py','hoct_worker.py','diagnostic_runtime.py']},outputs_empty=True,kaggle_requests=0)
    (P/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':build()
