# Codex：B的CPU文件快照测试（不运行模型、不提交评分）

指令ID：BIOHUB_B_CPU_OUTPUT_SNAPSHOT_20260922_V01  
原批次：BIOHUB_TWO_WAVE_20260922_V01；唯一B：Kernel135375343。  
仓库／执行与交付分支：SailorRen/Biohub-CELL ／ codex/two-wave-four-submit-20260922。  
交接基点：c26a43571ac250551814789bbf3f3bab147f957a。

## 1. 本轮只回答两个问题

1. 当前账号能否用CPU会话把真实工作目录文件随Quick Save保存到同一B的新版本Output，下载后字节一致？
2. 这种保存的GPU设置与正式评分加速器分别能核实到什么程度？无法核实隐藏GPU就保留UNKNOWN，不用正式提交验证。

用户授权本次短测试。只使用一个小型文本探针，不生成或命名为submission.csv，不伪造预测、不申请Colab GPU、不运行模型。成功也在本轮收口，再由Chat决定是否授权完整Colab生产及真实CSV返回。旧任务中允许完整生产/正式提交的段落，本轮不执行。

已读历史：B非运行V1/SV351871500，14单元未执行，Output为0B；事件B-ROUNDTRIP-001记录Save Output Never。此前没有真实CSV，也没有Kaggle CPU文件会话。这说明“带磁盘文件的快照”尚未测试；不是证明任何返回路径都不支持。Colab已测得1×T4并释放，不再重测。旧B SaveRun请求仍保留REQUEST_UNCERTAIN及计数。

## 2. Mac启动与必要输入

先核对当前仓库remote、分支、未提交改动，安全fetch指定分支。存在用户改动或分叉时使用隔离worktree/独立目录；不reset、stash、覆盖、强推或合并main。Git不可用时可用GitHub连接器，不安装新CLI环境。只读：

- AGENTS.md、本任务；9月3日初始情报的阅读数量合同不适用于本次。
- reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md最后的B Colab往返实测节。
- experiments/BIOHUB_TWO_WAVE_20260922_V01/platform_ledger.json。
- 同目录B/colab_roundtrip_result.json、B/resource_events.jsonl。
- 同目录B/candidate.ipynb、B/kernel-metadata.json（仅用于原代码/配置核对，不执行）。

目标编辑页：https://www.kaggle.com/code/sailorren/biohub-d960-l030p-20260922/edit 。账号sailorren；比赛biohub-cell-tracking-during-development。V1/SV351871500是历史起点，不预设下个版本必为V2。原B源码冻结commit4dca986a5bd61e3191ff790b74b505017678652e，文件SHA256为03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb；保留全部14代码单元的类型、顺序及source。

先成组只读核对最新账本、B版本及活动。若出现后续B运行、已有同一探针结果或他人正在编辑同一B，不覆盖：复用可验证结果或报告冲突。当前读取失败不当成没有作业。A/DF960等已有作业不取消、不重提、不改最终选择。历史余额不是实时事实，记录实际GPU用量/预留及时间即可，不重审全队提交。

## 3. 先检查界面，再启动一个CPU文件会话

查看Quick Save的Advanced Settings/Save Output，记录当前选项原文。需要的是“包含当前工作目录文件”的选项，不能继续选Never；不假定界面标签与旧教程相同。仅查看设置不计作已保存。若找不到对应能力，保存截图和原文，停止，不试Save & Run替代。

对同一B仅启动一个CPU交互会话，优先按本次会话选择CPU。若界面必须将草稿Accelerator设为None才允许CPU启动，本任务仅授权这项必要设置变更：保存前后值并标记试验版本非生产版；不要为维持GPU标签触发GPU申请。Inputs、Internet关闭、Private和完整B算法保持不变。不要认为能写enable_gpu=true就已证明隐藏GPU可用。

GPU/TPU启动、Run All、Save & Run All、普通kaggle kernels push、模型导入/权重读取/训练/推理全部禁止。CLI旧记录2.2.3不支持--no-run；本轮直接使用网页可见的Quick Save保存输出，不折腾CLI升级。登录、验证码或新授权由用户处理，不能读取凭据或绕过授权。

只执行下面的文件探针。首选官方Console（其代码不改变Notebook单元）；Console不可用时，允许添加一个临时探针单元、只执行该单元，然后在保存前删除此临时单元，核对原14单元未执行且source不变。若界面无法保证只执行探针，立即停止，不执行整本Notebook。

```python
# 仅在已确认的Kaggle CPU会话执行；不是模型、预测或比赛提交。
from pathlib import Path
import hashlib
import json

root = Path('/kaggle/working')
if not root.is_dir():
    raise RuntimeError('NOT_IN_KAGGLE_WORKING_DIRECTORY')
p = root / 'output_binding_probe.txt'
payload = (
    'BIOHUB_B_CPU_OUTPUT_SNAPSHOT_20260922_V01\n'
    'kernel=135375343\n'
    'purpose=FILE_SNAPSHOT_ONLY_NOT_A_PREDICTION\n'
).encode('utf-8')
if p.exists():
    raise RuntimeError('PROBE_ALREADY_EXISTS_CHECK_LEDGER_NO_OVERWRITE')
with p.open('xb') as f:
    f.write(payload)
print(json.dumps({
    'path': str(p), 'bytes': len(payload),
    'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
    'scope': 'CPU_TEXT_FILE_ONLY_NOT_MODEL_OUTPUT'
}, sort_keys=True))
```

