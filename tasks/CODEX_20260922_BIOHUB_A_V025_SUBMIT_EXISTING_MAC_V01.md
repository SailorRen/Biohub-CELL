# Codex Mac续接：验收现有A V1并正式提交一次

指令ID：BIOHUB_A_V025_SUBMIT_EXISTING_MAC_20260922_V01  
唯一实验批次：BIOHUB_TWO_WAVE_20260922_V01（同批续接，不新建实验）  
仓库／交付分支：SailorRen/Biohub-CELL ／ codex/two-wave-four-submit-20260922  
本指令依据的远端基点：6fa45f1207a967f65eb2bed3e710b38f322dee05。

## 1. 本次目标与边界

用户已回到Mac，明确通知A普通运行完成，并授权验收后正式提交现有版本。先核对平台，不把用户通知或旧GitHub RUNNING快照当作本次独立查证。只完成A的剩余步骤：版本对账→下载真实产物→CPU验收→正式提交一次→同步回执。不要重新设计候选、重新构建或启动Notebook；不执行B/C/D，不取消其他作业，不等DF960出分。

本次新增预算：Notebook创建/Fork 0；Save & Run 0；模型推理/训练/独立GPU诊断/TPU迁移/Dataset写入/最终选择修改各0；正式请求最多1次，且A累计最多1次。已提交或已有不明正式请求时只读对账，不再次发送。计入原批总账，不把四次总预算重置。当前授权适用于执行时真实可用的提交额度，不因旧“约21小时刷新”推算机械阻断，也不扩大B/C/D或下一周期实验范围。平台无可用名额则如实停止写入。

## 2. Mac同步与必读文件

优先使用Mac当前已打开的Biohub-CELL仓库及已配置的GitHub、Kaggle CLI/SDK/浏览器。先检查pwd、git rev-parse --show-toplevel、git remote -v及git status --short，确认实际仓库为SailorRen/Biohub-CELL。没有已确认的Mac绝对路径，不猜旧路径，不把其他比赛目录当成本项目。Mac缓存仅可在版本/哈希复核后复用；另一台电脑的新记录必须先从远端取得。

安全fetch本任务分支；工作区干净且分支无分叉时可以fast-forward同步。存在用户未提交改动、分支分叉或其他任务在用时，使用隔离worktree或独立clone；不reset、stash、覆盖、强推或合并main。没有可用本地Git时用GitHub连接器获取同样文件；不因此重跑Kaggle。下面仅用于核对，不在未确认仓库时盲执行：

```bash
git remote get-url origin
git status --short
git fetch origin codex/two-wave-four-submit-20260922
git rev-parse origin/codex/two-wave-four-submit-20260922
```

读取最新分支中的以下文件即可，不全仓重审：
1. `AGENTS.md`、本指令；旧两批任务只参考预算/实现背景，不执行其B/C/D启动动作。9月3日初始调研的阅读数量合同不适用于本次提交续接。
2. `reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md`。
3. `experiments/BIOHUB_TWO_WAVE_20260922_V01/platform_ledger.json`。
4. 同目录 `check_actual_csv.py`、`patch_support.py`、`known_output_hashes.json`。
5. 同目录 `A/candidate.ipynb`、`A/kernel-metadata.json`；已有源码冻结回读无需重复生成。

最近远端账本快照是Notebook1/4、Save & Run1/5、正式0/4，A普通RUNNING，B未运行；这是历史状态，执行时先扣除后续真实请求。若最新账本已有A正式提交，直接跳到接收状态和交付核对。

## 3. 精确身份：只续接这个版本

|字段|固定目标|
|---|---|
|账号／团队|sailorren ／ Sailor Ren|
|比赛|biohub-cell-tracking-during-development|
|候选|A：D960-V025，velocity0.25，无leaf剪枝|
|Notebook slug|sailorren/biohub-d960-v025-20260922|
|Notebook Version／SV|1 ／ 351739212|
|版本链接|https://www.kaggle.com/code/sailorren/biohub-d960-v025-20260922?scriptVersionId=351739212|
|Version Name历史记录|A V025 source 4dca986|
|源码冻结commit|4dca986a5bd61e3191ff790b74b505017678652e|
|源码路径|experiments/BIOHUB_TWO_WAVE_20260922_V01/A/candidate.ipynb|
|冻结文件SHA256|393dc558654af6abffd8c786a1b8fd4065a58e5c2a6a0ba61af4b9d3b4be40df|
|正式输出文件|submission.csv|

