# BIOHUB_DIVGATE_PAIR_20260920_V01 执行回执

本批已实际创建并 Save & Run **两个独立私有 Notebook**；两臂仍在普通生产运行，正式 submission **0 次**。没有本批 Public 分数，未宣称实验完成或提分。

- `execution_status = KERNEL_RUNNING`
- `score_status = NOT_SUBMITTED`；submission ID 和 Public 均为 `null`，不是正式评分等待。
- `delivery_status = COMPLETED_VERIFIED`，范围仅为固定交付提交 `e7672f46466fd4d8d8bb557da6b81d12c41272de` 的 49 文件逐字节回读；证据见 `github_readback.json`。本状态与核验回执作为后续证据提交保存，并再次核对远端；远端交付核验不代表运行完成。
- 本任务整体 `INCOMPLETE_KERNEL_RUNNING`，冻结执行验收当前未通过。

## 平台身份与观测

下表初始状态读取于 2026-09-20 03:41:46 UTC / 11:41:46 上海；A18/B22 后续源码核验的精确观测时间见各自 `platform_latest.json`。所有平台读取均为本账号只读，不采用历史 Best Score 代替当前分数。

|对象|Kernel ID|Version|ScriptVersionId|Submission ID|实际状态|Public|相对 G1|最终图变化|诊断覆盖|
|---|---:|---:|---:|---:|---|---:|---|---|---|
|G1 母版|134551153|1|350197436|56270217|正式 COMPLETE|0.948|基线|历史母版，本批未重提|原 proxy 非独立官方验证|
|现有 V1/F1，只读|134988494|1|351084196|56375774|普通 COMPLETE；正式 PENDING/UI Scoring|null|null|本批未测算|本批未评价|
|A18|135051720|1|351207161|null|KERNEL_RUNNING|null|null|UNKNOWN，等待最终输出|secondary 为 TRAIN_SEEN_DIAGNOSTIC；其他上游 COVERAGE_UNKNOWN|
|B22|135052315|1|351207989|null|KERNEL_RUNNING|null|null|UNKNOWN，等待最终输出|secondary 为 TRAIN_SEEN_DIAGNOSTIC；其他上游 COVERAGE_UNKNOWN|

