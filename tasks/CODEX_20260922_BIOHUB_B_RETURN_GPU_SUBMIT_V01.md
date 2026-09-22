# Codex：续接 B，完成真实输出回传与一次正式提交

任务ID：BIOHUB\_B\_RETURN\_GPU\_SUBMIT\_20260922\_V01
仓库：SailorRen/Biohub-CELL
执行／交付分支：codex/two-wave-four-submit-20260922
交接基点：1735cafe1ece57e8eb846d9fe9a885098e1087d4
沿用实验：BIOHUB\_TWO\_WAVE\_20260922\_V01

## 1. 唯一目标

继续现有 B，先解决“同一精确 Kaggle 版本同时保留 GPU 配置、完整离线推理源码和真实磁盘输出”，再完成一次 Colab 生产、真实 CSV 回传和一次正式提交。以正式 Public 判断结果，不设计新算法，不扩展 C/D，不重复已完成的 CPU 文本快照测试。

本指令由用户转交执行后，是本次 B 续接的单批授权；替代旧任务“本轮结束后不得继续”的停点，以及下文明确增加的资源上限。其余算法、隐私和安全约束保留。不把本指令解释为重新获得旧任务所有额度。

## 2. 先同步任务、读取现有证据

安全 fetch 原分支，确认包含交接基点。沿用干净的隔离 worktree；不覆盖用户改动，不 reset、stash、强推、合并 main 或修改其他仓库。若远端已有后续交付，先读取并排重，不退回旧版本执行。

将本指令原文保存为：
tasks/CODEX\_20260922\_BIOHUB\_B\_RETURN\_GPU\_SUBMIT\_V01.md
先提交、推送原分支并回读，再进行平台写操作。只授权本任务文件、必要适配代码和本批小型证据的 GitHub 写入。

读取以下必要材料；不用重新审计全仓库：

- AGENTS.md、本指令。
- tasks/CODEX\_20260922\_BIOHUB\_B\_COLAB\_ROUNDTRIP\_CONTINUE\_V01.md。
- reports/20260922\_BIOHUB\_TWO\_WAVE\_RESULTS.md 的最新 B 停点。
- experiments/BIOHUB\_TWO\_WAVE\_20260922\_V01/platform\_ledger.json。
- 同目录 B/candidate.ipynb、B/kernel-metadata.json、B/output\_snapshot\_probe.json、B/colab\_roundtrip\_result.json、B/resource\_events.jsonl。
- 同目录 check\_actual\_csv.py、patch\_support.py、known\_output\_hashes.json、A/formal\_precheck.json。

唯一 B：sailorren/biohub-d960-l030p-20260922，Kernel135375343。
历史 V2/SV351886222 仅探针版本，enable\_gpu=false，禁止提交该版本。
冻结 B/candidate.ipynb SHA256：
03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb

保留 D960＋L030P 单次保护剪枝、velocity0.5；不得改成 A 的0.25，不改模型、阈值、精度、batch、选择器、保护规则或分裂逻辑。

## 3. 本次新增预算与排重

本次最多新增：

- Colab 托管 GPU 会话1次、完整 B 生产1次；私有 Colab Notebook最多1个，已有则复用。
- Kaggle CPU 文件会话2次：仅用于必要的组合检查及真实文件回传；不做整本CPU推理。
- 同一 B 的非运行 Quick Save 最多2次：必要的 GPU＋输出组合检查最多1次，真实产物最终保存最多1次；路径已有充分证据时跳过检查保存。
- B 正式提交请求最多1次，计入原批总上限4次，不额外增加正式总额度。
- 恢复同一 B 的 GPU 元数据、固定 Inputs 和必要环境配置；不启动 Kaggle 交互 GPU 或普通 Save & Run。

新 Kaggle Notebook、训练、Dataset写入、付费购买、TPU、A/DF960/C/D执行、最终选择修改均为0。不得更换账号绕过配额。

旧非运行保存2次、CPU会话1次、Colab设备探针会话1次、普通SaveRun尝试2次、正式请求1次（A）全部保留。新额度单列增补，累计非运行保存最多4次、CPU文件会话最多3次、Colab GPU会话最多2次。旧REQUEST\_UNCERTAIN不退账；保存失败或响应不明也计入已派发次数。

开始只读核对当前账号、B最新版本与活动作业、是否已有真实产物／正式请求、GPU用量和团队提交额度。发现已有B运行就续接，不启动重复生产；已有合格真实产物则复用；已有B正式请求则只读查状态，不再提交。

保留另外2个正式名额。提交前实时剩余额度须至少3次，且仍处于原批授权的额度周期；不能用旧截图证明额度。跨额度刷新后不自动使用新周期名额，也不安排后台等待提交。

## 4. 先闭合 GPU＋输出路径，禁止反复探针

不要再测试一次“CPU文本文件能否进入Output”；该项已通过。

只核查一个问题：官方支持的操作能否在不启动Kaggle普通GPU运行的前提下，让同一保存版本保留GPU配置与磁盘文件输出。优先查看当前界面、官方说明和本机已安装SDK／CLI帮助，不假定某个未核实参数存在。

先确定文件导入方式、保存顺序、切换加速器是否终止会话／清空目录，以及如何从最终精确版本读回GPU设置和文件。不把“改元数据一定保留输出”当既定事实。不得借隐藏接口、伪造完成状态或篡改配额绕过限制。