先用本机已授权的只读入口核对账号、精确V1/SV、普通COMPLETE状态、产物可下载，以及此版本是否已有正式提交。不要只读slug的“最新版本”；如果最新已经不是V1，仍定位SV351739212，不擅自提交新版本。数值Kernel ID此前NOT_OBSERVED，不得拿SV冒充Kernel ID。

复核该版本全部14个代码单元的类型/顺序/source与冻结源码一致；元数据、输出及JSON序列化差异单列，不据整文件字节不同误判算法变更。若需要，只读下载精确SV源码，不能打开可启动GPU的交互会话来取文件。输入沿用已记录的primary Dataset V10、secondary V2、DeepCenter V5、gate Notebook V1/SV349707105及比赛输入；不可修改Inputs。精确Docker摘要不可见时保留已有环境证据限制，不为补一个API字段重建版本。

CLI/SDK能只读验证身份、能绑定精确版本且已授权时优先复用；否则用已登录浏览器。先检查本机真实接口/--help，不照搬跨电脑时的能力缺口，也不编造CLI参数。禁止打印或入库Token、Cookie、环境变量快照。无需安装训练环境或本地scorer。

## 4. 下载实际输出并执行已有标准库验收器

从该精确V1/SV下载 `submission.csv` 和 `two_wave/production_receipt.json`；只在核对加载与参数消费需要时补取同版本 `two_wave/postprocess_calls.jsonl`、`ppsweep_selected.json`、权重完整性回执、sprint回执和普通日志必要段。优先选择性下载，不拉原始影像、权重或所有图缓存。若工具只能获取最新输出，先确认当前最新恰为该V1并在下载后再次核对；不能证明则改用版本明确的下载入口。

在Git外建立本次Mac下载目录。以下第一段只创建目录；必须真实下载完成后，才运行第二段。后续会话若变量丢失，应查本轮实际下载位置或重新读取平台现有产物，不能造空文件：

```bash
OUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/biohub-a351739212.XXXXXX")"
printf 'A实际输出下载目录：%s\n' "$OUT_DIR"
```

下载后保持结构为 `$OUT_DIR/submission.csv` 和 `$OUT_DIR/two_wave/production_receipt.json`。在已安全同步的仓库根目录，用可用的Python3执行：

```bash
python3 experiments/BIOHUB_TWO_WAVE_20260922_V01/check_actual_csv.py \
  "$OUT_DIR/submission.csv" \
  "$OUT_DIR/two_wave/production_receipt.json" \
  --arm A \
  --output experiments/BIOHUB_TWO_WAVE_20260922_V01/A/formal_precheck.json
```

该脚本已实际核对接口，只用标准库及同目录patch_support，不需polars/tracksdata/CUDA。输出文件已存在且证明仍绑定相同输入字节和精确SV时可复用；不要为了再次生成PASS重复运行整本Notebook。若Python3实际路径不同，使用已确认的本机解释器替换命令，不随意重建环境。

验收必须核对：真实CSV的schema、发现的样本覆盖、坐标与哨兵、行ID、唯一节点/边、端点、时间前进及图度；文件/图哈希与回执相符，已有去重检查通过；det0.960、harmonic0.15、DeepCenter分裂门0.20、velocity0.25、leaf=null；三份推理权重和G1 gate匹配，模型实际参与输出。另核对生产回执中 `velocity_consumed` 的最终样本记录，确认实际消费0.25且有调用，不仅是初始配置显示。官方reader往返沿用同次云端 `csv_roundtrip=PASS` 回执，加上本地对真实CSV的独立检查，不另起GPU运行。