保存控制台输出中的字节数与SHA256。在Mac独立计算同一payload哈希，核对创建前后内容；不以创建脚本打印成功代替后续下载验证。只对该文件操作，不创建submission.csv，不复制A/D960 CSV，不清空/kaggle/working或删除未知文件。目录如有其他文件，先列出名称/大小，避免将凭据、他人产物或大文件随快照上传；无法安全隔离就报告阻断。

这个探针验证“工作目录→版本Output”，不是已完成“Colab CSV→Kaggle”的外部传输。即便成功，来源和范围也必须这样写。

## 4. 保存一次带输出的Quick Save并验证

先在原platform_ledger.json追加唯一意图，建议request_id=TW20260922-B-OUTPUTSNAP-01；记录对象、完整B源哈希、探针哈希、CPU会话状态、保存输出设置原文和时间，并同步必要小记录。源码未变无需重新构建或重复冻结证据包。

选择Quick Save以及明确包含磁盘输出的选项，版本名建议“B output snapshot probe - NOT FOR SUBMISSION”；只发送一次。保存返回不明时仅对账，不换SDK/浏览器再发一次。旧SaveRun解析错误不在本次修复范围。

保持CPU会话和页面，直到输出上传/快照完成；不要刚点击保存就结束会话。工作人员说明Quick Save带输出会先上传当前会话文件，上传期间离开或断开可能导致保存排队异常。正常小文件操作目标10分钟CPU会话内完成；总主动排查约20分钟，只处理一次明确UI/路径修复，不反复试版本。仍排队就记录已知状态，不取消或重发；未确认快照完成时，不强制断开来制造失败，也不声称后台仍有人监控。

保存后通过新版本Output/官方下载入口取得output_binding_probe.txt，验证真实Kernel/Version/SV、路径、字节数与哈希，不能下载旧版本同名文件替代。本机CLI若只能取latest，要在下载前后核对latest仍是目标；不明则用版本明确的UI入口。核对源单元仍为冻结的14个且未执行，不将临时探针混成生产算法。

一次性记录设置证据：CPU交互会话的实际Accelerator、保存界面配置、具体版本metadata的enable_gpu/machine_shape、Docker与Inputs、打包日志Accelerator。字段拿不到写NOT_OBSERVED；CPU会话和打包日志不能直接代表隐藏评分加速器。只读取已有提交对话框的要求，不点击Submit、不输入假submission.csv使按钮可用。没有真实CSV时仍缺文件属预期，不否定探针文件保存成功。

若启动CPU导致新版本为CPU配置，直接写“文件快照已验证，GPU生产配置未保留”；不重新保存、切GPU、测试正式评分来补齐。配置仍显示GPU也只能写CONFIG_GPU_RETAINED，隐藏worker为UNTESTED。

## 5. 边界、预算和收口

本轮新增上限：Kaggle候选创建0；CPU文件会话1；Quick Save带输出请求1；Kaggle/Colab GPU和TPU0；模型/数据下载与完整生产0；正式提交0；Dataset/购买/最终选择修改0。使用的是上轮非运行保存1/2中尚余的一次；执行时若已用完，不另增额度。本轮结束后通常累计非运行保存2/2，后续真实CSV保存和Colab重新连接需要另行授权，不因探针成功自动长跑。

记录原批候选2、普通运行尝试2、正式1（A）等历史，旧不明请求不退账；如有后续进展以最新账本为准。不要执行其他旧任务的剩余授权。

仅新增B/output_snapshot_probe.json，列出：CPU会话、实际文件创建、Save Output选项、非运行保存、具体版本下载哈希、原14单元一致性、GPU配置保留情况、hidden_gpu=UNTESTED、formal_requests=0。每项带实际时间、证据、PASS/BLOCKED/NOT_RUN；保存行为、算法效果和提交资格分开。

继续追加B/resource_events.jsonl、原platform_ledger.json及reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md的“CPU输出快照探针”节。只保存必要截图/脱敏原文；不创建第二套合同、报告体系或仪表盘。阻断时写清发生在哪一步、原话、已试修复、保留版本/文件及下一步最小问题。

快照完成、必要小文件已回收后，释放仅本任务CPU会话；不删B版本、不取消旧作业。试验版本明确标记不可提交。若草稿设置改为CPU，记录当前值，不擅自恢复GPU触发会话。向原分支同步一次新增/变更小文件并完成远端回读；不改main、不覆盖用户Mac改动，不循环验证回执。

最终回答：是否保存并回读了真实磁盘文件？新版本身份是什么？原推理代码是否保留？GPU配置证据说明什么、仍未知什么？本轮平台写请求及预算？固定报告commit和核验范围？成功也不要写“Colab回传正式评分已打通”；原B真实生产、CSV及评分仍未验证。

## 官方机制依据（历史说明，不替代本次实测）

- https://www.kaggle.com/product-feedback/41177 ：Kaggle工作人员说明Quick Save高级选项可保存输出，默认只保存Notebook。
- https://www.kaggle.com/product-feedback/159129 ：工作人员指向Quick Save Advanced Settings及工作目录文件下载。
- https://www.kaggle.com/product-feedback/402984 ：工作人员说明先上传当前会话输出，上传中断可能导致排队异常。
- https://www.kaggle.com/docs/notebooks ：Console不修改Notebook源单元；Quick Save与Save & Run区别。

本文件交付仅代表任务已写好；平台测试由Codex按最新账本实际执行。
