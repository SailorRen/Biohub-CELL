"""Parse all public notebook code cells without executing any source."""
import ast,json,hashlib,difflib
from pathlib import Path
P=Path(__file__).resolve().parent
BASE=P.parent/'PUBLIC_0950_20260924/sources/x138/biohub-x138.ipynb'
def cells(f):return [''.join(c['source']) for c in json.loads(f.read_text())['cells'] if c['cell_type']=='code']
bc=cells(BASE)
out=[]
for f in sorted((P/'sources').glob('*/*/source.ipynb')):
 cs=cells(f);rows=[]
 for i,s in enumerate(cs):
  py='\n'.join('# '+l if l.lstrip().startswith(('!','%')) else l for l in s.splitlines())
  t=ast.parse(py)
  rows.append({'code_cell':i+1,'bytes':len(s.encode()),'sha256':hashlib.sha256(s.encode()).hexdigest(),'ast_parse':True,'shell_or_magic_lines':[l for l in s.splitlines() if l.lstrip().startswith(('!','%'))],'definitions':[n.name for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]})
 d='\n'.join(difflib.unified_diff('\n'.join(bc).splitlines(),'\n'.join(cs).splitlines(),fromfile='x138',tofile=str(f.parent)))
 (f.parent/'vs_x138.diff').write_text(d+'\n')
 out.append({'ref':'/'.join(f.parts[-3:-1]),'notebook_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'code_cells':len(cs),'effective_code_cells':sum(bool(s.strip()) for s in cs),'cells':rows,'status':'FULL_NOTEBOOK_SOURCE_STATIC_CHECKED','limitation':'All cells parsed; selected algorithm differences inspected. No downloaded code execution or dynamic patch validation.'})
(P/'source_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for r in out:print(r['ref'],r['effective_code_cells'],'all cells AST parsed')