- [A18 私有 Notebook](https://www.kaggle.com/code/sailorren/biohub-g1-divgate018-20260920)：2026-09-20 03:37:32 UTC / 11:37:32 上海发出 Save & Run。
- [B22 私有 Notebook](https://www.kaggle.com/code/sailorren/biohub-g1-divgate022-20260920)：2026-09-20 03:41:30 UTC / 11:41:30 上海发出 Save & Run。
- SDK 回读 kernel/version/完整源码，网页可见 PRIVATE、Running、GPU T4×2；ScriptVersionId 来自页面实际 `edit/run/<id>` 链接，未打开编辑器。
- A18 日志已显示实际测试视频推理启动、模型材料哈希和原阈值 0.20。新增生产阶段尚未执行完，不把初始化值当成最终 0.18/0.22 生效证明。

## 冻结与实现

任务原文直接从固定远端提交读取，UTF-8 17826 字节，Git blob `e678da70880cb134992626ff1f1bfc597fe09239`，SHA-256 `8e84b1c618adbb95d0b47a12e59740d1e8872b27e71a22f1349cccc6a3e2d520`，均匹配用户指定值。没有根据聊天重写原文，也没有创建重复远端分支。

独立 worktree：`/private/tmp/biohub-divgate-pair-20260920`；只写 `codex/divgate-pair-20260920`。完整读取固定研究三文件、G1 全部 13 个代码单元和构建/生产模块及权重回执、F1 指定文件、官方评分和 CSV 往返路径。

预先冻结合同 SHA-256：`f236c8e2f73d8b3e9ed4ef6e04346caaeddc954e05cf7b6992104b1b2018c07e`。合同与原文先在 `ea8d261a00d675e5aab5a5f8189d0bdf453b3641` 推送并完成 7 文件字节回读。两臂源码均在 **`2649b1599785df268e614562a008d3fc0811c44a`** 推送并完成 33 文件回读后才发出 Save & Run；详见 `freeze_github_readback.json`、`source_github_readback.json`。

原 G1 13 个代码单元保持完全一致，新增最后一个生产/诊断单元：恢复母版加原选择配置，验证原阈值为 0.20，仅改最终 `DEEPCENTER_SAFE_DIV_THRESHOLD` 为 0.18 或 0.22。复用同一次原始推理图、原版完整后处理和 CSV 写出；保留 G1 私有输出，重放 0.20 做等价性检查，对原图和最终输出分别校验，记录完整内容差异。原始 proxy 只为保留 G1 选择行为，不声称官方独立验证。

本地人工图 6 项测试通过：阈值作用、深拷贝隔离、追加单元完整性、空边与行序不变性、逐视野检查点、实际官方 CSV 往返与 edge 字段汇总。第一次测试因 ML 环境缺少 polars 失败，改用仓库已有 scorer 环境通过；未安装环境、未跑大模型。短测试不是生产验收。

两臂冻结同一官方提交 `075fc5f5a52d11077f9dc2b074644618f26939e2`，与本会话官方远端 HEAD 一致。实际评分模块、division 模块和 CSV reader 源码已冻结哈希；平台运行时另记依赖版本和源码哈希。固定 8 视野测算使用最终 CSV 经官方读取后的图，逐视野持久化；仅辅助评价缺口不自动阻断正式探索性提交，图/配置/输出错误则阻断。

## 当前缺口与预算

|操作|实耗|上限|
|---|---:|---:|
|新私有 Notebook|2|2|
|Save & Run 请求|2|3（剩余共享工程备用 1）|
|正式 submission 请求|0|2|
|训练 / Dataset 写入 / 最终选择修改 / V1/F1 写入|各 0|各 0|

两臂尚未结束，生产回执、最终 CSV 完整性、0.20 等价性、完整图差异、候选间去重和辅助诊断均待实际输出；未造空 `diagnostic_results.jsonl` 作为成功结果。`summary.json` 明确记录缺口；执行验证器当前非零退出，未登记整体完成声明。

Kaggle SDK quota 的 total 6h 与已登录网页的“25h 59m available of 30h”不一致，原始两侧观测均保留，未伪称一致。写入前按实际已登录 UI 额度核查，平台接受两个请求；初始无普通 kernel 作业，B22 写入前仅 A18 普通作业和原 F1 正式评分。每日额度按当时接口的动态上限/实际已用核查，未硬编码上限、未取消现有任务。

保护核验：main 与 F1 远端 HEAD 前后一致；用户原工作区分支、HEAD、干净状态未变，见 `protected_refs_before.json` 和 `protected_refs_after.json`。不对其他并发任务造成的远端变化作本任务因果判断。

## 续接时的精确边界

先读取本分支 ledger 与 A18/B22 的精确 V1/SV，再只读状态；**不得重新运行 `launch_once.py`** 或创建新 Notebook。当前 `read_pair.py` 只读取既有两对象并更新本地账本，不发送平台写请求。

各自 COMPLETE 后，按固定版本收集小型回执和私有最终 CSV；独立验证源码、依赖、所有输入覆盖、无静默回退、最终阈值、0.20 原图等价、官方 CSV 往返与完整 canonical 差异。原始影像、完整图、权重和 submission.csv 不进入 GitHub。

若完整输出无效应，标记 MEASURED_NO_EFFECT 不提交；两臂内容相同则去重。其余通过工程检查且有差异的候选，在当前授权剩余预算内分别正式提交一次，并在请求前锁定 ledger、核查实时账号/比赛/额度/并发、推送相关代码配置提交。请求不明确只读对账，禁止盲重试。正式分数只绑定实际 submission ID，不修改最终选择。

本批未创建自动监控、后台定时器或跨日自动续跑。若会话结束时仍在运行，交付当前真实状态；不可把源代码上传、普通运行或 GitHub 交付写成正式跑分完成。
