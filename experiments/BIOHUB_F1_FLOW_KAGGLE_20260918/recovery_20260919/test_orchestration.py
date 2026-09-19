import ast,copy,json,unittest
from pathlib import Path
from budget import authorize
P=Path(__file__).resolve().parent.parent
class Tests(unittest.TestCase):
 def test_budget(self):
  ledger=json.loads((P/'ledger.json').read_text());ledger['requests']=ledger['requests'][:1];ledger['engineering_reserve_used']=0;authorize(ledger,'diagnostic','unknown_outcome_recovery')
  used=copy.deepcopy(ledger);used['engineering_reserve_used']=1
  with self.assertRaises(AssertionError):authorize(used,'diagnostic','unknown_outcome_recovery')
  used['requests'].append({'phase':'diagnostic','reason':'unknown_outcome_recovery'})
  authorize(used,'production','frozen_gate_passed')
  used['requests'].append({'phase':'production'})
  with self.assertRaises(AssertionError):authorize(used,'production','frozen_gate_passed')
 def test_send_mock(self):
  from types import SimpleNamespace as S
  import hashlib
  tree=ast.parse((P/'save_once.py').read_text());fn=next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name=='send')
  response=S(status_code=200,headers={'Content-Type':'text/html'},content=b'not json')
  event={'wire_sends':0};calls=[]
  scope={'event':event,'ledger':{},'persist':lambda x:None,'now':lambda:'mock','safe':str,'hashlib':hashlib,'original_send':lambda *a,**kw:calls.append(kw) or response}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'mock','exec'),scope)
  session=S(adapters={'https':S(max_retries=S(total=0))});request=S(url='https://api.kaggle.com/kernels.KernelsApiService/SaveKernel')
  scope['send'](session,request)
  self.assertEqual(event['wire_sends'],1);self.assertEqual(event['http']['response_length'],8);self.assertFalse(calls[0]['allow_redirects'])
  with self.assertRaises(AssertionError):scope['send'](session,request)
  self.assertEqual(len(calls),1)
if __name__=='__main__':unittest.main()