存在实际、非纯重编号变化才提交；同次CPU回放只证明改动生效，不是独立Public对照。CPU脚本/路径报错可在本批目录做最小工程修复并如实记录，不放松验收、不改生产源码。实际输出非法、候选无变化、模型缺失、参数未生效或回执缺失无法核实则只阻断A正式请求；本指令不授权重新Save & Run补产物。缺原Mac缓存不是阻断理由，现有云端产物可重新下载。

## 5. 通过即正式提交一次，不新增普通GPU会话

验收合格后立即核对当前账号/比赛、实际剩余提交名额和已有提交列表。GPU余额低或恢复倒计时本身不等于已有版本被禁止正式提交：查看实际提交入口是否可用，不为了“可用GPU”打开交互会话。若平台明确拒绝已有版本评分，保存原始提示，不绕过，不偷偷另启普通运行。

在唯一 `platform_ledger.json` 追加A正式请求意图：唯一request_id、SV351739212、version1、file=submission.csv、源码commit、实际CSV哈希、时间与拟用入口，先持久化；同步必要验收摘要/意图，但不重复冻结未变源码或重传旧证据包。正式提交前从远端再核对没有并发新增A请求；不明状态先对账，不盲重试。

走“提交已完成Notebook精确版本”的正式评分入口。SDK/CLI只有明确支持code submission且可绑定该V1时才用；按本机实际接口传入比赛、Notebook、Version=1及输出文件submission.csv。不要调用只上传本地CSV的普通文件提交入口冒充代码竞赛提交。

浏览器后备：进入精确V1的Output/Submit to Competition，确认比赛及submission.csv后只点击一次正式提交。不要使用Fork、Copy & Edit、Run All、Save Version、Save & Run或 `kaggle kernels push`；出现会额外创建/运行新版本的路径就返回，改用现有版本入口。正式隐藏评分是本次授权目标，禁止的是新增普通保存运行。

描述建议：`BIOHUB_TWO_WAVE_20260922_V01 A V025 V1 SV351739212`。

响应不明或超时时，计为一次正式尝试，只读检索精确SV、描述、时间和输出绑定，不换API/浏览器再提交一次。成功取得submission ID后只读回查一次，记录精确版本、原始Public、状态/错误和时间。UI确认受理但没有数值ID时记 `SUBMITTED_UI_CONFIRMED_ID_UNAVAILABLE`，ID=null、保留精确版本与UI证据，不冒用DF960/D960的ID；API字段未读写NOT_OBSERVED，不把缺字段假装成API返回空值。

取得受理证据即可交付，不等8小时、不追加GPU分析、不创建定时器。已有正式结果可如实报告；无分数时只记待分，不推测提分。

## 6. 最小交付

沿用原目录和报告，只更新本次新增证据：
- `experiments/BIOHUB_TWO_WAVE_20260922_V01/A/formal_precheck.json`：实际CSV检查结果；必要绑定/受理小回执放A目录。
- `experiments/BIOHUB_TWO_WAVE_20260922_V01/platform_ledger.json`：保留历史条目，追加唯一正式请求和真实结果；新建Notebook/SaveRun计数不得增加。
- `reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md`：追加“A现有V1正式提交续接”一节，不改写历史；明确B/C/D本轮未执行。
- 原 `github_readback.json` 保留既有证据，追加或引用本次新增/变更payload的一次远端回读；不循环验证回执。

仅push本交付分支，不merge main或改其他项目。公开仓库不入库原始CSV、完整图、权重、凭据或大日志。保留Mac用户工作区；如用detached worktree，向指定分支做非强制fast-forward推送，远端变化时先协调，不能覆盖他人进展。

最终直接返回：A普通与CSV验收状态、是否实际正式提交、V1/SV351739212、真实submission ID或ID不可见状态、正式状态/原始Public、观测时间、原批累计预算、本次新增请求数、固定报告commit及回读范围。正文不能只重复旧“普通完成”状态；没有受理证据就写NOT_SUBMITTED或REQUEST_UNCERTAIN，不写完成评分。
