from pathlib import Path
from datetime import datetime,timezone
import ast,json,hashlib,csv
ROOT=Path.cwd(); RAW=ROOT/'downloads/20260909_public_research/notebooks';OUT=ROOT/'research/20260909_公开来源优化研究';OUT.mkdir(parents=True,exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def src(c):return c['source'] if isinstance(c['source'],str) else ''.join(c['source'])
def dump(x):return json.dumps(x,ensure_ascii=False,indent=2)+'\n'
invraw=json.loads((RAW/'inventory_raw.json').read_text());inv={}
for query in invraw:
 for row in query['items']:
  e=inv.setdefault(row['ref'],{'ref':row['ref'],'title':row['title'],'last_run_time':row.get('lastRunTime'),'total_votes':row.get('totalVotes'),'found_in':[],'evidence_scope':'DISCOVERY_ONLY_NOT_SOURCE_OR_SCORE'})
  e['found_in'].append(query['sort'])
refs=['redoctopusk/biohub-942tta','flexonafft/biohub-harmonic-fusion','flexonafft/biohub-lineage-forge-precision-tracking','zhincez/the-metric-pays-you-to-delete-nodes','rogerrogerroger3r/biohub-run84']
prior={}
for label,filename in [('tta','tta_源码审读.json'),('harmonic','harmonic_源码审读.json')]:
 prior[label]=json.loads((ROOT/'research/20260908_正式成绩与公开946对比'/filename).read_text())
notebooks=[];nbs={}
for ref in refs:
 p=RAW/ref.replace('/','__');m=json.loads((p/'metadata.json').read_text());nb=json.loads((p/'source.ipynb').read_text());nbs[ref]=nb
 rec={**m,'url':'https://www.kaggle.com/code/'+ref,'source_path':str((p/'source.ipynb').relative_to(ROOT)),'fact_class':'SOURCE_CODE_VERIFIED','script_version_id':None,'script_version_id_status':'UNKNOWN_PENDING_ROOT_UI','score':{'value':None,'status':'UNKNOWN_PENDING_ROOT_UI','formal_submission_id':None},'code_cells_total':sum(c['cell_type']=='code' for c in nb['cells']),'execution_status':'NOT_RUN','cells':[]}
 for i,c in enumerate(nb['cells']):
  s=src(c);e={'index':i,'cell_type':c['cell_type'],'line_count':len(s.splitlines()),'source_sha256':sha(s.encode())}
  if c['cell_type']=='code':
   tree=ast.parse(s);compile(tree,'source_only','exec');e.update({'parse_compile':'PASS_NOT_EXECUTED','ast_sha256':sha(ast.dump(tree).encode())})
  rec['cells'].append(e)
 if ref==refs[0]:
  assert rec['sha256']==prior['tta']['notebook_sha256']
  for e,c in zip(rec['cells'],prior['tta']['cells']):
   assert e['source_sha256']==c['sha256_utf8_source'];e.update({'coverage':'PRIOR_FULL_READ_BYTE_REVERIFIED','summary':c['summary_zh']})
  rec.update({'coverage_status':'FULL_NOTEBOOK_SOURCE_REVERIFIED','code_cells_read':12,'prior_full_read_evidence':'research/20260908_正式成绩与公开946对比/tta_源码审读.json','prior_full_read_commit':'175054cb891e2f7981d196a6c1cb6d26f8d6abcf','review_method':'本轮GetKernel下载全部源码，12/12cell逐字hash与已全读审计锚定一致并全部AST/compile检查；本轮重读配置、动态补丁、motion/safe-div、proxy和PP。复用已有全读证据，不声称本轮逐字重读4151行。'})
 elif ref==refs[1]:
  old=ROOT/'downloads/20260908_public946/harmonic/biohub-harmonic-fusion.ipynb';assert rec['sha256']==sha(old.read_bytes())
  for e,c in zip(rec['cells'],prior['harmonic']['cells']):
   assert e['source_sha256']==c['source_sha256'];e.update({'coverage':'PRIOR_FULL_READ_BYTE_REVERIFIED','summary':c['review']})
  rec.update({'coverage_status':'FULL_NOTEBOOK_SOURCE_REVERIFIED','code_cells_read':12,'prior_full_read_evidence':'research/20260908_正式成绩与公开946对比/harmonic_源码审读.json','prior_full_read_commit':'175054cb891e2f7981d196a6c1cb6d26f8d6abcf','review_method':'本轮GetKernel全部源码SHA与9/8全读锚一致，12/12cellhash及AST复核；与TTA逐cellAST对照(剥离cell0展示docstring后全等)。'})
 elif ref==refs[2]:
  base=nbs[refs[1]]
  for e,c,b in zip(rec['cells'],nb['cells'],base['cells']):
   same=src(c)==src(b);e['byte_equal_harmonic_same_cell']=same
   e['coverage']='IDENTICAL_TO_FULL_READ_HARMONIC_CELL_REVERIFIED' if same else 'ALL_DIFFERENCES_READ_AND_STATIC_PATCH_EXPANDED'
   e['summary']=prior['harmonic']['cells'][e['index']]['review'] if same else ('仅展示docstring变化' if e['index']==0 else '保留全母版动态补丁，新增次模型8pass特征TTA，0.25原始特征+0.75增强均值；全部新增old47/new99行字符串已展开审读，B0展开源码上锚点恰1且compile通过。')
  assert [e['index'] for e in rec['cells'] if not e['byte_equal_harmonic_same_cell']]==[0,4]
  rec.update({'coverage_status':'FULL_NOTEBOOK_SOURCE_DIFFERENTIAL_READ','code_cells_read':12,'review_method':'下载全部12cell；10cell逐字等于本轮重核全读Harmonic，另2cell全部差异读取。新增动态patch47→99行展开检查，唯一锚点替换B0完整展开源码并compile；未执行Notebook/模型。','script_version_id':348210665,'script_version_id_status':'ROOT_FIXED_VERSION_UI_REPORTED_PENDING_RECEIPT_LINK','score':{'value':'0.946','status':'ROOT_FIXED_VERSION_PUBLIC_SCORE_UI','version':7,'script_version_id':348210665,'formal_submission_id':None,'caveat':'公开Version分数，不冒充已取得作者submission列表回执。'},'new_model_weights':False,'training_added':False,'association_fusion_weights_changed':False,'pp_selection_changed':False,'secondary_feature_formula':'0.25 * original_features + 0.75 * eight_pass_inverse_aligned_mean','comparison_to_our_C2':'C2 uses mean only (weight1.0); Forge interpolates weight0.75. Same original duplicate-XY view set, no C1 view correction. Public displayed score does not exceed own B0/C2 .946.'})
 elif ref==refs[3]:
  for e in rec['cells']:e['coverage']='FULL_CELL_TEXT_READ'
  rec.update({'coverage_status':'FULL_NOTEBOOK_SOURCE_READ','code_cells_read':1,'markdown_cells_read':8,'review_method':'本轮实际读取全部9cell全文，唯一codecell7共36行，numpy演示不含模型推理。','score_claims':{'fact_class':'AUTHOR_CLAIM','baseline_lb':'0.938','bundled_deletion_lb':'0.934','baseline_four_fov_proxy':'0.9368','bundled_deletion_proxy':'0.9495','formal_submission_ids':'UNKNOWN','claims_verified_as_scores':False},'method_caveat':'compare()的abs(delta_M)/(abs(delta_J)+abs(delta_M))并不是J*M的精确归因，不能照抄为真实贡献百分比；应分别记录J,M或用乘积精确分解。'})
 else:
  for e in rec['cells']:e['coverage']='STATIC_AST_AND_PARTIAL_SOURCE_DIFF_REVIEW'
  rec.update({'coverage_status':'PARTIAL_NOTEBOOK_SOURCE_READ','code_cells_read':0,'review_method':'全部10cell已取得并AST解析；重点读cell0/cell4及与B0差异，未声明所有cell已人工全读。','main_difference':'learned relink bonus3.0/tight7.0/relaxed11.0；移除B0末端PP自动选参，validator回默认每prefix2。','upstream_claim':{'ref':'mianwang1024/biohub-relink-v1','lb_in_comment':'0.946','cv_in_comment':'0.91944 on199movies','fact_class':'AUTHOR_CLAIM','source_access':'GET_KERNEL_HTTP_ERROR','version':'UNKNOWN','script_version_id':'UNKNOWN'}})
 notebooks.append(rec)
# AST equivalence proof, excluding only module-level display docstring.
def normalized_ast(s):
 t=ast.parse(s)
 if t.body and isinstance(t.body[0],ast.Expr) and isinstance(t.body[0].value,ast.Constant) and isinstance(t.body[0].value.value,str):t.body=t.body[1:]
 return ast.dump(t)
equal=[normalized_ast(src(a))==normalized_ast(src(b)) for a,b in zip(nbs[refs[0]]['cells'],nbs[refs[1]]['cells'])];assert all(equal)
pp=ROOT/'experiments/PUBLIC946_TTA_20260908/B0';vr=list(csv.DictReader((pp/'validator_results.csv').open()));rs=list(csv.DictReader((pp/'run_stats.csv').open()));chosen=[r for r in vr if r['config']=='tight55'];keys=['edges_recovered','edges_fragmented','edges_lost_to_detection','wrong_association_edges','missed_gt_nodes','spurious_pred_nodes','div_tp','div_fp','div_fn','t_pred','t_true']
data={'schema_version':'1.0','task_id':'PUBLIC_OPTIMIZATION_RESEARCH_20260909','observed_at_utc':datetime.now(timezone.utc).isoformat(),'fact_class':'SOURCE_CODE_VERIFIED','inventory':{'requests':[{'sort':r['sort'],'page':1,'page_size':30,'returned':len(r['items']),'observed_at_utc':r['observed_at_utc']} for r in invraw],'unique_refs':len(inv),'complete_public_catalog':False,'raw_path':'downloads/20260909_public_research/notebooks/inventory_raw.json','raw_sha256':sha((RAW/'inventory_raw.json').read_bytes()),'entries':list(inv.values())},'notebooks':notebooks,'coverage':{'full_fresh_notebooks':1,'full_differential_notebooks':1,'prior_full_read_byte_reverified_notebooks':2,'partial_notebooks':1,'effective_all_code_cell_review_count':4,'note':'不把发现列表或仅AST解析的run84计入全读；两既有母版以完整源hash+12cellhash复用已全读证据，明确非本轮重新逐字全文审读。'},'mechanical_comparisons':{'tta_vs_harmonic_same_executable_ast_all12':equal,'forge_different_cells_vs_harmonic':[0,4],'forge_patch_anchor_in_B0_expanded':1,'forge_patch_old_lines':47,'forge_patch_new_lines':99,'forge_expanded_compile':'PASS_NOT_EXECUTED','forge_expanded_sha256':sha((RAW/'forge_expanded_static.py').read_bytes())},'own_B0_observable_diagnostics':{'fact_class':'MEASURED','scope':'已有B0 ordinary8FOV本地proxy可观测标签，不是hiddenformal评分细项','selected_pp':'tight55','validator_results_path':str((pp/'validator_results.csv').relative_to(ROOT)),'validator_results_sha256':sha((pp/'validator_results.csv').read_bytes()),'selected_counts':{k:sum(int(float(r[k])) for r in chosen) for k in keys},'run_stats_path':str((pp/'run_stats.csv').relative_to(ROOT)),'run_stats_sha256':sha((pp/'run_stats.csv').read_bytes()),'production_motion_reset':[{'dataset':r['dataset'],'replaced_raw_edges':int(r['motion_relink_replaced_raw_edges']),'final_division_sources':int(r['division_like_sources']),'safe_divisions_added':int(r['safe_divisions_added'])} for r in rs],'sparse_annotation_limit':'spurious_pred_nodes不是可确认真实假阳性；wrong_association_edges=0不代表hidden没有误关联；8FOV不等于8独立胚胎。'},'findings':[{'id':'same_family','fact_class':'SOURCE_CODE_VERIFIED','text':'Harmonic当前V29与942ttaV1算法AST全等，应去重为同实现家族，标题不是新的模型方案。'},{'id':'forge','fact_class':'SOURCE_CODE_VERIFIED','text':'LineageForgeV7核心是次特征TTA权重0.75；自有C2权重1.0。无新权重/训练/关联融合/PP算法，本轮公开显示仍.946。'},{'id':'motion_resets_divisions','fact_class':'SOURCE_CODE_VERIFIED','source':'redoctopusk/biohub-942tta cell5 lines420-551,1428-1445','text':'motion_relink_edges每帧两轮一对一Hungarian；非空时edges=motion_edges覆盖原ILP拓扑，原边概率仅作为motion代价的learned bonus输入。'},{'id':'divisions_in_output','fact_class':'MEASURED','text':'B0普通四视频最终division51/15/9/27恰等safe_divisions_added；原分裂拓扑没有直接保留。不是ILP完全无效的证明。'},{'id':'safe_div_bottleneck','fact_class':'SOURCE_CODE_VERIFIED','source':'redoctopusk/biohub-942tta cell5 lines973-1141','text':'safe-div要求parent现有一女儿+下一帧无parent孤儿，单向nearest orphan、两女儿各有t+2唯一后继且分离增加>=2.25um，才进入DC和symmetry检查；这是具体候选召回限制，但不能凭门槛存在就判定放宽提分。'},{'id':'deletion_failure','fact_class':'AUTHOR_CLAIM','text':'公开作者称删短轨/提检测阈值/按类型阈值组合让4FOVproxy .9368→.9495而LB .938→.934；版本源码确认这些文字存在，提交ID不可得，非独立复现。'}],'recommendations':[{'priority':1,'label':'保护有证据的分裂拓扑，再做剩余节点匹配','fact_class':'INFERENCE','status':'NOT_RUN','mechanism':'从B0保留通过图像支持、多帧持续性和单parent约束的高置信ILP分裂；motion匹配只处理剩余节点，避免先抹去全部分裂再靠safe-div重建。','basis':['motion_resets_divisions','divisions_in_output','own_B0_observable_diagnostics div_tp3 fp1 fn9'],'risks':'错误分裂会伤division精度；必须检查锚点及两女儿谱系连接，不能只增加fork数。','comparison':'未来若授权，仅与B0精确同det/weights/TTA/PP政策作单机制正式对照；不得与新阈值搜索捆绑。'},{'priority':2,'label':'先拆解分裂FN与断轨，再验证目标性修复','fact_class':'INFERENCE','status':'NOT_RUN','mechanism':'将9个可观测divisionFN按候选缺失、ILP后丢失、motion覆盖、safe-div拒绝、两女儿后继缺失、末端过滤分类；136断边按已有节点未关联和缺检测区分。','basis':['safe_div_bottleneck','own_B0_observable_diagnostics'],'risks':'稀疏标注验证只能定位已观测失败，不能作为hidden收益替代。'},{'priority':3,'label':'不优先扫次特征TTA插值或补齐D4','fact_class':'INFERENCE','status':'NOT_RUN','mechanism':'C1正式.940，C2正式.946，Forge0.75公开.946；公开证据未给出超越母版的信号。','basis':['forge','same_family'],'risks':'显示三位持平不等于内部分完全一致，也不证明所有TTA变体都无用。'},{'priority':4,'label':'不以删节点带来的proxy涨分驱动优化','fact_class':'INFERENCE','status':'NOT_RUN','mechanism':'分别报raw edge Jaccard、node-count multiplier、divisionTP/FP/FN、保留率；不要把未匹配稀疏GT节点视作应删除FP。','basis':['deletion_failure'],'risks':'作者单例非普遍定律，但足以否定proxy单一前置目标。'}],'external_writes':{'notebook_create_or_save':0,'inference_started':0,'formal_submission':0,'training':0,'dataset_or_model_write':0},'read_errors':[{'operation':'initial SDK authentication read','error':'SSL_UNEXPECTED_EOF','resolved_by':'subsequent read-only query succeeded'},{'operation':'GetKernel mianwang1024/biohub-relink-v1','error':'HTTPError','status':'SOURCE_UNAVAILABLE'}]}
(OUT/'notebook_findings.json').write_text(dump(data))
print('written',len(inv),'inventory',len(notebooks),'source objects')
