# Biohub 最新成绩与公开区更新报告（2026-09-28）

采集开始：2026-09-28T09:41:02.434595+08:00；页面核对完成：2026-09-28T09:45:29.950653+08:00。均为中国上海时区。分支 `codex/xrl9-two-wave-20260927`；比较基点为昨天晚间报告。此次仅刷新结果、读取公开资料及同步本仓库；Kaggle 新运行、正式请求和最终选择修改均为 0。

## 结论

**MEASURED：R9D950 正式 0.955，R8D955 正式 0.956；两波五份均 COMPLETE。本队已核验最高仍为 0.956，由 R9D955 与 R8D955 并列，较 XR0 高 0.003。当前排名 189 / 3964，前百显示线 0.959，尚差 0.003。**

公开区出现值得关注的新信息：John Taylor (AI) 在[新讨论 743929](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743929)披露 ILP 分裂成本和 readmit 阈值两项设置。其团队榜单显示 0.959，但具体实验分数、因果归因及可迁移收益仍属于 AUTHOR_CLAIM，没有可绑定的逐方案 submission/SV 或完整新源码。

代码目录三种排序共 300 条、去重 162 份，相比昨晚无新增 ref、1 份更新时间变化；该更新 Notebook 的准确 V14 Public 为 0.882。本轮没有找到新公开且经过准确版本高分验证、可直接替代本队 0.956 的完整方案。此结论限于样本，不是全站穷尽。

## 本队正式成绩

以下 11 个准确 submission 均在本轮通过官方 get_submission 刷新；状态全为 COMPLETE，无 errorDescription 返回。SV 绑定来自仓库精确版本回执及提交描述。XR0 为同队 dongdongjiaqi，其余为 sailorren。分差仅针对显示 Public，不代表 Private 稳定提升。

| 候选 | Version / SV | submission ID | 正式状态 | Public | ΔXR0 | 提交时间（上海） |
|---|---|---|---|---:|---:|---|
| XR0 | V1 / 352643547 | 56546951 | COMPLETE | 0.953 | +0.000 | 09-25 17:25:57 |
| XV25 | V1 / 352908214 | 56573059 | COMPLETE | 0.953 | +0.000 | 09-26 15:31:40 |
| XG95 | V1 / 352908258 | 56573089 | COMPLETE | 0.929 | -0.024 | 09-26 15:32:41 |
| XV25G95 | V1 / 352913254 | 56573515 | COMPLETE | 0.952 | -0.001 | 09-26 15:51:48 |
| XD960 | V1 / 353050916 | 56585147 | COMPLETE | 0.954 | +0.001 | 09-27 01:22:55 |
| XRL9 | V1 / 353050971 | 56587392 | COMPLETE | 0.955 | +0.002 | 09-27 03:33:36 |
| R8D965 | V1 / 353188155 | 56599380 | COMPLETE | 0.955 | +0.002 | 09-27 13:53:07 |
| R9D960 | V1 / 353188100 | 56599443 | COMPLETE | 0.955 | +0.002 | 09-27 13:55:59 |
| R9D955 | V1 / 353192186 | 56599964 | COMPLETE | 0.956 | +0.003 | 09-27 14:08:34 |
| R9D950 | V1 / 353314948 | 56615584 | COMPLETE | 0.955 | +0.002 | 09-28 01:56:10 |
| R8D955 | V1 / 353315066 | 56615617 | COMPLETE | 0.956 | +0.003 | 09-28 01:57:37 |