必要时使用已归档的103字节探针，最多做一次新的“GPU配置＋真实文件Output同时保留”组合检查；这不是重做CPU-only测试。不得改名成submission.csv或拿探针提交。切换设置前备份本任务文件，未知用户文件不覆盖、不删除。

组合检查合格必须绑定同一个真实Kernel/Version/SV，并确认：GPU配置已保留、探针可精确下载且哈希正确、原14代码单元未被模型执行。CPU打包日志的Accelerator None不单独决定隐藏评分GPU状态；GPU元数据正常也不等于隐藏worker已验证。

hidden\_gpu=UNTESTED可以如实保留，不要求先做一次额外正式提交来验证GPU。若官方流程明确不能保留两者，或实际设置动作必须消耗本次未授权的Kaggle GPU运行，停止于BLOCKED\_GPU\_OUTPUT\_COEXISTENCE并给出直接证据，不先花完整Colab生产成本。

不得把仅存在非生产V2、旧JSON响应错误、或尚无隐藏GPU日志作为新的循环阻断理由。路径具备官方支持且所需设置可核验后，继续真实生产，不再就本指令范围内的操作反复请示。

## 5. 一次 Colab 真实生产与回传

使用Colab自己的托管GPU，不连接Kaggle后台。仅用现有合法账号权限；登录、验证码或新增OAuth授权由用户本人完成，不读取或记录明文凭据。

沿用固定输入版本：primary V10、secondary V2、DeepCenter V5、gate Notebook V1/SV349707105；精确slug、模型哈希和原验证／选参输入从现有任务与断言读取。只把必要数据和权重放Colab临时磁盘，不全量下载到Mac，不用同名最新版替换，不少下载选参数据后静默改变样本。

在同一会话完成空间、依赖、GPU、权重和一个真实批次检查，通过即继续完整B生产；不另开模型诊断批次。允许外层路径、设备数量及依赖的最小兼容适配并保留diff；单卡采用原有单进程回退，不虚构第二张卡，不改变算法。环境主动排查最多30分钟、一轮最小修复；需要算法重写或额外会话则停止并保存具体错误。

保存真实submission.csv、two\_wave/production\_receipt.json及必要日志。运行现有check\_actual\_csv.py，使用arm B并以A/formal\_precheck.json作为另一候选的检查摘要；依据脚本真实参数调用，不重写宽松验收器。

确认样本覆盖、CSV及图结构合法、固定配置真实生效、L030P实际变化，并与已归档结果去重。仅做原流程已有的对照，不增加GPU重跑、8视野诊断、阈值扫描或新回放。无有效变化或输出重复就不提交，不放宽保护规则强行制造差异。

通过已确认的正规文件流程把真实CSV返回同一B。最终Kaggle代码必须保留完整离线推理、固定输入与GPU配置，不能只复制Colab预计算CSV，不能把联网登录／下载单元作为隐藏评分必经路径，不能按已知可见／隐藏样本特判绕过推理。

默认恢复冻结B的原14代码单元；必要的环境兼容改动单列return\_candidate.ipynb及diff，不伪称全文哈希仍等于冻结原件。按逐单元源码和实际配置确认算法一致，不把JSON格式或执行元数据变化误判为算法变化。

执行最多一次最终带输出Quick Save；从该精确版本下载实际CSV，与Colab原件及回传工作目录分别核对字节数和SHA256。再次读取该版本的真实Version/SV、GPU配置、Inputs、源码与提交资格，禁止把V1的GPU证据和V2／其他版本的Output拼接验收。

## 6. 合格后正式提交 B 一次

同一最终版本同时满足真实CSV哈希、代码／输入绑定、GPU元数据和CSV有效性检查，且实时额度符合第3节时：先在原platform\_ledger.json写唯一请求意图并同步，再通过官方入口提交该精确版本一次，不等待A出分。

出现超时、JSON解析错误或不明响应，仅只读对账，禁止换CLI／网页入口重发。当前无B已受理证据不等于旧请求从未收到。

记录submission ID、Notebook Version、SV、状态、读取时间和Public原始值。查同窗D960 56416049、A 56456090用于比较，均只读；不用三位小数反推隐藏分数。

已受理未出分写SCORE\_PENDING；正式失败写直接错误，不重提；有实际Public才报告差值。工程生产成功、提交受理与提分是三件事，不宣称达到0.95，不修改最终选择。

## 7. 交付和停止条件

沿用原报告与原账本，不另建治理框架：

- 在reports/20260922\_BIOHUB\_TWO\_WAVE\_RESULTS.md追加本次结果。
- 更新原platform\_ledger.json、B/resource\_events.jsonl、B/colab\_roundtrip\_result.json，保存必要源码diff及小型检查回执。

原始CSV、完整图、模型、原始数据、凭据不入GitHub。保存必要产物后，释放仅本次创建且已不需要的CPU／Colab会话，不取消其他既有作业。

推送原分支，对本轮新增／变更小文件从固定commit回读一次并核对哈希，报告实际通过数、remote HEAD和worktree状态，不循环自证。不把GitHub交付通过写成模型提分。

最终回复只说明：B到达哪个阶段；精确Version/SV/submission；实际Public或PENDING；GPU＋真实CSV绑定是否通过；本轮和累计预算；固定commit及报告位置。若阻断，附具体原始错误、已尝试动作与可复用产物，不只写“GPU不足”。