[本队提交页](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/submissions)；[R9D950 精确版本](https://www.kaggle.com/code/sailorren/biohub-xrl9-r9d950-20260927?scriptVersionId=353314948)；[R8D955 精确版本](https://www.kaggle.com/code/sailorren/biohub-xrl9-r8d955-20260927?scriptVersionId=353315066)。每份原始小型成绩回执见 `research/PUBLIC_UPDATE_20260928/submission_<ID>.json`，读取时点由同目录 observation.json 绑定。

MEASURED：固定 relaxed=9 μm，检测阈值 0.965 / 0.960 / 0.955 / 0.950 分别为 0.955 / 0.955 / 0.956 / 0.955。因此继续下调检测阈值没有显示收益；不能把 0.955→0.950 当成召回增加就必然提分。固定检测 0.955，relaxed=9 与 8 均为 0.956，后一份没有超过母版。五次正式请求已用完；普通请求 6/6（含工程备用），本轮没有追加请求。最终选择保留原样。

## 排行榜与截止时间

OFFICIAL_FACT / MEASURED：[官方榜单](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/leaderboard) API 前 200 行与页面本队行一致。当前 189 / 3964，0.956、61 entries；昨晚归档为 191 / 3953。前进 2 位是两个时点的观察，不把全部变动归因于第二波。

| 排名 | 当前显示分 | 较本队高 |
|---|---:|---:|
| 1（yu4u） | 0.978 | 0.022 |
| 50 | 0.963 | 0.007 |
| 75 | 0.961 | 0.005 |
| 100 | 0.959 | 0.003 |
| 150 | 0.957 | 0.001 |
| 200 | 0.956 | 0.000 |

同分不保证同排名；排行榜成绩不证明方法公开。John Taylor (AI) 在本次 API 顺序第 103 行、显示 0.959，支持其团队当前分数，但不能证明每一步参数实验的单独收益。

OFFICIAL_FACT：[官方时间表](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/overview/timeline)截止为 2026-09-29 23:59 UTC，即 **上海 09-30 07:59**。本轮约剩不到两天；不以社区答复替代截止政策。

## 新讨论：两个具体优化线索

AUTHOR_CLAIM：[743929](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743929)由 John Taylor (AI) 发布。作者回复 message 3529308 于上海 09-28 06:57 披露：

| 作者的实验步骤 | 参数变化 | 作者报告的 Public |
|---|---|---|
| 已有私有后处理母版上改 ILP 成本 | ILP_DIVISION_WEIGHT：1.2 → 0.4 | 0.957 → 0.958 |
| 再改轨迹端点附近补回检测的阈值 | READMIT_MIN_SCORE：0.965 → 0.94 | 0.958 → 0.959 |

作者称两项可见节点数变化均不到 1%，强调局部验证未反映 Public 改善。我们未取得这些实验的具体版本、提交回执或完整源码；其 0.953→0.957 的前置后处理尚未披露，不能跳过这个条件，不能把上述两个参数拼到我们母版便宣称能达 0.959。“全部收益来自改边而非节点惩罚”也仍为作者归因，未独立验证。

INFERENCE：与继续扩大检测阈值搜索相比，这两个线索更值得后续技术核查，因为本队进一步降到 0.950 已回落，而新帖给出了明确参数和不同作用位置。若之后另行授权实验，应先核对当前母版参数实际消费与守卫，再保持其他处理不变做可归因比较；本报告不构建候选、不申请或使用新预算。反复按 Public 选参不能证明 Private 收益，也不自动采纳作者的最终选择建议。

其余六个已跟踪主题中，五个正文无变化；[前百讨论 742169](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742169)只新增欢迎回复，无新配方。[截止问题 743765](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743765)无新正文；没有据此新增官方规则结论。总目录从 121 增至 122 个主题。

## 公开代码：唯一更新对象未带来高分证据

MEASURED：[Anhad — Track Your Cells V14 / SV353423030](https://www.kaggle.com/code/anhadmahajan06/biohub-track-your-cells?scriptVersionId=353423030)当前页面 Public **0.882**；Best **0.946** 属于 V4 / SV350331995。两者不能混用，源码中的目标分数文字也不是正式成绩。

SOURCE_CODE_VERIFIED（定向静态检查）：已下载完整 10 个代码单元，并逐单元 AST 检查通过；这不等于动态运行验收。配置包含检测 0.965、tight relink 5.2 μm、gap 4.5 μm、分裂母女距离 8.5 μm、DeepCenter 阈值 0.35。实现与完整 XR0 不同：

- relink 使用相邻帧未连接端点的距离矩阵与 Hungarian 配对；不把文字介绍中的速度一致性当作实际消费证据。
- DeepCenter cache 初始化为空，所查 Notebook 中没有填充调用；gap veto 以缓存存在为条件。打印“Active”不能证明该门实际生效。
- 写出节点坐标时使用 round 后转 int，与保留连续坐标不同。
- 末尾固定 selected_label；仅列出 sweep 名字不代表真实搜索。不能把本地 proxy 分数或宣传文字当成正式评价。

INFERENCE：该 V14 的 0.882 与上述实现差异不支持整份移植；不据静态发现断言其中某一项独自导致退分。未下载其前一版源码，所以这里只说明当前实现，不声称每项都是最新修改。

其余四份源码与昨晚快照逐字节相同：Aman V6、Robust V8、Harmonic V5、m-toshi V6。它们的旧精确页面成绩及限制继续引用[昨晚报告](20260927_BIOHUB_PUBLIC_UPDATE_AND_RESULTS_EVENING.md)，本轮不冒充再次刷新这些页面成绩；本次刷新的只是完整源码与版本号。Harmonic 0.953、Robust 0.429 为历史页面证据；Aman V6、m-toshi V6 的准确正式 Public 仍为 UNKNOWN。

## 覆盖、证据与限制

已刷新 11 个正式 ID；三种代码排序各 100 条；new/active 两种讨论目录各 20 条；7 主题共 40 个正文/嵌套回复；5 份 Notebook 共 90 个代码单元。全部取得完整源码，逐单元经 IPython 语法转换后 AST 通过，但仅对更新对象做定向语义检查，不标记 FULL_NOTEBOOK_SOURCE_REVIEWED，不执行外部代码或验证隐藏输入。

证据目录：`research/PUBLIC_UPDATE_20260928/`。包含原始 API 小型回执、公开源码、哈希与差异摘要、页面观测、验收结果。网络搜索仅用来发现/核对官方来源，索引可能滞后，最新动态以本次 Kaggle API 和页面为准。没有穷尽全站代码与讨论，未检验讨论中的逐方案正式回执或 Private 结果。

完成范围仅为本次有界结果与研究报告；不是整个历史全量研究合同完成。机器检查和固定 commit 远端关键文件回读另存交付回执，分析判断保留 INFERENCE，作者收益保留 AUTHOR_CLAIM。
